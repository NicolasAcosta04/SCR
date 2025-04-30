import { FC, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface ArticleProps {
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

const Article: FC<ArticleProps> = (article) => {
  const navigate = useNavigate();
  const [imageError, setImageError] = useState(false);

  const handleArticleClick = () => {
    navigate(`/article/${article.article_id}`, { state: { article } });
  };

  const handleIconClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent the article click from firing
    // Handle icon-specific actions here
  };

  const handleImageError = () => {
    setImageError(true);
  };

  return (
    <div
      className='bg-gray-100 dark:bg-gray-800 rounded-lg p-4 mb-4 cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors'
      onClick={handleArticleClick}
    >
      <div className='flex gap-4'>
        {article.image_url && !imageError ? (
          <div className='w-36 h-36 bg-gray-200 dark:bg-gray-700 rounded-lg overflow-hidden'>
            <img
              src={article.image_url}
              alt={article.title}
              className='w-full h-full object-cover'
              onError={handleImageError}
            />
          </div>
        ) : (
          <div className='w-36 h-36 bg-gray-200 dark:bg-gray-700 rounded-lg flex items-center justify-center'>
            <div className='w-16 h-16 border-2 border-gray-300 dark:border-gray-600 rounded-lg flex items-center justify-center'>
              <svg className='w-8 h-8 text-gray-400' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                <path
                  strokeLinecap='round'
                  strokeLinejoin='round'
                  strokeWidth={2}
                  d='M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z'
                />
              </svg>
            </div>
          </div>
        )}
        <div className='flex-1'>
          <div className='flex items-center gap-2 mb-2'>
            <h2 className='text-xl font-bold text-gray-900 dark:text-white'>{article.title}</h2>
            <span className='text-sm text-gray-500 dark:text-gray-400'>
              • {new Date(article.published_at).toLocaleDateString()}
            </span>
          </div>
          <p className='text-gray-600 dark:text-gray-300 line-clamp-2'>{article.content}</p>
          <div className='flex items-center gap-2 mt-2'>
            <p className='text-sm text-gray-500 dark:text-gray-400'>{article.source}</p>
            <span>•</span>
            <p className='text-sm text-gray-500 dark:text-gray-400'>{article.category}</p>
          </div>
        </div>
      </div>
      <div className='flex justify-end gap-2 mt-4'>
        <button className='p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full' onClick={handleIconClick}>
          <svg
            className='w-5 h-5 text-gray-600 dark:text-gray-400'
            fill='none'
            stroke='currentColor'
            viewBox='0 0 24 24'
          >
            <path
              strokeLinecap='round'
              strokeLinejoin='round'
              strokeWidth={2}
              d='M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z'
            />
          </svg>
        </button>
        <button className='p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full' onClick={handleIconClick}>
          <svg className='w-5 h-5 text-green-600' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
            <path
              strokeLinecap='round'
              strokeLinejoin='round'
              strokeWidth={2}
              d='M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5'
            />
          </svg>
        </button>
        <button className='p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full' onClick={handleIconClick}>
          <svg className='w-5 h-5 text-red-600' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
            <path
              strokeLinecap='round'
              strokeLinejoin='round'
              strokeWidth={2}
              d='M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.017c-.163 0-.326-.02-.485-.06L17 4m-7 10v5a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L17 13V4m-7 10h2M17 4h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5'
            />
          </svg>
        </button>
        <button className='p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full' onClick={handleIconClick}>
          <svg
            className='w-5 h-5 text-gray-600 dark:text-gray-400'
            fill='none'
            stroke='currentColor'
            viewBox='0 0 24 24'
          >
            <path
              strokeLinecap='round'
              strokeLinejoin='round'
              strokeWidth={2}
              d='M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z'
            />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default Article;
