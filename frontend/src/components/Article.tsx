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
  onNavigate: () => void;
}

const Article = ({
  article_id,
  title,
  content,
  source,
  url,
  published_at,
  image_url,
  category,
  subcategory,
  confidence,
  onNavigate,
}: ArticleProps) => {
  const [isHovered, setIsHovered] = useState(false);
  const navigate = useNavigate();

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Date not available';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch (error) {
      return 'Invalid date';
    }
  };

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    onNavigate();
  };

  const handleIconClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent the article click from firing
    // Handle icon-specific actions here
  };

  return (
    <div
      className='bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden cursor-pointer transform transition-transform duration-200 hover:scale-[1.02]'
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleClick}
    >
      {image_url && (
        <div className='relative h-64 w-full overflow-hidden'>
          <img
            src={image_url}
            alt={title}
            className='w-full h-full object-cover transition-transform duration-200'
            style={{ transform: isHovered ? 'scale(1.05)' : 'scale(1)' }}
            onError={(e) => {
              e.currentTarget.src = 'https://via.placeholder.com/800x800?text=No+Image+Available';
            }}
          />
        </div>
      )}
      <div className='p-4'>
        <div className='flex items-center gap-2 mb-2'>
          <span className='px-2 py-1 text-xs font-semibold text-white bg-indigo-600 rounded-full'>{category}</span>
          {subcategory && (
            <span className='px-2 py-1 text-xs font-semibold text-indigo-600 bg-indigo-100 dark:bg-indigo-900 dark:text-indigo-200 rounded-full'>
              {subcategory}
            </span>
          )}
        </div>
        <h2 className='text-lg font-bold text-gray-900 dark:text-white mb-2'>{title}</h2>
        <p className='text-sm text-gray-600 dark:text-gray-300 mb-3 line-clamp-2'>{content}</p>
        <div className='flex items-center justify-between text-xs text-gray-500 dark:text-gray-400'>
          <span>{source}</span>
          <span>{formatDate(published_at)}</span>
        </div>
      </div>
      <div className='flex justify-end gap-2 p-2 border-t border-gray-100 dark:border-gray-700'>
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
