import requests
import feedparser
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
import os
from urllib.parse import urljoin, urlparse, quote
from dotenv import load_dotenv
from newspaper import Article, Config
from category_mappings import validate_category, validate_subcategory, map_to_main_category, map_to_subcategory, get_subcategories
from newsapi import NewsApiClient
import nltk
import concurrent.futures
import hashlib
import json
from pathlib import Path
import time
import asyncio
import aiohttp
from functools import lru_cache
import random

load_dotenv()

class NewsFetcher:
    def __init__(self):
        self.newsapi = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))
        self.newsapi_key = os.getenv("NEWS_API_KEY")
        self.newsapi_base_url = "https://newsapi.org/v2/"
        self.newsdata_api_key = os.getenv("NEWSDATA_API_KEY")
        self.base_url = "https://newsdata.io/api/1/latest"
        self.discovered_feeds: Dict[str, Set[str]] = {}
        
        # Configure newspaper3k
        self.newspaper_config = Config()
        self.newspaper_config.browser_user_agent = 'Mozilla/5.0'
        self.newspaper_config.request_timeout = 10
        self.newspaper_config.fetch_images = False
        self.newspaper_config.memoize_articles = False  # Disable memoization
        
        # Initialize session and lock for async requests
        self.session = None
        self.session_lock = asyncio.Lock()
        
        # List of news sources to randomly select from
        self.news_sources = [
            "bbc-news", "cnn", "the-verge", "techcrunch", "wired",
            "reuters", "bloomberg", "the-wall-street-journal",
            "the-new-york-times", "the-washington-post",
            "the-guardian-uk", "time", "fortune", "business-insider",
            "engadget", "ars-technica", "techradar", "venturebeat"
        ]
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            print("Downloading NLTK punkt data...")
            nltk.download('punkt')
            
        try:
            nltk.data.find('tokenizers/punkt_tab')
        except LookupError:
            print("Downloading NLTK punkt_tab data...")
            nltk.download('punkt_tab')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            print("Downloading NLTK stopwords data...")
            nltk.download('stopwords')
            
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            async with self.session_lock:
                if self.session is None or self.session.closed:
                    self.session = aiohttp.ClientSession()
        return self.session
            
    async def _close_session(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
        
    def _get_cache_key(self, url: str) -> str:
        """Generate a cache key for a URL"""
        return hashlib.md5(url.encode()).hexdigest()
        
    @lru_cache(maxsize=1000)
    def _get_cached_content(self, url: str) -> Optional[Dict]:
        """Get cached content for a URL if it exists and is not expired"""
        cache_key = self._get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    # Check if cache is less than 24 hours old
                    if time.time() - cached_data.get('timestamp', 0) < 86400:
                        return cached_data.get('data')
            except Exception as e:
                print(f"Error reading cache for {url}: {str(e)}")
        return None
        
    def _save_to_cache(self, url: str, data: Dict):
        """Save content to cache"""
        cache_key = self._get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'timestamp': time.time(),
                    'data': data
                }, f)
        except Exception as e:
            print(f"Error saving cache for {url}: {str(e)}")
            
    async def _extract_article_content_async(self, url: str, original_title: str = "") -> Dict[str, str]:
        """Async version of article content extraction"""
        try:
            # print(f"Attempting to extract content from: {url}")
            session = await self._get_session()
            
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                    
                html = await response.text()
                article = Article(url, config=self.newspaper_config)
                article.set_html(html)
                article.parse()
                
                # Only run NLP if we have content
                if article.text:
                    try:
                        article.nlp()  # This will extract keywords, summary, etc.
                    except Exception as e:
                        print(f"Warning: NLP processing failed: {str(e)}")
                
                # Log the extraction results
                # print(f"Successfully extracted content from {url}")
                # print(f"Title: {article.title}")
                # print(f"Content length: {len(article.text)} characters")
                
                # Only use extracted title if it's not empty and different from original
                final_title = article.title if article.title and article.title != original_title else original_title
                
                # Get published date, fallback to current time if not available
                published_at = None
                if article.publish_date:
                    try:
                        published_at = article.publish_date.isoformat()
                    except Exception as e:
                        print(f"Warning: Failed to format publish date: {str(e)}")
                
                if not published_at:
                    published_at = datetime.now().isoformat()
                    print(f"Using current time as fallback for publish date: {published_at}")
                
                return {
                    "title": final_title,
                    "content": article.text,
                    "image_url": article.top_image,
                    "published_at": published_at,
                    "summary": article.summary if hasattr(article, 'summary') else "",
                    "keywords": article.keywords if hasattr(article, 'keywords') else []
                }
                
        except Exception as e:
            print(f"Error extracting article content from {url}: {str(e)}")
            return {
                "title": original_title,  # Keep the original title
                "content": "",
                "image_url": None,
                "published_at": datetime.now().isoformat(),  # Use current time as fallback
                "summary": "",
                "keywords": []
            }
            
    async def _extract_articles_parallel_async(self, articles: List[Dict]) -> List[Dict]:
        """Extract content from multiple articles in parallel using async"""
        tasks = []
        for article in articles:
            if article.get('url'):
                task = asyncio.create_task(
                    self._extract_article_content_async(
                        article['url'],
                        article.get('title', '')
                    )
                )
                tasks.append((article, task))
        
        # Process results as they complete
        processed_articles = []
        for article, task in tasks:
            try:
                extracted_data = await asyncio.wait_for(task, timeout=15)  # 15 second timeout per article
                if extracted_data.get('content'):
                    article.update(extracted_data)
                    processed_articles.append(article)
            except asyncio.TimeoutError:
                print(f"Timeout extracting content from: {article.get('url')}")
            except Exception as e:
                print(f"Error processing article {article.get('url')}: {str(e)}")
        
        return processed_articles

    async def fetch_articles_async(self, 
                      query: Optional[str] = None,
                      category: Optional[str] = None,
                      language: str = "en",
                      page_size: int = 10,
                      days_back: Optional[int] = None,
                      sort_by: str = "relevancy",
                      page: int = 1,
                      use_rss: bool = True,
                      discover_feeds: bool = True) -> List[Dict]:
        """
        Fetch articles from NewsAPI asynchronously
        """
        if not self.newsapi_key:
            print("No NewsAPI key found")
            return []

        try:
            print(f"Making NewsAPI request with query: {query}")
            
            # Basic parameters for NewsAPI
            params = {
                'q': query,
                'language': language,
                'sort_by': sort_by,
                'page_size': min(page_size, 100),
                'apiKey': self.newsapi_key,
                'page': page
            }
            
            # Remove None values and empty strings
            params = {k: v for k, v in params.items() if v is not None and v != ''}
            
            # Make the request
            url = f"{self.newsapi_base_url}everything"
            print(f"Request URL: {url}")
            print(f"Request params: {params}")
            
            session = await self._get_session()
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    print(f"HTTP error: {response.status}")
                    return []
                
                data = await response.json()
                # print(f"Response data: {data}")
                
                if data.get('status') != 'ok':
                    print(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                    return []
                
                # Process articles in parallel
                articles = []
                for article in data.get('articles', []):
                    # Get original article data
                    original_title = article.get('title', '')
                    original_description = article.get('description', '')
                    original_url = article.get('url', '')
                    original_source = article.get('source', {}).get('name', 'unknown')
                    original_image = article.get('urlToImage')
                    original_published = article.get('publishedAt')
                    
                    # Generate a unique article ID
                    article_id = f"{original_source}-{original_title}"[:50].replace(" ", "-").lower()
                    if original_url:
                        url_hash = str(hash(original_url))[:8]
                        article_id = f"{article_id}-{url_hash}"
                    
                    # Only add articles that have both title and URL
                    if original_title and original_url:
                        article_data = {
                            "article_id": article_id,
                            "title": original_title,
                            "content": original_description,  # Use description as initial content
                            "source": original_source,
                            "url": original_url,
                            "published_at": original_published,
                            "image_url": original_image,
                            "category": "other"  # Default category
                        }
                        articles.append(article_data)
                
                # Extract full content in parallel
                # print(f"Extracting content for {len(articles)} articles...")
                articles_with_content = await self._extract_articles_parallel_async(articles)
                # print(f"Successfully extracted content for {len(articles_with_content)} articles")
                
                return articles_with_content[:page_size]
                    
        except Exception as e:
            print(f"Error fetching articles: {str(e)}")
            return []
            
    def _get_random_sources(self, count: int = 5) -> List[str]:
        """Get a random selection of news sources"""
        return random.sample(self.news_sources, min(count, len(self.news_sources)))

    def fetch_articles(self, 
                      query: Optional[str] = None,
                      category: Optional[str] = None,
                      language: str = "en",
                      page_size: int = 10,
                      days_back: Optional[int] = None,
                      sort_by: str = "relevancy",
                      page: int = 1,
                      use_rss: bool = True,
                      discover_feeds: bool = True,
                      randomize_sources: bool = False,
                      force_refresh: bool = False,
                      use_rss_only: bool = True) -> List[Dict]:
        """
        Fetch articles from either NewsAPI or RSS feeds based on use_rss_only flag
        """
        if use_rss_only:
            return self._fetch_articles_from_rss(
                query=query,
                category=category,
                page_size=page_size,
                page=page
            )
        else:
            return self._fetch_articles_from_newsapi(
                query=query,
                category=category,
                language=language,
                page_size=page_size,
                days_back=days_back,
                sort_by=sort_by,
                page=page,
                randomize_sources=randomize_sources,
                force_refresh=force_refresh
            )

    def _fetch_articles_from_rss(self,
                      query: Optional[str] = None,
                      category: Optional[str] = None,
                      page_size: int = 10,
                      page: int = 1) -> List[Dict]:
        """
        Fetch articles from RSS feeds and extract full content
        """
        executor = None
        try:
            # Define a list of popular RSS feeds by category
            rss_feeds = {
                'technology': [
                    'https://techcrunch.com/feed/',
                    'https://www.theverge.com/rss/index.xml',
                    'https://www.wired.com/feed/rss',
                    'https://www.engadget.com/rss.xml',
                    'https://www.zdnet.com/news/rss.xml'
                ],
                'business': [
                    'https://www.bloomberg.com/feeds/sitemap_news.xml',
                    'https://www.reutersagency.com/feed/',
                    'https://www.ft.com/rss/home',
                    'https://www.wsj.com/xml/rss/3_7085.xml',
                    'https://www.cnbc.com/id/100003114/device/rss/rss.html'
                ],
                'politics': [
                    'https://www.politico.com/rss/politicopicks.xml',
                    'https://www.theguardian.com/politics/rss',
                    'https://www.nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/section/politics/rss.xml',
                    'https://www.washingtonpost.com/politics/feed/',
                    'https://www.bbc.com/news/politics/rss.xml'
                ],
                'entertainment': [
                    'https://www.rollingstone.com/feed/',
                    'https://www.variety.com/feed',
                    'https://www.hollywoodreporter.com/feed',
                    'https://www.ew.com/feed/',
                    'https://www.billboard.com/feed/'
                ],
                'sports': [
                    'https://www.espn.com/espn/rss/news',
                    'https://www.si.com/rss/si_topstories.xml',
                    'https://www.skysports.com/rss/0,20514,11661,00.xml',
                    'https://www.bbc.com/sport/rss.xml',
                    'https://www.theguardian.com/sport/rss'
                ],
                'science': [
                    'https://www.sciencedaily.com/rss/all.xml',
                    'https://www.nature.com/nature.rss',
                    'https://www.science.org/rss/news_current.xml',
                    'https://www.newscientist.com/feed/',
                    'https://www.sciencenews.org/feed'
                ],
                'health': [
                    'https://www.medicalnewstoday.com/newsfeeds/rss/all.xml',
                    'https://www.healthline.com/rss/all',
                    'https://www.who.int/rss-feeds/news-english.xml',
                    'https://www.mayoclinic.org/rss/all-health-information-topics',
                    'https://www.nih.gov/news-events/news-releases/rss'
                ],
                'environment': [
                    'https://www.theguardian.com/uk/environment/rss',
                    'https://www.nationalgeographic.com/environment/rss.xml',
                    'https://www.climate.gov/news-feeds/rss',
                    'https://www.greenpeace.org/international/feed/',
                    'https://www.wwf.org.uk/feeds/news'
                ],
                'education': [
                    'https://www.ed.gov/feed',
                    'https://www.insidehighered.com/rss.xml',
                    'https://www.chronicle.com/rss',
                    'https://www.timeshighereducation.com/rss',
                    'https://www.edweek.org/ew/rss/feed.xml'
                ],
                'world': [
                    'https://www.bbc.com/news/world/rss.xml',
                    'https://www.theguardian.com/world/rss',
                    'https://www.aljazeera.com/xml/rss/all.xml',
                    'https://www.reutersagency.com/feed/',
                    'https://www.nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/section/world/rss.xml'
                ]
            }

            # Select feeds based on query or category
            selected_feeds = []
            if query:
                # If query is a single word, treat it as a category
                if ' ' not in query:
                    category = query.lower()
            
            if category and category.lower() in rss_feeds:
                selected_feeds.extend(rss_feeds[category.lower()])
            else:
                # If no category or query matches, use a mix of feeds
                for feeds in rss_feeds.values():
                    selected_feeds.extend(feeds[:2])  # Take first 2 feeds from each category

            # Shuffle feeds to get variety
            random.shuffle(selected_feeds)
            
            # Fetch articles from feeds with timeout
            all_articles = []
            for feed_url in selected_feeds:
                try:
                    feed = feedparser.parse(feed_url)  # Add timeout to feed parsing
                    if feed.entries:
                        for entry in feed.entries:
                            # Get article data
                            title = entry.get('title', '')
                            url = entry.get('link', '')
                            published = entry.get('published', '')
                            source = feed.feed.get('title', 'Unknown Source')
                            
                            # Generate article ID
                            article_id = f"{source}-{title}"[:50].replace(" ", "-").lower()
                            if url:
                                url_hash = str(hash(url))[:8]
                                article_id = f"{article_id}-{url_hash}"
                            
                            # Get initial content from RSS
                            content = entry.get('summary', '')
                            if not content and entry.get('content'):
                                content = entry.get('content')[0].get('value', '')
                            
                            # Get initial image from RSS
                            image_url = None
                            if entry.get('media_content'):
                                for media in entry.get('media_content', []):
                                    if media.get('type', '').startswith('image/'):
                                        image_url = media.get('url')
                                        break
                            elif entry.get('media_thumbnail'):
                                image_url = entry.get('media_thumbnail', [{}])[0].get('url')
                            
                            if title and url and content:
                                article_data = {
                                    "article_id": article_id,
                                    "title": title,
                                    "content": content,  # Initial content from RSS
                                    "source": source,
                                    "url": url,
                                    "published_at": published,
                                    "image_url": image_url,  # Initial image from RSS
                                    "category": category if category else "other"
                                }
                                all_articles.append(article_data)
                except Exception as e:
                    print(f"Error fetching feed {feed_url}: {str(e)}")
                    continue
            
            # Shuffle articles and select the ones we'll return
            random.shuffle(all_articles)
            selected_articles = all_articles[:page_size]
            
            # Extract full content and images only for the selected articles
            print(f"Extracting full content for {len(selected_articles)} articles...")
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
            futures = []
            for article in selected_articles:
                if article.get('url'):
                    futures.append(
                        executor.submit(
                            self._extract_article_content,
                            article['url'],
                            article.get('title', '')
                        )
                    )
            
            # Process results as they complete with timeout
            for article, future in zip(selected_articles, futures):
                try:
                    extracted_data = future.result(timeout=10)  # Reduced timeout to 10 seconds
                    if extracted_data.get('content'):
                        # Keep the original published_at from RSS
                        original_published = article['published_at']
                        article.update(extracted_data)
                        article['published_at'] = original_published
                        
                        # If we got a better image from the article, use it
                        if extracted_data.get('image_url'):
                            article['image_url'] = extracted_data['image_url']
                except concurrent.futures.TimeoutError:
                    print(f"Timeout extracting content from: {article.get('url')}")
                except Exception as e:
                    print(f"Error processing article {article.get('url')}: {str(e)}")
            
            return selected_articles
                    
        except Exception as e:
            print(f"Error fetching articles from RSS: {str(e)}")
            return []
        finally:
            # Ensure executor is properly shut down
            if executor:
                executor.shutdown(wait=False)

    def _fetch_articles_from_newsapi(self,
                      query: Optional[str] = None,
                      category: Optional[str] = None,
                      language: str = "en",
                      page_size: int = 10,
                      days_back: Optional[int] = None,
                      sort_by: str = "relevancy",
                      page: int = 1,
                      randomize_sources: bool = False,
                      force_refresh: bool = False) -> List[Dict]:
        """
        Fetch articles from NewsAPI and extract their content
        """
        if not self.newsapi_key:
            print("No NewsAPI key found")
            return []

        try:
            print(f"Making NewsAPI request with query: {query}")
            
            # Calculate date range for fresh articles (last week)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=2)  # Get articles from the last 2 days
            
            # Prepare API parameters
            params = {
                'q': query,
                'language': language,
                'sort_by': sort_by,  # Python client expects 'sort_by'
                'page_size': min(page_size, 100),  # Python client expects 'page_size'
                'page': page,
                'from_param': start_date.strftime('%Y-%m-%dT%H:%M:%S'),  # Python client expects 'from_param'
                'to': end_date.strftime('%Y-%m-%dT%H:%M:%S')
            }
            
            # Add random sources if requested
            if randomize_sources:
                random_sources = self._get_random_sources()
                params['sources'] = ','.join(random_sources)
            
            # Remove None values and empty strings
            params = {k: v for k, v in params.items() if v is not None and v != ''}
            
            print(f"NewsAPI request params: {params}")
            
            # Use the NewsAPI client to fetch articles
            response = self.newsapi.get_everything(**params)
            
            print(f"NewsAPI response status: {response.get('status')}")
            print(f"NewsAPI response totalResults: {response.get('totalResults')}")
            
            if response.get('status') != 'ok':
                print(f"NewsAPI error: {response.get('message', 'Unknown error')}")
                return []
            
            articles = response.get('articles', [])
            print(f"Number of articles received: {len(articles)}")
            
            if not articles:
                print("No articles received from NewsAPI")
                return []
            
            # Process articles
            processed_articles = []
            for article in articles:
                # Get original article data
                original_title = article.get('title', '')
                original_description = article.get('description', '')
                original_url = article.get('url', '')
                original_source = article.get('source', {}).get('name', 'unknown')
                original_image = article.get('urlToImage')
                original_published = article.get('publishedAt')  # This is the reliable date from NewsAPI
                
                # Generate a unique article ID
                article_id = f"{original_source}-{original_title}"[:50].replace(" ", "-").lower()
                if original_url:
                    url_hash = str(hash(original_url))[:8]
                    article_id = f"{article_id}-{url_hash}"
                
                # Only add articles that have both title and URL
                if original_title and original_url:
                    article_data = {
                        "article_id": article_id,
                        "title": original_title,
                        "content": original_description,  # Use description as initial content
                        "source": original_source,
                        "url": original_url,
                        "published_at": original_published,  # Use the NewsAPI date
                        "image_url": original_image,
                        "category": "other"  # Default category
                    }
                    processed_articles.append(article_data)
            
            print(f"Number of processed articles: {len(processed_articles)}")
            
            # Extract full content in parallel using ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for article in processed_articles:
                    if article.get('url'):
                        futures.append(
                            executor.submit(
                                self._extract_article_content,
                                article['url'],
                                article.get('title', '')
                            )
                        )
                
                # Process results as they complete
                for article, future in zip(processed_articles, futures):
                    try:
                        extracted_data = future.result(timeout=15)  # 15 second timeout per article
                        if extracted_data.get('content'):
                            # Keep the original published_at from NewsAPI
                            original_published = article['published_at']
                            article.update(extracted_data)
                            article['published_at'] = original_published
                    except Exception as e:
                        print(f"Error processing article {article.get('url')}: {str(e)}")
            
            return processed_articles[:page_size]
                    
        except Exception as e:
            print(f"Error fetching articles from NewsAPI: {str(e)}")
            return []

    def _extract_article_content(self, url: str, original_title: str = "") -> Dict[str, str]:
        """Synchronous version of article content extraction"""
        try:
            # print(f"Attempting to extract content from: {url}")
            article = Article(url, config=self.newspaper_config)
            article.download()
            article.parse()
            
            # Only run NLP if we have content
            if article.text:
                try:
                    article.nlp()  # This will extract keywords, summary, etc.
                except Exception as e:
                    print(f"Warning: NLP processing failed: {str(e)}")
            
            # Log the extraction results
            # print(f"Successfully extracted content from {url}")
            # print(f"Title: {article.title}")
            # print(f"Content length: {len(article.text)} characters")
            
            # Only use extracted title if it's not empty and different from original
            final_title = article.title if article.title and article.title != original_title else original_title
            
            return {
                "title": final_title,
                "content": article.text,
                "image_url": article.top_image,
                "summary": article.summary if hasattr(article, 'summary') else "",
                "keywords": article.keywords if hasattr(article, 'keywords') else []
            }
                
        except Exception as e:
            print(f"Error extracting article content from {url}: {str(e)}")
            return {
                "title": original_title,  # Keep the original title
                "content": "",
                "image_url": None,
                "summary": "",
                "keywords": []
            }
        finally:
            # Ensure any open connections are closed
            if hasattr(article, 'html') and article.html:
                article.html = None
            if hasattr(article, 'text') and article.text:
                article.text = None

    def _merge_article_data(self, api_data: Dict, extracted_data: Dict) -> Dict:
        """
        Merge article data from API with extracted full content
        Prefers API metadata but uses extracted content when API content is truncated
        """
        merged = api_data.copy()
        
        # Use extracted content if API content is too short or missing
        api_content = api_data.get("content", "")
        if not api_content or len(api_content) < 200:  # Threshold for truncated content
            merged["content"] = extracted_data.get("content", api_content)
            
        # Use extracted image if API image is missing
        if not merged.get("image_url") and extracted_data.get("image_url"):
            merged["image_url"] = extracted_data["image_url"]
            
        return merged
        
    def _is_valid_rss_url(self, url: str) -> bool:
        """Check if a URL is a valid RSS feed"""
        try:
            feed = feedparser.parse(url)
            return feed.entries and feed.feed
        except:
            return False
            
    def _find_rss_links(self, url: str) -> List[str]:
        """Find RSS feed links on a webpage"""
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            rss_links = []
            
            # Look for RSS feed links in various formats
            for link in soup.find_all('link'):
                if link.get('type') in ['application/rss+xml', 'application/atom+xml', 'application/xml']:
                    href = link.get('href')
                    if href:
                        rss_links.append(urljoin(url, href))
            
            # Look for common RSS feed patterns in links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if any(pattern in href.lower() for pattern in ['rss', 'feed', 'atom', '.xml']):
                    rss_links.append(urljoin(url, href))
                    
            return rss_links
        except:
            return []
            
    def _search_for_feeds(self, query: str, num_results: int = 5) -> List[str]:
        """Search for websites that might have RSS feeds"""
        try:
            # Use DuckDuckGo's HTML version for searching
            search_url = f"https://html.duckduckgo.com/html/?q={quote(query)}+rss+feed"
            response = requests.get(search_url, timeout=5)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            results = []
            
            # Extract search results
            for result in soup.find_all('div', class_='result'):
                link = result.find('a', class_='result__url')
                if link and link.get('href'):
                    results.append(link['href'])
                    
            return results[:num_results]
        except:
            return []
            
    def discover_feeds(self, category: str, num_feeds: int = 5) -> Set[str]:
        """
        Discover RSS feeds for a given category
        """
        if category in self.discovered_feeds:
            return self.discovered_feeds[category]
            
        # Search for websites in the category
        search_query = f"{category} news website"
        websites = self._search_for_feeds(search_query)
        
        discovered_feeds = set()
        for website in websites:
            # Find RSS feeds on the website
            rss_links = self._find_rss_links(website)
            
            # Validate and add feeds
            for feed_url in rss_links:
                if self._is_valid_rss_url(feed_url):
                    discovered_feeds.add(feed_url)
                    if len(discovered_feeds) >= num_feeds:
                        break
                        
            if len(discovered_feeds) >= num_feeds:
                break
                
        self.discovered_feeds[category] = discovered_feeds
        return discovered_feeds
        
    def _format_article(self, article: Dict, source: str = "newsdata") -> Dict:
        """Format article data consistently regardless of source"""
        if source == "newsdata":
            # Generate a unique article ID
            article_id = article.get("link", "").split("/")[-1]
            if not article_id or len(article_id) < 5:  # If the URL doesn't provide a good ID
                # Use a combination of source and title
                source_name = article.get("source_id", "unknown")
                title = article.get("title", "")
                article_id = f"{source_name}-{title}"[:50].replace(" ", "-").lower()
            
            return {
                "article_id": article_id,
                "title": article.get("title", ""),
                "content": article.get("content", ""),
                "source": article.get("source_id", ""),
                "url": article.get("link", ""),
                "published_at": article.get("pubDate", ""),
                "image_url": article.get("image_url", ""),
                "category": article.get("category", ["other"])[0] if isinstance(article.get("category"), list) else article.get("category", "other")
            }
        else:  # RSS feed
            # Try to extract image from RSS feed
            image_url = None
            
            # First try media_content
            if article.get("media_content"):
                for media in article.get("media_content", []):
                    if media.get("type", "").startswith("image/"):
                        image_url = media.get("url")
                        break
            
            # Then try media_thumbnail
            elif article.get("media_thumbnail"):
                image_url = article.get("media_thumbnail", [{}])[0].get("url")
            
            # Then try enclosures
            elif article.get("enclosures"):
                for enclosure in article.get("enclosures", []):
                    if enclosure.get("type", "").startswith("image/"):
                        image_url = enclosure.get("url")
                        break
            
            # Then try to extract from summary
            elif article.get("summary"):
                try:
                    soup = BeautifulSoup(article.get("summary", ""), 'lxml')
                    img = soup.find('img')
                    if img and img.get('src'):
                        image_url = img['src']
                except:
                    pass
            
            # Get category and subcategory
            category = article.get("category", "other")
                
            # Generate a unique article ID
            article_id = article.get("link", "").split("/")[-1]
            if not article_id or len(article_id) < 5:  # If the URL doesn't provide a good ID
                # Use a combination of source and title
                source_name = source
                title = article.get("title", "")
                article_id = f"{source_name}-{title}"[:50].replace(" ", "-").lower()
            
            # Get the full content
            content = article.get("summary", "")
            if not content:
                content = article.get("description", "")
            
            return {
                "article_id": article_id,
                "title": article.get("title", ""),
                "content": content,
                "source": source,
                "url": article.get("link", ""),
                "published_at": article.get("published", ""),
                "image_url": image_url,
                "category": category
            }
            
    def fetch_top_headlines(self, 
                          country: str = "us",
                          category: Optional[str] = None,
                          page_size: int = 10,
                          use_rss: bool = True,
                          discover_feeds: bool = True) -> List[Dict]:
        """
        Fetch top headlines from NewsData.io API and optionally RSS feeds
        """
        articles = []
        
        # Try NewsData.io API first if we have a key
        if self.newsdata_api_key:
            try:
                # Build query parameters
                params = {
                    "apikey": self.newsdata_api_key,
                    "country": country.lower(),  # NewsData.io expects lowercase country codes
                    "size": page_size,
                    "timeframe": "12h"  # Set timeframe to 12 hours
                }
                
                # Add category if provided
                if category:
                    params["category"] = category.lower()  # NewsData.io expects lowercase categories
                
                # Make the API request
                response = requests.get(self.base_url, params=params)
                response.raise_for_status()
                newsdata_response = response.json()
                
                if newsdata_response.get("status") == "success":
                    articles.extend([self._format_article(article, "newsdata") for article in newsdata_response.get("results", [])])
                
            except Exception as e:
                print(f"NewsData.io API error: {str(e)}")
                if hasattr(e, 'response'):
                    print(f"Response content: {e.response.text}")
        
        # If we want RSS feeds and have a category
        if use_rss and category:
            try:
                # Discover feeds if needed
                if discover_feeds:
                    feed_urls = self.discover_feeds(category)
                else:
                    feed_urls = self.discovered_feeds.get(category, set())
                
                for feed_url in feed_urls:
                    feed = feedparser.parse(feed_url)
                    if feed.entries:
                        rss_articles = [self._format_article(entry, feed.feed.title) for entry in feed.entries[:page_size]]
                        articles.extend(rss_articles)
            except Exception as e:
                print(f"RSS feed error: {str(e)}")
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                unique_articles.append(article)
        
        return unique_articles[:page_size] 