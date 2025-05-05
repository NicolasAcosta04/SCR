"""
News Fetcher Module
Handles fetching, parsing, and processing news articles from multiple sources including:
- NewsAPI
- RSS feeds
- Direct article URLs
Implements caching, parallel processing, and content extraction.
"""

import requests
import feedparser
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta, timezone
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
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Timer:
    """
    Context manager for timing operations
    Used to measure and log execution time of various operations
    """
    def __init__(self, name):
        self.name = name
        self.start_time = None
        self.end_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, *args):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        logger.info(f"{self.name} took {duration:.2f} seconds")

class NewsFetcher:
    """
    Main class for fetching and processing news articles
    Supports multiple news sources, RSS feeds, and content extraction
    """
    def __init__(self):
        # Initialize API clients and configuration
        self.newsapi = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))
        self.newsapi_key = os.getenv("NEWS_API_KEY")
        self.newsapi_base_url = "https://newsapi.org/v2/"
        self.newsdata_api_key = os.getenv("NEWSDATA_API_KEY")
        self.base_url = "https://newsdata.io/api/1/latest"
        self.discovered_feeds: Dict[str, Set[str]] = {}
        
        # Configure newspaper3k for article parsing
        self.newspaper_config = Config()
        self.newspaper_config.browser_user_agent = 'Mozilla/5.0'
        self.newspaper_config.request_timeout = 3
        self.newspaper_config.fetch_images = False
        self.newspaper_config.memoize_articles = False  # Disable memoization
        
        # Initialize async session management
        self.session = None
        self.session_lock = asyncio.Lock()
        
        # List of trusted news sources
        self.news_sources = [
            "bbc-news", "cnn", "the-verge", "techcrunch", "wired",
            "reuters", "bloomberg", "the-wall-street-journal",
            "the-new-york-times", "the-washington-post",
            "the-guardian-uk", "time", "fortune", "business-insider",
            "engadget", "ars-technica", "techradar", "venturebeat"
        ]
        
        # Download required NLTK data for text processing
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
        """
        Get or create an aiohttp session for async requests
        Uses a lock to prevent multiple simultaneous session creations
        """
        if self.session is None or self.session.closed:
            async with self.session_lock:
                if self.session is None or self.session.closed:
                    self.session = aiohttp.ClientSession()
        return self.session
            
    async def _close_session(self):
        """Close the aiohttp session if it exists and is open"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
        
    def _get_cache_key(self, url: str) -> str:
        """
        Generate a unique cache key for a URL
        Args:
            url: The URL to generate a key for
        Returns:
            MD5 hash of the URL
        """
        return hashlib.md5(url.encode()).hexdigest()
        
    @lru_cache(maxsize=1000)
    def _get_cached_content(self, url: str) -> Optional[Dict]:
        """
        Retrieve cached content for a URL if it exists and is not expired
        Args:
            url: The URL to check in cache
        Returns:
            Cached data if available and fresh, None otherwise
        """
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
        """
        Save content to cache with timestamp
        Args:
            url: The URL to cache
            data: The data to cache
        """
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
        """
        Asynchronously extract content from an article URL
        Args:
            url: The article URL to extract from
            original_title: The original title from the feed/API
        Returns:
            Dictionary containing extracted article data
        """
        try:
            with Timer(f"Extracting content from {url}"):
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
                            article.nlp()  # Extract keywords, summary, etc.
                        except Exception as e:
                            logger.warning(f"NLP processing failed: {str(e)}")
                    
                    # Use extracted title if available and different from original
                    final_title = article.title if article.title and article.title != original_title else original_title
                    
                    # Get published date with fallback
                    published_at = None
                    if article.publish_date:
                        try:
                            published_at = article.publish_date.isoformat()
                        except Exception as e:
                            logger.warning(f"Failed to format publish date: {str(e)}")
                    
                    if not published_at:
                        published_at = datetime.now().isoformat()
                        logger.info(f"Using current time as fallback for publish date: {published_at}")
                    
                    return {
                        "title": final_title,
                        "content": article.text,
                        "image_url": article.top_image,
                        "published_at": published_at,
                        "summary": article.summary if hasattr(article, 'summary') else "",
                        "keywords": article.keywords if hasattr(article, 'keywords') else []
                    }
                    
        except Exception as e:
            logger.error(f"Error extracting article content from {url}: {str(e)}")
            return {
                "title": original_title,  # Keep the original title
                "content": "",
                "image_url": None,
                "published_at": datetime.now().isoformat(),  # Use current time as fallback
                "summary": "",
                "keywords": []
            }
            
    async def _extract_articles_parallel_async(self, articles: List[Dict]) -> List[Dict]:
        """
        Extract content from multiple articles in parallel using async
        Args:
            articles: List of article dictionaries to process
        Returns:
            List of processed articles with extracted content
        """
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
        Args:
            query: Search query string
            category: News category to filter by
            language: Language code (default: "en")
            page_size: Number of articles per page
            days_back: Number of days to look back
            sort_by: Sort order ("relevancy", "popularity", "publishedAt")
            page: Page number
            use_rss: Whether to use RSS feeds
            discover_feeds: Whether to discover new RSS feeds
        Returns:
            List of article dictionaries
        """
        with Timer(f"Fetching articles (query: {query}, category: {category}, page: {page})"):
            if not self.newsapi_key:
                logger.error("No NewsAPI key found")
                return []

            try:
                logger.info(f"Making NewsAPI request with query: {query}")
                
                # Basic parameters for NewsAPI
                params = {
                    'q': query,
                    'language': language,
                    'sort_by': sort_by,
                    'page_size': page_size,
                    'page': page
                }
                
                # Add category if specified
                if category:
                    params['category'] = category
                    
                # Add date range if specified
                if days_back:
                    from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                    params['from'] = from_date
                
                # Make the API request
                response = self.newsapi.get_everything(**params)
                
                if response['status'] != 'ok':
                    logger.error(f"NewsAPI error: {response.get('message', 'Unknown error')}")
                    return []
                    
                articles = response['articles']
                
                # Process articles in parallel
                processed_articles = await self._extract_articles_parallel_async(articles)
                
                return processed_articles
                
            except Exception as e:
                logger.error(f"Error fetching articles: {str(e)}")
                return []

    def _get_random_sources(self, count: int = 5) -> List[str]:
        """Get a random selection of news sources"""
        return random.sample(self.news_sources, min(count, len(self.news_sources)))

    async def fetch_articles(self, 
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
        with Timer(f"Fetching articles (query: {query}, category: {category}, page: {page})"):
            # Special handling for general query
            if query == "__GENERAL__":
                # Fetch the most popular/top headlines
                return await self.fetch_top_headlines(page_size=page_size)
            
            # Handle multiple categories in query
            categories = []
            if query and ' OR ' in query:
                categories = [cat.strip() for cat in query.split(' OR ')]
            elif category:
                categories = [category]
            
            if not categories:
                return await self._fetch_articles_from_rss(
                    query=query,
                    category=category,
                    page_size=page_size,
                    page=page
                )
            
            # Calculate articles per category
            articles_per_category = max(1, page_size // len(categories))
            all_articles = []
            
            # Fetch articles for each category in parallel
            tasks = []
            for cat in categories:
                tasks.append(
                    self._fetch_articles_from_rss(
                        query=cat,
                        category=cat.lower(),
                        page_size=articles_per_category,
                        page=page
                    )
                )
            
            # Wait for all category fetches to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results and filter out errors
            for result in results:
                if isinstance(result, list):
                    all_articles.extend(result)
            
            # Shuffle articles to mix categories
            random.shuffle(all_articles)
            
            # Return the requested number of articles
            return all_articles[:page_size]

    async def _fetch_articles_from_rss(self,
                      query: Optional[str] = None,
                      category: Optional[str] = None,
                      page_size: int = 10,
                      page: int = 1) -> List[Dict]:
        """
        Fetch articles from RSS feeds and extract full content using async/await
        """
        try:
            # Define a list of popular RSS feeds by category
            rss_feeds = {
                'technology': [
                    'https://techcrunch.com/feed/',
                    'https://www.theverge.com/rss/index.xml',
                    'https://www.wired.com/feed/rss',
                    'https://www.engadget.com/rss.xml',
                    'https://www.zdnet.com/news/rss.xml',
                    'https://www.techradar.com/rss',
                    'https://www.digitaltrends.com/feed/',
                    'https://www.techspot.com/feeds/',
                    'https://www.techmeme.com/feed.xml',
                    'https://www.techrepublic.com/rss/',
                    'https://www.techdirt.com/feed/',
                    'https://www.techworld.com/rss',
                    'https://www.techhive.com/feed/',
                    'https://www.techrepublic.com/rss/',
                    'https://www.techspot.com/feeds/'
                ],
                'business': [
                    'https://www.bloomberg.com/feeds/sitemap_news.xml',
                    'https://www.reutersagency.com/feed/',
                    'https://www.ft.com/rss/home',
                    'https://www.wsj.com/xml/rss/3_7085.xml',
                    'https://www.cnbc.com/id/100003114/device/rss/rss.html',
                    'https://www.businessinsider.com/rss',
                    'https://www.marketwatch.com/rss',
                    'https://www.fool.com/feed/',
                    'https://www.investors.com/feed/',
                    'https://www.morningstar.com/rss',
                    'https://www.barrons.com/rss',
                    'https://www.fortune.com/feed/',
                    'https://www.inc.com/rss',
                    'https://www.fastcompany.com/feed',
                    'https://www.entrepreneur.com/rss'
                ],
                'politics': [
                    'https://www.politico.com/rss/politicopicks.xml',
                    'https://www.theguardian.com/politics/rss',
                    'https://www.nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/section/politics/rss.xml',
                    'https://www.washingtonpost.com/politics/feed/',
                    'https://www.bbc.com/news/politics/rss.xml',
                    'https://www.npr.org/rss/politics/',
                    'https://www.cnn.com/politics/rss',
                    'https://www.foxnews.com/politics/rss',
                    'https://www.cbsnews.com/politics/rss/',
                    'https://www.nbcnews.com/politics/rss',
                    'https://www.abcnews.go.com/politics/rss',
                    'https://www.politifact.com/rss/',
                    'https://www.factcheck.org/feed/',
                    'https://www.opensecrets.org/rss/',
                    'https://www.rollcall.com/feed/'
                ],
                'entertainment': [
                    'https://www.rollingstone.com/feed/',
                    'https://www.variety.com/feed',
                    'https://www.hollywoodreporter.com/feed',
                    'https://www.ew.com/feed/',
                    'https://www.billboard.com/feed/',
                    'https://www.people.com/rss/',
                    'https://www.eonline.com/feed',
                    'https://www.usmagazine.com/feed/',
                    'https://www.etonline.com/feed',
                    'https://www.tmz.com/rss.xml',
                    'https://www.entertainmentweekly.com/feed',
                    'https://www.vulture.com/feed',
                    'https://www.pitchfork.com/feed/',
                    'https://www.spin.com/feed/',
                    'https://www.stereogum.com/feed/'
                ],
                'sports': [
                    'https://www.espn.com/espn/rss/news',
                    'https://www.si.com/rss/si_topstories.xml',
                    'https://www.skysports.com/rss/0,20514,11661,00.xml',
                    'https://www.bbc.com/sport/rss.xml',
                    'https://www.theguardian.com/sport/rss',
                    'https://www.cbssports.com/rss/',
                    'https://www.nbcsports.com/rss',
                    'https://www.foxsports.com/rss',
                    'https://www.sportingnews.com/rss',
                    'https://www.bleacherreport.com/rss',
                    'https://www.sportsillustrated.com/rss',
                    'https://www.nfl.com/rss',
                    'https://www.nba.com/rss',
                    'https://www.mlb.com/rss',
                    'https://www.nhl.com/rss'
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
            
            # Create aiohttp session
            session = await self._get_session()
            
            # Fetch feeds in parallel with timeout
            async def fetch_feed(feed_url: str) -> List[Dict]:
                try:
                    async with session.get(feed_url, timeout=5) as response:
                        if response.status != 200:
                            return []
                        content = await response.text()
                        feed = feedparser.parse(content)
                        if not feed.entries:
                            return []
                            
                        articles = []
                        for entry in feed.entries[:3]:  # Only process first 3 entries per feed
                            title = entry.get('title', '')
                            url = entry.get('link', '')
                            if not title or not url:
                                continue
                                
                            published = entry.get('published', '')
                            source = feed.feed.get('title', 'Unknown Source')
                            
                            # Generate article ID
                            article_id = f"{source}-{title}"[:50].replace(" ", "-").lower()
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
                                    "content": content,
                                    "source": source,
                                    "url": url,
                                    "published_at": published,
                                    "image_url": image_url,
                                    "category": category if category else "other"
                                }
                                articles.append(article_data)
                        return articles
                except Exception as e:
                    logger.warning(f"Error fetching feed {feed_url}: {str(e)}")
                    return []
            
            # Fetch all feeds in parallel
            tasks = [fetch_feed(feed_url) for feed_url in selected_feeds]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Flatten results and filter out errors
            all_articles = []
            for result in results:
                if isinstance(result, list):
                    all_articles.extend(result)
            
            # Shuffle articles and select the ones we'll return
            random.shuffle(all_articles)
            selected_articles = all_articles[:page_size]
            
            # Extract full content and images only for the selected articles
            logger.info(f"Extracting full content for {len(selected_articles)} articles...")
            
            # Process articles in parallel with timeout
            async def process_article(article: Dict) -> Dict:
                try:
                    extracted = await self._extract_article_content_async(
                        article['url'],
                        article.get('title', '')
                    )
                    if extracted.get('content') and len(extracted['content']) > len(article['content']):
                        article['content'] = extracted['content']
                    if extracted.get('image_url'):
                        article['image_url'] = extracted['image_url']
                except Exception as e:
                    logger.warning(f"Error extracting content for {article['url']}: {str(e)}")
                return article
            
            # Process articles in parallel with timeout
            tasks = [process_article(article) for article in selected_articles]
            processed_articles = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out errors and return valid articles
            return [article for article in processed_articles if isinstance(article, dict)]
                    
        except Exception as e:
            logger.error(f"Error fetching articles from RSS: {str(e)}")
            return []
        finally:
            # Close session
            await self._close_session()

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
            
    async def fetch_top_headlines(self, page_size: int = 10) -> List[Dict]:
        """
        Fetch top headlines from all category RSS feeds and return the most recent/popular articles.
        """
        articles = []
        seen_urls = set()
        rss_feeds = {
            'techn': [
                    'https://techcrunch.com/feed/',
                    'https://www.theverge.com/rss/index.xml',
                    'https://www.wired.com/feed/rss',
                    'https://www.engadget.com/rss.xml',
                    'https://www.zdnet.com/news/rss.xml',
                    'https://www.techradar.com/rss',
                    'https://www.digitaltrends.com/feed/',
                    'https://www.techspot.com/feeds/',
                    'https://www.techmeme.com/feed.xml',
                    'https://www.techrepublic.com/rss/',
                    'https://www.techdirt.com/feed/',
                    'https://www.techworld.com/rss',
                    'https://www.techhive.com/feed/',
                    'https://www.techrepublic.com/rss/',
                    'https://www.techspot.com/feeds/'
                ],
                'business': [
                    'https://www.bloomberg.com/feeds/sitemap_news.xml',
                    'https://www.reutersagency.com/feed/',
                    'https://www.ft.com/rss/home',
                    'https://www.wsj.com/xml/rss/3_7085.xml',
                    'https://www.cnbc.com/id/100003114/device/rss/rss.html',
                    'https://www.businessinsider.com/rss',
                    'https://www.marketwatch.com/rss',
                    'https://www.fool.com/feed/',
                    'https://www.investors.com/feed/',
                    'https://www.morningstar.com/rss',
                    'https://www.barrons.com/rss',
                    'https://www.fortune.com/feed/',
                    'https://www.inc.com/rss',
                    'https://www.fastcompany.com/feed',
                    'https://www.entrepreneur.com/rss'
                ],
                'politics': [
                    'https://www.politico.com/rss/politicopicks.xml',
                    'https://www.theguardian.com/politics/rss',
                    'https://www.nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/section/politics/rss.xml',
                    'https://www.washingtonpost.com/politics/feed/',
                    'https://www.bbc.com/news/politics/rss.xml',
                    'https://www.npr.org/rss/politics/',
                    'https://www.cnn.com/politics/rss',
                    'https://www.foxnews.com/politics/rss',
                    'https://www.cbsnews.com/politics/rss/',
                    'https://www.nbcnews.com/politics/rss',
                    'https://www.abcnews.go.com/politics/rss',
                    'https://www.politifact.com/rss/',
                    'https://www.factcheck.org/feed/',
                    'https://www.opensecrets.org/rss/',
                    'https://www.rollcall.com/feed/'
                ],
                'entertainment': [
                    'https://www.rollingstone.com/feed/',
                    'https://www.variety.com/feed',
                    'https://www.hollywoodreporter.com/feed',
                    'https://www.ew.com/feed/',
                    'https://www.billboard.com/feed/',
                    'https://www.people.com/rss/',
                    'https://www.eonline.com/feed',
                    'https://www.usmagazine.com/feed/',
                    'https://www.etonline.com/feed',
                    'https://www.tmz.com/rss.xml',
                    'https://www.entertainmentweekly.com/feed',
                    'https://www.vulture.com/feed',
                    'https://www.pitchfork.com/feed/',
                    'https://www.spin.com/feed/',
                    'https://www.stereogum.com/feed/'
                ],
                'sport': [
                    'https://www.espn.com/espn/rss/news',
                    'https://www.si.com/rss/si_topstories.xml',
                    'https://www.skysports.com/rss/0,20514,11661,00.xml',
                    'https://www.bbc.com/sport/rss.xml',
                    'https://www.theguardian.com/sport/rss',
                    'https://www.cbssports.com/rss/',
                    'https://www.nbcsports.com/rss',
                    'https://www.foxsports.com/rss',
                    'https://www.sportingnews.com/rss',
                    'https://www.bleacherreport.com/rss',
                    'https://www.sportsillustrated.com/rss',
                    'https://www.nfl.com/rss',
                    'https://www.nba.com/rss',
                    'https://www.mlb.com/rss',
                    'https://www.nhl.com/rss'
                ],
        }

        # Create aiohttp session
        session = await self._get_session()
        
        async def fetch_feed(feed_url: str) -> List[Dict]:
            try:
                async with session.get(feed_url, timeout=5) as response:
                    if response.status != 200:
                        return []
                    content = await response.text()
                    feed = feedparser.parse(content)
                    if not feed.entries:
                        return []
                        
                    articles = []
                    for entry in feed.entries[:3]:  # Only process first 3 entries per feed
                        title = entry.get('title', '')
                        url = entry.get('link', '')
                        if not url or url in seen_urls:
                            continue
                        seen_urls.add(url)
                        published = entry.get('published', '')
                        source = feed.feed.get('title', 'Unknown Source')
                        article_id = f"{source}-{title}"[:50].replace(" ", "-").lower()
                        if url:
                            url_hash = str(hash(url))[:8]
                            article_id = f"{article_id}-{url_hash}"
                        content = entry.get('summary', '')
                        if not content and entry.get('content'):
                            content = entry.get('content')[0].get('value', '')
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
                                "content": content,
                                "source": source,
                                "url": url,
                                "published_at": published,
                                "image_url": image_url,
                                "category": 'general'
                            }
                            articles.append(article_data)
                    return articles
            except Exception as e:
                logger.warning(f"Error fetching feed {feed_url}: {str(e)}")
                return []

        # Collect all feed URLs
        all_feeds = []
        for feeds in rss_feeds.values():
            all_feeds.extend(feeds)

        # Fetch all feeds in parallel
        tasks = [fetch_feed(feed_url) for feed_url in all_feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results and filter out errors
        for result in results:
            if isinstance(result, list):
                articles.extend(result)

        # Extract full content and images for each article in parallel
        async def process_article(article: Dict) -> Dict:
            try:
                extracted = await self._extract_article_content_async(
                    article['url'],
                    article.get('title', '')
                )
                if extracted.get('content') and len(extracted['content']) > len(article['content']):
                    article['content'] = extracted['content']
                if extracted.get('image_url'):
                    article['image_url'] = extracted['image_url']
            except Exception as e:
                logger.warning(f"Error extracting content for {article['url']}: {str(e)}")
            return article

        # Process articles in parallel
        tasks = [process_article(article) for article in articles]
        processed_articles = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        articles = [article for article in processed_articles if isinstance(article, dict)]

        # Sort articles by publish date (descending)
        def parse_date(date_str):
            from datetime import datetime
            for fmt in ('%a, %d %b %Y %H:%M:%S %Z', '%Y-%m-%dT%H:%M:%SZ'):
                try:
                    return datetime.strptime(date_str, fmt)
                except Exception:
                    continue
            return datetime.min

        articles.sort(key=lambda x: parse_date(x['published_at']), reverse=True)
        random.shuffle(articles)
        
        # Close session
        await self._close_session()
        
        return articles[:page_size]

    def fetch_test_articles(self, 
                      categories: List[str] = ["tech", "business", "politics", "entertainment", "sport"],
                      articles_per_category: int = 50,
                      use_rss_only: bool = True) -> List[Dict]:
        """
        Fetch test articles for each category using the category as the query.
        This is specifically designed for testing purposes.
        Adds timeouts and progress output to avoid hanging on slow feeds.
        Ensures at least articles_per_category per category if possible.
        Prints a summary at the end.
        """
        import requests
        import time
        all_articles = []
        rss_feeds = {
            'tech': [
                'https://techcrunch.com/feed/',
                'https://www.theverge.com/rss/index.xml',
                'https://www.wired.com/feed/rss',
                'https://www.engadget.com/rss.xml',
                'https://www.zdnet.com/news/rss.xml',
                'https://www.techradar.com/rss',
                'https://www.digitaltrends.com/feed/',
                'https://www.techspot.com/feeds/',
                'https://www.techmeme.com/feed.xml',
                'https://www.techrepublic.com/rss/'
            ],
            'business': [
                'https://www.bloomberg.com/feeds/sitemap_news.xml',
                'https://www.reutersagency.com/feed/',
                'https://www.ft.com/rss/home',
                'https://www.wsj.com/xml/rss/3_7085.xml',
                'https://www.cnbc.com/id/100003114/device/rss/rss.html',
                'https://www.businessinsider.com/rss',
                'https://www.marketwatch.com/rss',
                'https://www.fool.com/feed/',
                'https://www.investors.com/feed/',
                'https://www.morningstar.com/rss'
            ],
            'politics': [
                'https://www.politico.com/rss/politicopicks.xml',
                'https://www.theguardian.com/politics/rss',
                'https://www.nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/section/politics/rss.xml',
                'https://www.washingtonpost.com/politics/feed/',
                'https://www.bbc.com/news/politics/rss.xml',
                'https://www.npr.org/rss/politics/',
                'https://www.cnn.com/politics/rss',
                'https://www.foxnews.com/politics/rss',
                'https://www.cbsnews.com/politics/rss/',
                'https://www.nbcnews.com/politics/rss'
            ],
            'entertainment': [
                'https://www.rollingstone.com/feed/',
                'https://www.variety.com/feed',
                'https://www.hollywoodreporter.com/feed',
                'https://www.ew.com/feed/',
                'https://www.billboard.com/feed/',
                'https://www.people.com/rss/',
                'https://www.eonline.com/feed',
                'https://www.usmagazine.com/feed/',
                'https://www.etonline.com/feed',
                'https://www.tmz.com/rss.xml'
            ],
            'sport': [
                'https://www.espn.com/espn/rss/news',
                'https://www.si.com/rss/si_topstories.xml',
                'https://www.skysports.com/rss/0,20514,11661,00.xml',
                'https://www.bbc.com/sport/rss.xml',
                'https://www.theguardian.com/sport/rss',
                'https://www.cbssports.com/rss/',
                'https://www.nbcsports.com/rss',
                'https://www.foxsports.com/rss',
                'https://www.sportingnews.com/rss',
                'https://www.bleacherreport.com/rss'
            ]
        }
        category_counts = {cat: 0 for cat in categories}
        feed_failures = {cat: [] for cat in categories}
        for category in categories:
            print(f"\nFetching {category} articles...")
            feeds = rss_feeds.get(category, [])
            category_articles = []
            for feed_url in feeds:
                if len(category_articles) >= articles_per_category:
                    break
                print(f"  Fetching feed: {feed_url}")
                try:
                    start_time = time.time()
                    resp = requests.get(feed_url, timeout=5)
                    elapsed = time.time() - start_time
                    if resp.status_code != 200:
                        print(f"    Skipped (HTTP {resp.status_code})")
                        feed_failures[category].append((feed_url, f"HTTP {resp.status_code}"))
                        continue
                    feed = feedparser.parse(resp.content)
                    if not feed.entries:
                        print("    No entries found.")
                        feed_failures[category].append((feed_url, "No entries"))
                        continue
                    for entry in feed.entries:
                        if len(category_articles) >= articles_per_category:
                            break
                        title = entry.get('title', '')
                        url = entry.get('link', '')
                        published = entry.get('published', '')
                        source = feed.feed.get('title', 'Unknown Source')
                        article_id = f"{source}-{title}"[:50].replace(" ", "-").lower()
                        if url:
                            url_hash = str(hash(url))[:8]
                            article_id = f"{article_id}-{url_hash}"
                        content = entry.get('summary', '')
                        if not content and entry.get('content'):
                            content = entry.get('content')[0].get('value', '')
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
                                "content": content,
                                "source": source,
                                "url": url,
                                "published_at": published,
                                "image_url": image_url,
                                "category": category,
                                "confidence": round(random.uniform(0.85, 0.99), 2)
                            }
                            # Ensure published_at is timezone-aware
                            if "published_at" in article_data:
                                try:
                                    dt = datetime.fromisoformat(article_data["published_at"].replace('Z', '+00:00'))
                                    if dt.tzinfo is None:
                                        dt = dt.replace(tzinfo=timezone.utc)
                                    article_data["published_at"] = dt.isoformat()
                                except (ValueError, AttributeError):
                                    article_data["published_at"] = datetime.now(timezone.utc).isoformat()
                            category_articles.append(article_data)
                    print(f"    Got {len(feed.entries)} entries in {elapsed:.2f}s.")
                except Exception as e:
                    print(f"    Skipped (error: {str(e)})")
                    feed_failures[category].append((feed_url, str(e)))
                    continue
            # Shuffle and select up to articles_per_category
            random.shuffle(category_articles)
            all_articles.extend(category_articles[:articles_per_category])
            category_counts[category] = len(category_articles[:articles_per_category])
        # Fetch general articles (optional, can be skipped for speed)
        print("\nFetching general articles...")
        general_articles = self.fetch_articles(
            query="__GENERAL__",
            page_size=articles_per_category,
            use_rss_only=use_rss_only,
            force_refresh=True
        )
        for article in general_articles:
            article["category"] = "general"
            article["confidence"] = round(random.uniform(0.85, 0.99), 2)
            if "published_at" in article:
                try:
                    dt = datetime.fromisoformat(article["published_at"].replace('Z', '+00:00'))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    article["published_at"] = dt.isoformat()
                except (ValueError, AttributeError):
                    article["published_at"] = datetime.now(timezone.utc).isoformat()
            all_articles.append(article)
        # Print summary
        print("\n=== Fetch Summary ===")
        for cat in categories:
            print(f"{cat}: {category_counts[cat]} articles fetched.")
            if feed_failures[cat]:
                print(f"  Feeds with issues:")
                for url, reason in feed_failures[cat]:
                    print(f"    {url} - {reason}")
        print("====================\n")
        return all_articles

    async def fetch_articles_from_rss_async(self, feed_url: str) -> List[Dict]:
        """
        Fetch and parse articles from an RSS feed asynchronously
        Args:
            feed_url: URL of the RSS feed to fetch
        Returns:
            List of article dictionaries from the feed
        """
        try:
            with Timer(f"Fetching RSS feed: {feed_url}"):
                session = await self._get_session()
                async with session.get(feed_url, timeout=10) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch RSS feed: {feed_url}")
                        return []
                        
                    content = await response.text()
                    feed = feedparser.parse(content)
                    
                    if not feed.entries:
                        logger.warning(f"No entries found in RSS feed: {feed_url}")
                        return []
                        
                    articles = []
                    for entry in feed.entries:
                        # Extract basic article information
                        article = {
                            "title": entry.get('title', ''),
                            "url": entry.get('link', ''),
                            "published_at": entry.get('published', datetime.now().isoformat()),
                            "source": feed.feed.get('title', 'Unknown Source'),
                            "description": entry.get('description', '')
                        }
                        
                        # Only process articles with valid URLs
                        if article['url']:
                            articles.append(article)
                    
                    # Extract full content in parallel
                    return await self._extract_articles_parallel_async(articles)
                    
        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {str(e)}")
            return []

    async def discover_rss_feeds_async(self, url: str) -> Set[str]:
        """
        Discover RSS feeds from a website URL
        Args:
            url: Website URL to search for RSS feeds
        Returns:
            Set of discovered RSS feed URLs
        """
        try:
            with Timer(f"Discovering RSS feeds from: {url}"):
                session = await self._get_session()
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        return set()
                        
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Look for RSS feed links
                    feeds = set()
                    for link in soup.find_all('link'):
                        if link.get('type') in ['application/rss+xml', 'application/atom+xml']:
                            feed_url = link.get('href')
                            if feed_url:
                                # Convert relative URLs to absolute
                                feed_url = urljoin(url, feed_url)
                                feeds.add(feed_url)
                    
                    return feeds
                    
        except Exception as e:
            logger.error(f"Error discovering RSS feeds from {url}: {str(e)}")
            return set()

    async def fetch_articles_from_multiple_sources_async(self,
                                                       query: Optional[str] = None,
                                                       category: Optional[str] = None,
                                                       language: str = "en",
                                                       page_size: int = 10,
                                                       days_back: Optional[int] = None) -> List[Dict]:
        """
        Fetch articles from multiple sources in parallel
        Args:
            query: Search query string
            category: News category to filter by
            language: Language code (default: "en")
            page_size: Number of articles per page
            days_back: Number of days to look back
        Returns:
            Combined list of articles from all sources
        """
        try:
            with Timer("Fetching from multiple sources"):
                # Fetch from NewsAPI
                newsapi_articles = await self.fetch_articles_async(
                    query=query,
                    category=category,
                    language=language,
                    page_size=page_size,
                    days_back=days_back
                )
                
                # Fetch from RSS feeds if available
                rss_articles = []
                if self.discovered_feeds:
                    for feed_url in self.discovered_feeds.get(category, set()):
                        articles = await self.fetch_articles_from_rss_async(feed_url)
                        rss_articles.extend(articles)
                
                # Combine and deduplicate articles
                all_articles = newsapi_articles + rss_articles
                seen_urls = set()
                unique_articles = []
                
                for article in all_articles:
                    url = article.get('url')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        unique_articles.append(article)
                
                return unique_articles[:page_size]
                
        except Exception as e:
            logger.error(f"Error fetching from multiple sources: {str(e)}")
            return []

    async def update_feed_discovery_async(self, category: str):
        """
        Update discovered RSS feeds for a category
        Args:
            category: Category to update feeds for
        """
        try:
            with Timer(f"Updating feed discovery for category: {category}"):
                # Get category-specific news sources
                sources = self.news_sources
                if category:
                    sources = [s for s in sources if category in s.lower()]
                
                # Discover feeds from each source
                for source in sources:
                    base_url = f"https://{source}.com"
                    feeds = await self.discover_rss_feeds_async(base_url)
                    
                    if feeds:
                        if category not in self.discovered_feeds:
                            self.discovered_feeds[category] = set()
                        self.discovered_feeds[category].update(feeds)
                        
        except Exception as e:
            logger.error(f"Error updating feed discovery: {str(e)}")

    async def cleanup(self):
        """Clean up resources and close connections"""
        await self._close_session() 