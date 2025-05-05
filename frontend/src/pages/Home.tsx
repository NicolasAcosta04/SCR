import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Article from '../components/Article';
import Header from '../components/Header';
import BottomNavBar from '../components/BottomNavBar';
import { useUser } from '../contexts/UserContext';
import Skeleton from '../components/Skeleton';
import ErrorComponent from '../components/ErrorComponent';
import RefreshArticlesButton from '../components/RefreshArticlesButton';
import Categories from '../components/Categories';

// Create a cache outside the component to persist between renders
const articleCache = {
  articles: [] as Article[],
  page: 1,
  hasMore: true,
  lastFetchTime: 0,
  CACHE_DURATION: 5 * 60 * 1000, // 5 minutes in milliseconds
  currentQuery: '', // Add current query tracking
};

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

const GENERAL_QUERY = '__GENERAL__';

const Home = () => {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(false);
  const [skeleton, setSkeleton] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activePreference, setActivePreference] = useState<string | null>(null);
  const navigate = useNavigate();
  const mainRef = useRef<HTMLDivElement>(null);
  const scrollPositionRef = useRef<number>(0);
  const { userId, token, userDetails } = useUser();
  const displayedArticleIds = useRef(new Set());

  // Log initial context state
  useEffect(() => {
    console.log('Home component mounted', { userId, hasToken: !!token });
  }, [userId, token]);

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
        console.log('Restoring scroll position:', position);
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

  // Clear cache and fetch new articles on mount
  useEffect(() => {
    console.log('Initial article fetch - checking cache...');
    // Check if we have cached articles that are still valid
    const now = Date.now();
    if (articleCache.articles.length > 0 && now - articleCache.lastFetchTime < articleCache.CACHE_DURATION) {
      console.log('Using cached articles:', {
        count: articleCache.articles.length,
        age: Math.round((now - articleCache.lastFetchTime) / 1000) + 's',
      });
      setArticles(articleCache.articles);
      setPage(articleCache.page);
      setHasMore(articleCache.hasMore);
    } else {
      console.log('Cache expired or empty, fetching fresh articles...');
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

  // Update activePreference when userDetails change
  useEffect(() => {
    if (userDetails?.preferences && userDetails.preferences.length > 0) {
      setActivePreference(userDetails.preferences[0]);
    }
  }, [userDetails]);

  const handleRefresh = async () => {
    console.log('Manual refresh triggered');
    setRefreshing(true);
    setLoading(true);
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

  // Helper to get label for a category
  const getCategoryLabel = (cat: string) => {
    switch (cat) {
      case 'tech':
        return 'Technology';
      case 'business':
        return 'Business';
      case 'politics':
        return 'Politics';
      case 'entertainment':
        return 'Entertainment';
      case 'sport':
        return 'Sports';
      default:
        return cat.charAt(0).toUpperCase() + cat.slice(1);
    }
  };

  // Modified fetchArticles to accept a category filter
  const fetchArticles = async (
    pageNum: number = 1,
    shouldAppend: boolean = true,
    forceRefresh: boolean = false,
    categoryOverride: string | null = null
  ) => {
    try {
      setLoading(true);
      setError(null); // Clear any previous errors

      let query = '';
      if (categoryOverride) {
        query = getCategoryLabel(categoryOverride);
      } else if (userDetails?.preferences && userDetails.preferences.length > 0) {
        // If user has multiple preferences, combine them with OR operator
        if (userDetails.preferences.length > 1) {
          // Calculate how many articles we want per category
          query = userDetails.preferences.map((pref) => getCategoryLabel(pref)).join(' OR ');
        } else {
          // Single preference case
          query = getCategoryLabel(userDetails.preferences[0]);
        }
      } else {
        query = GENERAL_QUERY; // Use special indicator for general search
      }

      const requestBody = {
        query,
        page_size: 10,
        sort_by: 'popularity',
        page: pageNum,
        randomize_sources: true,
        force_refresh: forceRefresh,
        timestamp: Date.now(), // Always include timestamp to prevent caching
      };

      console.log('Fetching articles:', {
        page: pageNum,
        append: shouldAppend,
        forceRefresh,
        query: requestBody.query,
        preferences: userDetails?.preferences,
      });

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
      // Filter out articles already displayed
      const filteredArticles = newArticles.filter(
        (article: any) => !displayedArticleIds.current.has(article.article_id)
      );
      // Add new article IDs to the set
      filteredArticles.forEach((article: any) => displayedArticleIds.current.add(article.article_id));

      if (filteredArticles.length === 0) {
        console.log('No more articles available');
        setHasMore(false);
        articleCache.hasMore = false;
      } else {
        if (shouldAppend) {
          const updatedArticles = [...articles, ...filteredArticles];
          console.log('Appending articles:', {
            previousCount: articles.length,
            newCount: updatedArticles.length,
          });
          setArticles(updatedArticles);
          articleCache.articles = updatedArticles;
        } else {
          console.log('Setting new articles:', { count: filteredArticles.length });
          setArticles(filteredArticles);
          articleCache.articles = filteredArticles;
        }
        setPage(pageNum);
        articleCache.page = pageNum;
        setHasMore(true);
        articleCache.hasMore = true;
        articleCache.lastFetchTime = Date.now();
        articleCache.currentQuery = requestBody.query;
      }
    } catch (err) {
      console.error('Error fetching articles:', err);
      setError(err instanceof Error ? err.message : 'Failed to load articles');
    } finally {
      setLoading(false);
      setSkeleton(false);
    }
  };

  const handleScroll = () => {
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 100) {
      if (!loading && hasMore) {
        console.log('Scroll threshold reached, loading more articles...');
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

  const Articles = articles.map((article) => (
    <Article
      key={article.article_id}
      article_id={article.article_id}
      title={article.title}
      content={article.content}
      source={article.source}
      url={article.url}
      published_at={article.published_at}
      image_url={article.image_url}
      category={article.category.toUpperCase()}
      subcategory={article.subcategory}
      confidence={article.confidence}
      onNavigate={() => {
        scrollPositionRef.current = window.scrollY;
        sessionStorage.setItem('scrollPosition', scrollPositionRef.current.toString());
        console.log('Navigating to article:', {
          id: article.article_id,
          title: article.title,
          scrollPosition: scrollPositionRef.current,
        });
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
  ));

  if (error) {
    console.error('Error state:', error);
    return (
      <div className='min-h-screen bg-gray-50 dark:bg-gray-900 .styled-scrollbars'>
        <Header />
        <ErrorComponent error={error} />
        <BottomNavBar />
      </div>
    );
  }

  return (
    <div className='min-h-screen bg-gray-50 dark:bg-gray-900 .styled-scrollbars'>
      <Header />
      <main ref={mainRef} className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24'>
        <div className='flex justify-between items-center gap-4 mb-6'>
          <button
            onClick={() => navigate('/recommendations')}
            className='inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500'
          >
            Recommendations
          </button>
          <div className='flex items-center gap-4'>
            {/* Category Dropdown */}
            {userDetails?.preferences && userDetails.preferences.length > 1 && (
              <Categories
                activePreference={activePreference || ''}
                setActivePreference={setActivePreference}
                setLoading={setLoading}
                setPage={setPage}
                fetchArticles={fetchArticles}
                setSkeleton={setSkeleton}
                userDetails={userDetails}
                getCategoryLabel={getCategoryLabel}
              />
            )}
            <RefreshArticlesButton handleRefresh={handleRefresh} refreshing={refreshing} />
          </div>
        </div>
        <div className='space-y-6'>
          {loading && articles.length === 0 && <Skeleton />}
          {skeleton && articles.length > 0 ? <Skeleton /> : Articles}
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
