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

  const handleExternalLink = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent the article click from firing
    window.open(url, '_blank', 'noopener,noreferrer');
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
        <button
          className='relative p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full group'
          onClick={handleExternalLink}
        >
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
              d='M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14'
            />
          </svg>
          <span className='absolute left-1/2 -translate-x-1/2 bottom-full mb-2 px-2 py-1 rounded bg-gray-800 text-white text-xs opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-20'>
            Read the original article
          </span>
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
