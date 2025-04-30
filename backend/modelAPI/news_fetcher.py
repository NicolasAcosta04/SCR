import requests
import feedparser
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
import os
import re
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
from newsapi import NewsApiClient
from category_mappings import validate_category, validate_subcategory, map_to_main_category, map_to_subcategory, get_subcategories

load_dotenv()

class NewsFetcher:
    def __init__(self):
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self.news_api = NewsApiClient(api_key=self.news_api_key)
        self.discovered_feeds: Dict[str, Set[str]] = {}  # Cache discovered feeds by category
        
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
            search_url = f"https://html.duckduckgo.com/html/?q={query}+rss+feed"
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
        
    def _format_article(self, article: Dict, source: str = "newsapi") -> Dict:
        """Format article data consistently regardless of source"""
        if source == "newsapi":
            # Try to get the best available image
            image_url = None
            
            # First try urlToImage (most common in News API)
            if article.get("urlToImage"):
                image_url = article.get("urlToImage")
            
            # Then try media objects
            elif article.get("media"):
                # Some sources provide media objects
                media = article.get("media", [])
                if media and isinstance(media, list):
                    for item in media:
                        if item.get("type") == "image" and item.get("url"):
                            image_url = item.get("url")
                            break
            
            # Get category and subcategory
            category = article.get("category", "other")
            # subcategory = article.get("subcategory")
            # if not subcategory:
            #     # If no subcategory is provided, use the first subcategory from the main category
            #     subcategories = get_subcategories(category)
            #     subcategory = subcategories[0] if subcategories else "general"
            
            # Then try to extract from content
            if article.get("content"): # was elif
                try:
                    soup = BeautifulSoup(article.get("content", ""), 'lxml')
                    img = soup.find('img')
                    if img and img.get('src'):
                        image_url = img['src']
                except:
                    pass
            
            # Generate a unique article ID
            article_id = article.get("url", "").split("/")[-1]
            if not article_id or len(article_id) < 5:  # If the URL doesn't provide a good ID
                # Use a combination of source and title
                source_name = article.get("source", {}).get("name", "unknown")
                title = article.get("title", "")
                article_id = f"{source_name}-{title}"[:50].replace(" ", "-").lower()
            
            # Get the full content
            content = article.get("content", "")
            
            # Check if content is truncated
            if content and "..." in content:
                # Try to get the full content from description
                description = article.get("description", "")
                if description and len(description) > len(content.split("...")[0]):
                    content = description
            
            # If content is still truncated, try to get it from the URL
            if content and "..." in content:
                try:
                    response = requests.get(article.get("url", ""), timeout=5)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'lxml')
                        # Try to find the main content
                        main_content = soup.find('article') or soup.find('main') or soup.find('div', class_='content')
                        if main_content:
                            # Get all paragraphs
                            paragraphs = main_content.find_all('p')
                            if paragraphs:
                                # Combine all paragraphs
                                full_content = ' '.join([p.get_text() for p in paragraphs])
                                if len(full_content) > len(content.split("...")[0]):
                                    content = full_content
                except:
                    pass
            
            return {
                "article_id": article_id,
                "title": article.get("title", ""),
                "content": content,
                "source": article.get("source", {}).get("name", ""),
                "url": article.get("url", ""),
                "published_at": article.get("publishedAt", ""),
                "image_url": image_url,
                "category": category,
                # "subcategory": subcategory
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
            # subcategory = article.get("subcategory")
            # if not subcategory:
            #     # If no subcategory is provided, use the first subcategory from the main category
            #     subcategories = get_subcategories(category)
            #     subcategory = subcategories[0] if subcategories else "general"
                
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
            
            # If content is still truncated, try to get it from the URL
            if content and "..." in content:
                try:
                    response = requests.get(article.get("link", ""), timeout=5)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'lxml')
                        # Try to find the main content
                        main_content = soup.find('article') or soup.find('main') or soup.find('div', class_='content')
                        if main_content:
                            # Get all paragraphs
                            paragraphs = main_content.find_all('p')
                            if paragraphs:
                                # Combine all paragraphs
                                full_content = ' '.join([p.get_text() for p in paragraphs])
                                if len(full_content) > len(content.split("...")[0]):
                                    content = full_content
                except:
                    pass
            
            return {
                "article_id": article_id,
                "title": article.get("title", ""),
                "content": content,
                "source": source,
                "url": article.get("link", ""),
                "published_at": article.get("published", ""),
                "image_url": image_url,
                "category": category,
                # "subcategory": subcategory
            }
    
    def fetch_articles(self, 
                      query: Optional[str] = None,
                      category: Optional[str] = None,
                      language: str = "en",
                      page_size: int = 10,
                      days_back: int = 7,
                      use_rss: bool = True,
                      discover_feeds: bool = True) -> List[Dict]:
        """
        Fetch articles from News API and optionally RSS feeds
        """
        articles = []
        
        # Try News API first if we have a key
        if self.news_api_key:
            try:
                # Calculate dates correctly
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days_back)
                
                # Format dates as YYYY-MM-DD
                from_date = start_date.strftime("%Y-%m-%d")
                to_date = end_date.strftime("%Y-%m-%d")
                
                # Ensure we have at least one required parameter
                if not query and not category:
                    query = "technology OR science OR business OR health"  # Default query
                
                # Use the Python client library
                news_api_articles = self.news_api.get_everything(
                    q=query,
                    from_param=from_date,
                    to=to_date,
                    language=language,
                    sort_by="publishedAt",
                    page_size=page_size
                )
                
                if news_api_articles.get("status") == "ok":
                    articles.extend([self._format_article(article, "newsapi") for article in news_api_articles.get("articles", [])])
                else:
                    print(f"News API error: {news_api_articles.get('message', 'Unknown error')}")
                
            except Exception as e:
                print(f"News API error: {str(e)}")
        
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
            
    def fetch_top_headlines(self, 
                          country: str = "us",
                          category: Optional[str] = None,
                          page_size: int = 10,
                          use_rss: bool = True,
                          discover_feeds: bool = True) -> List[Dict]:
        """
        Fetch top headlines from News API and optionally RSS feeds
        """
        articles = []
        
        # Try News API first if we have a key
        if self.news_api_key:
            try:
                # Use the Python client library
                news_api_articles = self.news_api.get_top_headlines(
                    country=country,
                    category=category,
                    page_size=page_size
                )
                
                if news_api_articles.get("status") == "ok":
                    articles.extend([self._format_article(article, "newsapi") for article in news_api_articles.get("articles", [])])
                
            except Exception as e:
                print(f"News API error: {str(e)}")
        
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