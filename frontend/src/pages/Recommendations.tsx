import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Article from '../components/Article';
import Header from '../components/Header';
import BottomNavBar from '../components/BottomNavBar';
import { useUser } from '../contexts/UserContext';
import Skeleton from '../components/Skeleton';
import ErrorComponent from '../components/ErrorComponent';

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

const Recommendations = () => {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const navigate = useNavigate();
  const { userId, token } = useUser();
  const displayedArticleIds = useRef(new Set());

  const fetchRecommendations = async (pageNum: number = 1, shouldAppend: boolean = true) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `http://localhost:8080/articles/recommendations/${userId}?num_recommendations=10&page=${pageNum}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch recommendations');
      }

      const newArticles = await response.json();

      // Filter out articles already displayed
      const filteredArticles = newArticles.filter(
        (article: Article) => !displayedArticleIds.current.has(article.article_id)
      );

      // Add new article IDs to the set
      filteredArticles.forEach((article: Article) => displayedArticleIds.current.add(article.article_id));

      if (filteredArticles.length === 0) {
        console.log('No more recommendations available');
        setHasMore(false);
      } else {
        if (shouldAppend) {
          setArticles((prevArticles) => [...prevArticles, ...filteredArticles]);
        } else {
          setArticles(filteredArticles);
        }
        setPage(pageNum);
        setHasMore(true);
      }
    } catch (err) {
      console.error('Error fetching recommendations:', err);
      setError(err instanceof Error ? err.message : 'Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userId && token) {
      fetchRecommendations(1, false);
    }
  }, [userId, token]);

  const handleScroll = () => {
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 100) {
      if (!loading && hasMore) {
        console.log('Scroll threshold reached, loading more recommendations...');
        const nextPage = page + 1;
        setPage(nextPage);
        fetchRecommendations(nextPage, true);
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
        navigate(`/recommendations/${article.article_id}`, {
          state: { article },
        });
      }}
    />
  ));

  if (error) {
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
      <main className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24'>
        <div className='mb-6'>
          <h2 className='text-2xl font-bold text-gray-900 dark:text-white'>Recommended for You</h2>
          <p className='text-gray-600 dark:text-gray-400 mt-2'>
            Articles tailored to your interests and reading history
          </p>
        </div>
        <div className='space-y-6'>
          {loading && articles.length === 0 ? <Skeleton /> : Articles}
          {loading && articles.length > 0 && (
            <div className='text-center'>
              <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto'></div>
            </div>
          )}
          {!loading && articles.length === 0 && (
            <div className='text-center py-12'>
              <p className='text-gray-600 dark:text-gray-400'>
                No recommendations available yet. Start reading articles to get personalized recommendations!
              </p>
            </div>
          )}
        </div>
      </main>
      <BottomNavBar />
    </div>
  );
};

export default Recommendations;
