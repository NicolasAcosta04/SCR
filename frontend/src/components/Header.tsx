import { useTheme } from '../contexts/ThemeContext';
import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Header = () => {
  const { theme, toggleTheme } = useTheme();
  const [isAnimating, setIsAnimating] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { setLoggedIn } = useAuth();

  // Function to get page title based on current path
  const getPageTitle = () => {
    const path = location.pathname;
    switch (path) {
      case '/':
        return 'Sign In';
      case '/signup':
        return 'Sign Up';
      case '/home':
        return 'Home';
      case '/recommendations':
        return 'Recommendations';
      case '/profile':
        return 'Profile';
      case '/forgot-password':
        return 'Forgot Password';
      default:
        return 'SCR';
    }
  };

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const menu = document.getElementById('slide-menu');
      const button = document.getElementById('menu-button');
      if (menu && button && !menu.contains(event.target as Node) && !button.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleThemeToggle = () => {
    setIsAnimating(true);
    toggleTheme();
    setTimeout(() => setIsAnimating((prev) => !prev), 500);
  };

  const handleSignOut = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      setLoggedIn(false);
      navigate('/');
      return;
    }

    try {
      await fetch('http://localhost:8000/logout', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('token');
      setLoggedIn(false);
      navigate('/');
    }
  };

  return (
    <>
      <header className='fixed top-0 w-full z-10 bg-white dark:bg-gray-800 shadow'>
        <div className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between'>
          <div className='flex items-center'>
            <div className='w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center'>
              <svg className='w-6 h-6 text-gray-400' fill='currentColor' viewBox='0 0 24 24'>
                <path d='M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5' />
              </svg>
            </div>
            <h1 className='ml-4 text-2xl font-bold text-gray-900 dark:text-white'>{getPageTitle()}</h1>
          </div>
          <div className='flex items-center space-x-4'>
            <button
              onClick={handleThemeToggle}
              className='p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-all duration-300'
            >
              <div className={`relative w-6 h-6 ${isAnimating ? 'animate-[spin_0.5s_linear]' : ''}`}>
                {theme === 'dark' ? (
                  <svg className='w-6 h-6' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                    <path
                      strokeLinecap='round'
                      strokeLinejoin='round'
                      strokeWidth={2}
                      d='M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z'
                    />
                  </svg>
                ) : (
                  <svg className='w-6 h-6' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                    <path
                      strokeLinecap='round'
                      strokeLinejoin='round'
                      strokeWidth={2}
                      d='M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z'
                    />
                  </svg>
                )}
              </div>
            </button>
            <button
              id='menu-button'
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className='p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full'
            >
              <svg className='w-6 h-6' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 6h16M4 12h16M4 18h16' />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* Slide-out Menu */}
      <div
        id='slide-menu'
        className={`fixed top-0 right-0 h-full w-64 sm:w-80 bg-white dark:bg-gray-800 shadow-lg transform transition-transform duration-200 ease-in-out z-20 ${
          isMenuOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className='pt-4 pr-4 pl-4 pb-2 flex items-center justify-between'>
          <h2 className='text-lg font-semibold text-gray-900 dark:text-white'>Menu</h2>
          <button
            onClick={() => setIsMenuOpen(false)}
            className='p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full'
            aria-label='Close menu'
          >
            <svg className='w-6 h-6' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
              <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M6 18L18 6M6 6l12 12' />
            </svg>
          </button>
        </div>

        <div className='border-t border-gray-200 dark:border-gray-700 my-2'></div>

        <nav className=''>
          <button
            className='w-full flex items-center text-left px-4 py-3 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors duration-200'
            onClick={() => {
              setIsMenuOpen(false);
              navigate('/profile');
            }}
          >
            <svg className='w-6 h-6 mr-2' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
              <path
                strokeLinecap='round'
                strokeLinejoin='round'
                strokeWidth={2}
                d='M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z'
              />
            </svg>
            Profile
          </button>
          <button
            className='w-full flex items-center text-left px-4 py-3 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors duration-200'
            onClick={() => {
              setIsMenuOpen(false);
              // Add navigation to settings page here
            }}
          >
            <svg className='w-6 h-6 mr-2' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
              <path
                strokeLinecap='round'
                strokeLinejoin='round'
                strokeWidth={2}
                d='M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z'
              />
              <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M15 12a3 3 0 11-6 0 3 3 0 016 0z' />
            </svg>
            Settings
          </button>
          <button
            onClick={handleSignOut}
            className='w-full flex items-center text-left px-4 py-3 text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors duration-200'
          >
            <svg className='w-6 h-6 mr-2' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
              <path
                strokeLinecap='round'
                strokeLinejoin='round'
                strokeWidth={2}
                d='M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1'
              />
            </svg>
            Sign Out
          </button>
        </nav>
      </div>

      {/* Blur Overlay */}
      {isMenuOpen && (
        <div
          // className='fixed inset-0 backdrop-blur-xs bg-white/30 dark:bg-black/30 z-10'
          className='fixed inset-0 bg-white/60 dark:bg-black/60 z-10'
          onClick={() => setIsMenuOpen(false)}
        ></div>
      )}
    </>
  );
};

export default Header;
