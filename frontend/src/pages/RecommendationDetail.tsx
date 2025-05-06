import { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import Header from '../components/Header';
import BottomNavBar from '../components/BottomNavBar';
import { ArticleProps } from '../interfaces/Interfaces';

const RecommendationDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [article, setArticle] = useState<ArticleProps | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [imageError, setImageError] = useState(false);

  useEffect(() => {
    // Try to get the article from the location state first
    if (location.state?.article) {
      setArticle(location.state.article);
      return;
    }

    // If not in state, show error
    setError('Article not found');
  }, [id, location.state]);

  const handleImageError = () => {
    setImageError(true);
  };

  if (error || !article) {
    return (
      <div className='min-h-screen bg-gray-50 dark:bg-gray-900'>
        <Header />
        <main className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24'>
          <div className='text-center'>
            <h1 className='text-2xl font-bold text-gray-900 dark:text-white mb-4'>Error</h1>
            <p className='text-gray-600 dark:text-gray-400'>{error || 'Article not found'}</p>
            <button
              onClick={() => navigate('/recommendations')}
              className='mt-4 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700'
            >
              Back to Recommendations
            </button>
          </div>
        </main>
        <BottomNavBar />
      </div>
    );
  }

  return (
    <div className='min-h-screen bg-gray-50 dark:bg-gray-900'>
      <Header />
      <main className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24'>
        <div className='mb-6'>
          <button
            onClick={() => navigate('/recommendations')}
            className='flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors shadow-sm'
          >
            <svg className='w-5 h-5' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
              <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M10 19l-7-7m0 0l7-7m-7 7h18' />
            </svg>
            Back to Recommendations
          </button>
        </div>
        <article className='bg-white dark:bg-gray-800 rounded-lg shadow-md p-6'>
          {article.image_url && !imageError && (
            <div className='mb-6 w-full'>
              <img
                src={article.image_url}
                alt={article.title}
                className='w-full aspect-square object-cover rounded-lg'
                onError={handleImageError}
              />
            </div>
          )}
          <h1 className='text-3xl font-bold text-gray-900 dark:text-white mb-4'>{article.title}</h1>
          <div className='flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-6'>
            <span>{article.source}</span>
            <span>•</span>
            <span>{new Date(article.published_at).toLocaleDateString()}</span>
            <span>•</span>
            <span>{article.category}</span>
          </div>
          <div className='prose dark:prose-invert max-w-none'>
            <p className='text-gray-600 dark:text-gray-300 whitespace-pre-line'>{article.content}</p>
          </div>
          {article.url && (
            <div className='mt-6'>
              <a
                href={article.url}
                target='_blank'
                rel='noopener noreferrer'
                className='text-indigo-600 dark:text-indigo-400 hover:underline'
              >
                Read original article
              </a>
            </div>
          )}
        </article>
      </main>
      <BottomNavBar />
    </div>
  );
};

export default RecommendationDetail;
