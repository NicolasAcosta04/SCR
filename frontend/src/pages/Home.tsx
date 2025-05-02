import { useEffect, useState, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Article from '../components/Article';
import Header from '../components/Header';
import BottomNavBar from '../components/BottomNavBar';

interface Article {
  article_id: string;
  title: string;
  content: string;
  source: string;
  url: string;
  published_at: string;
  image_url?: string;
  category: string;
  subcategory: string;
  confidence: number;
}

// Create a cache outside the component to persist between renders
const articleCache = {
  articles: [] as Article[],
  page: 1,
  hasMore: true,
  lastFetchTime: 0,
  CACHE_DURATION: 5 * 60 * 1000, // 5 minutes in milliseconds
  currentQuery: '', // Add current query tracking
};

// Define topics and categories for query rotation
const TOPICS = [
  'technology',
  'business',
  'politics',
  'entertainment',
  'sports',
  'science',
  'health',
  'environment',
  'education',
  'world',
];

const Home = () => {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [currentTopic, setCurrentTopic] = useState<string>('');
  const location = useLocation();
  const navigate = useNavigate();
  const mainRef = useRef<HTMLDivElement>(null);
  const scrollPositionRef = useRef<number>(0);

  // Save scroll position before navigating away
  useEffect(() => {
    const handleBeforeUnload = () => {
      sessionStorage.setItem('scrollPosition', window.scrollY.toString());
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  // Restore scroll position when articles are loaded
  useEffect(() => {
    if (articles.length > 0 && !loading) {
      const savedPosition = sessionStorage.getItem('scrollPosition');
      if (savedPosition) {
        const position = parseInt(savedPosition);
        // Use setTimeout to ensure the DOM is fully rendered
        setTimeout(() => {
          window.scrollTo({
            top: position,
            behavior: 'instant',
          });
          sessionStorage.removeItem('scrollPosition');
        }, 100);
      }
    }
  }, [articles, loading]);

  // Function to get a random topic
  const getRandomTopic = () => {
    const randomIndex = Math.floor(Math.random() * TOPICS.length);
    return TOPICS[randomIndex];
  };

  // Function to generate a query
  const generateQuery = () => {
    const topic = getRandomTopic();
    setCurrentTopic(topic);
    return topic; // Return just the single topic
  };

  // Clear cache and fetch new articles on mount
  useEffect(() => {
    // Check if we have cached articles that are still valid
    const now = Date.now();
    if (articleCache.articles.length > 0 && now - articleCache.lastFetchTime < articleCache.CACHE_DURATION) {
      setArticles(articleCache.articles);
      setPage(articleCache.page);
      setHasMore(articleCache.hasMore);
      setCurrentTopic(articleCache.currentQuery);
    } else {
      // Clear the cache if it's expired
      articleCache.articles = [];
      articleCache.page = 1;
      articleCache.hasMore = true;
      articleCache.lastFetchTime = 0;
      articleCache.currentQuery = '';

      // Fetch fresh articles
      fetchArticles(1, false, true);
    }
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    // Clear the cache
    articleCache.articles = [];
    articleCache.page = 1;
    articleCache.hasMore = true;
    articleCache.lastFetchTime = 0;
    articleCache.currentQuery = '';

    // Fetch new articles with a new random query
    await fetchArticles(1, false, true);
    setRefreshing(false);
  };

  const fetchArticles = async (pageNum: number = 1, shouldAppend: boolean = true, forceRefresh: boolean = false) => {
    try {
      setLoading(true);
      setError(null); // Clear any previous errors

      const requestBody = {
        query: forceRefresh
          ? generateQuery()
          : articleCache.currentQuery || 'technology OR business OR politics OR entertainment OR sports',
        page_size: 10,
        sort_by: 'popularity',
        page: pageNum,
        randomize_sources: true,
        force_refresh: forceRefresh,
        timestamp: Date.now(), // Always include timestamp to prevent caching
      };

      console.log('Request body:', requestBody.query);

      console.log('Fetching articles with params:', requestBody);

      const response = await fetch('http://localhost:8080/articles/fetch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          Pragma: 'no-cache',
          Expires: '0',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch articles');
      }

      const newArticles = await response.json();
      console.log('Received articles:', newArticles);

      if (newArticles.length === 0) {
        setHasMore(false);
        articleCache.hasMore = false;
      } else {
        if (shouldAppend) {
          const updatedArticles = [...articles, ...newArticles];
          setArticles(updatedArticles);
          articleCache.articles = updatedArticles;
        } else {
          setArticles(newArticles);
          articleCache.articles = newArticles;
        }
        setPage(pageNum);
        articleCache.page = pageNum;
        setHasMore(true);
        articleCache.hasMore = true;
        articleCache.lastFetchTime = Date.now();
        articleCache.currentQuery = requestBody.query;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load articles');
      console.error('Error fetching articles:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleScroll = () => {
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 100) {
      if (!loading && hasMore) {
        const nextPage = page + 1;
        setPage(nextPage);
        fetchArticles(nextPage, true);
      }
    }
  };

  useEffect(() => {
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [loading, hasMore, page]);

  if (loading && articles.length === 0) {
    return (
      <div className='min-h-screen bg-gray-50 dark:bg-gray-900 .styled-scrollbars'>
        <Header />
        <main className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24'>
          <div className='space-y-6'>
            {[...Array(3)].map((_, i) => (
              <div key={i} className='animate-pulse'>
                <div className='h-48 bg-gray-200 dark:bg-gray-700 rounded-lg mb-4'></div>
                <div className='h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2'></div>
                <div className='h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2'></div>
              </div>
            ))}
          </div>
        </main>
        <BottomNavBar />
      </div>
    );
  }

  if (error) {
    return (
      <div className='min-h-screen bg-gray-50 dark:bg-gray-900 .styled-scrollbars'>
        <Header />
        <main className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24'>
          <div className='bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6'>
            <div className='flex items-center gap-3 mb-4'>
              <svg className='w-6 h-6 text-red-500' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                <path
                  strokeLinecap='round'
                  strokeLinejoin='round'
                  strokeWidth={2}
                  d='M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'
                />
              </svg>
              <h2 className='text-xl font-semibold text-red-800 dark:text-red-200'>Error Loading Articles</h2>
            </div>
            <p className='text-red-700 dark:text-red-300 mb-4'>{error}</p>
          </div>
        </main>
        <BottomNavBar />
      </div>
    );
  }

  return (
    <div className='min-h-screen bg-gray-50 dark:bg-gray-900 .styled-scrollbars'>
      <Header />
      <main ref={mainRef} className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24'>
        <div className='flex justify-between items-center mb-4'>
          {currentTopic && (
            <div className='text-sm text-gray-600 dark:text-gray-400'>
              Current topic: <span className='font-medium capitalize'>{currentTopic}</span>
            </div>
          )}
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className='inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed'
          >
            {refreshing ? (
              <>
                <svg
                  className='animate-spin -ml-1 mr-3 h-5 w-5 text-white'
                  xmlns='http://www.w3.org/2000/svg'
                  fill='none'
                  viewBox='0 0 24 24'
                >
                  <circle className='opacity-25' cx='12' cy='12' r='10' stroke='currentColor' strokeWidth='4'></circle>
                  <path
                    className='opacity-75'
                    fill='currentColor'
                    d='M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z'
                  ></path>
                </svg>
                Refreshing...
              </>
            ) : (
              <>
                <svg
                  className='-ml-1 mr-2 h-5 w-5'
                  xmlns='http://www.w3.org/2000/svg'
                  fill='none'
                  viewBox='0 0 24 24'
                  stroke='currentColor'
                >
                  <path
                    strokeLinecap='round'
                    strokeLinejoin='round'
                    strokeWidth={2}
                    d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15'
                  />
                </svg>
                Refresh Articles
              </>
            )}
          </button>
        </div>
        <div className='space-y-6'>
          {articles.map((article) => (
            <Article
              key={article.article_id}
              article_id={article.article_id}
              title={article.title}
              content={article.content}
              source={article.source}
              url={article.url}
              published_at={article.published_at}
              image_url={article.image_url}
              category={article.category}
              subcategory={article.subcategory}
              confidence={article.confidence}
              onNavigate={() => {
                scrollPositionRef.current = window.scrollY;
                sessionStorage.setItem('scrollPosition', scrollPositionRef.current.toString());
                navigate(`/article/${article.article_id}`, {
                  state: {
                    article: {
                      article_id: article.article_id,
                      title: article.title,
                      content: article.content,
                      source: article.source,
                      url: article.url,
                      published_at: article.published_at,
                      image_url: article.image_url,
                      category: article.category,
                      subcategory: article.subcategory,
                      confidence: article.confidence,
                    },
                  },
                });
              }}
            />
          ))}
          {loading && articles.length > 0 && (
            <div className='text-center'>
              <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto'></div>
            </div>
          )}
        </div>
      </main>
      <BottomNavBar />
    </div>
  );
};

export default Home;
