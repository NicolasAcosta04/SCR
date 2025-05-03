import { useState, useEffect, useRef } from 'react';
import { useUser } from '../contexts/UserContext';
import Header from '../components/Header';
import BottomNavBar from '../components/BottomNavBar';

interface Category {
  value: string;
  label: string;
}

const CATEGORIES: Category[] = [
  { value: 'tech', label: 'Technology' },
  { value: 'politics', label: 'Politics' },
  { value: 'entertainment', label: 'Entertainment' },
  { value: 'business', label: 'Business' },
  { value: 'sport', label: 'Sports' },
];

const Profile = () => {
  const { token, userDetails, fetchUserDetails, updateUserPreferences } = useUser();
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [currentPreferences, setCurrentPreferences] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const barRef = useRef<HTMLDivElement>(null);

  // Fetch user preferences on mount
  useEffect(() => {
    const fetchPreferences = async () => {
      if (!token) return;
      try {
        const response = await fetch('http://localhost:8000/users/me/preferences', {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) throw new Error('Failed to fetch preferences');
        const data = await response.json();
        setCurrentPreferences(data.preferences || []);
      } catch (err) {
        console.error('Error fetching preferences:', err);
        setError('Failed to load preferences');
      }
    };
    fetchPreferences();
  }, [token]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (barRef.current && !barRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    if (dropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    } else {
      document.removeEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [dropdownOpen]);

  const addCategory = (category: string) => {
    if (selectedCategories.length >= 5) {
      setError('Maximum of 5 categories allowed');
      return;
    }
    setSelectedCategories([...selectedCategories, category]);
    setError(null);
    setDropdownOpen(false);
  };

  const removeCategory = (category: string) => {
    setSelectedCategories(selectedCategories.filter((c) => c !== category));
    setError(null);
  };

  const handleBarClick = () => {
    if (!isLoading && selectedCategories.length < 5) {
      setDropdownOpen((open) => !open);
    }
  };

  const handleSubmitPreferences = async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    setSuccess(null);
    try {
      // Merge current and new selections, remove duplicates, and limit to 5
      const merged = Array.from(new Set([...currentPreferences, ...selectedCategories])).slice(0, 5);
      if (merged.length > 5) {
        setError('Maximum of 5 categories allowed');
        return;
      }
      await updateUserPreferences(merged);
      setCurrentPreferences(merged);
      setSuccess('Preferences updated successfully');
      setSelectedCategories([]); // Clear the select bar after saving
      await fetchUserDetails();
    } catch (err) {
      console.error('Error updating preferences:', err);
      setError(err instanceof Error ? err.message : 'Failed to update preferences');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemovePreference = async (categoryToRemove: string) => {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const updatedPreferences = currentPreferences.filter((cat) => cat !== categoryToRemove);
      await updateUserPreferences(updatedPreferences);
      setCurrentPreferences(updatedPreferences);
      setSuccess('Preference removed successfully');
      await fetchUserDetails();
    } catch (err) {
      console.error('Error removing preference:', err);
      setError(err instanceof Error ? err.message : 'Failed to remove preference');
    } finally {
      setIsLoading(false);
    }
  };

  // Only show categories not already in preferences or currently selected
  const availableCategories = CATEGORIES.filter(
    (cat) => !currentPreferences.includes(cat.value) && !selectedCategories.includes(cat.value)
  );

  return (
    <div className='min-h-screen bg-gray-50 dark:bg-gray-900'>
      <Header />
      <main className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24'>
        <div className='max-w-3xl mx-auto'>
          <div className='bg-white dark:bg-gray-800 shadow rounded-lg p-6'>
            <h2 className='text-2xl font-bold text-gray-900 dark:text-white mb-6'>Hello, {userDetails?.username}!</h2>
            {/* User Info */}
            <div className='mb-8'>
              <h3 className='text-lg font-medium text-gray-900 dark:text-white mb-2'>User Information</h3>
              {/* <p className='text-gray-600 dark:text-gray-400'>Username: {userDetails?.username}</p> */}
            </div>
            {/* Category Selection Bar as unified input */}
            <div className='mb-8'>
              <h3 className='text-lg font-medium text-gray-900 dark:text-white mb-4'>Select Categories</h3>
              <p className='text-sm text-gray-500 dark:text-gray-400 mb-4'>
                Choose up to 5 categories you're interested in.
              </p>
              {error && (
                <div className='mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg'>
                  <p className='text-red-600 dark:text-red-400'>{error}</p>
                </div>
              )}
              {success && (
                <div className='mb-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg'>
                  <p className='text-green-600 dark:text-green-400'>{success}</p>
                </div>
              )}
              <div
                ref={barRef}
                className='flex items-center w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg px-2 py-2 min-h-[48px] cursor-pointer relative shadow focus-within:ring-2 focus-within:ring-indigo-500 mb-4'
                onClick={handleBarClick}
                tabIndex={0}
                style={{ minHeight: 48 }}
              >
                {/* Pills for selected categories */}
                <div className='flex flex-wrap gap-2 flex-1'>
                  {selectedCategories.length === 0 && (
                    <span className='text-gray-400 dark:text-gray-500 pl-2'>Select categories...</span>
                  )}
                  {selectedCategories.map((catValue) => {
                    const cat = CATEGORIES.find((c) => c.value === catValue);
                    return (
                      <div
                        key={catValue}
                        className='flex items-center px-3 py-1 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white shadow whitespace-nowrap'
                      >
                        <span>{cat?.label}</span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            removeCategory(catValue);
                          }}
                          disabled={isLoading}
                          className='ml-2 text-gray-500 hover:text-red-500 focus:outline-none rounded-full w-5 h-5 flex items-center justify-center text-xl'
                        >
                          ×
                        </button>
                      </div>
                    );
                  })}
                </div>
                {/* Dropdown arrow */}
                <div className='flex items-center ml-2'>
                  <button
                    type='button'
                    tabIndex={-1}
                    onClick={(e) => {
                      e.stopPropagation();
                      setDropdownOpen(!dropdownOpen);
                    }}
                    disabled={isLoading || availableCategories.length === 0 || selectedCategories.length >= 5}
                    className='flex items-center justify-center w-8 h-8 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed'
                  >
                    <svg className='w-5 h-5' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                      <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7' />
                    </svg>
                  </button>
                </div>
                {/* Dropdown menu */}
                {dropdownOpen && availableCategories.length > 0 && (
                  <div className='absolute left-0 top-full mt-2 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-10'>
                    {availableCategories.map((cat) => (
                      <button
                        key={cat.value}
                        onClick={(e) => {
                          e.stopPropagation();
                          addCategory(cat.value);
                        }}
                        className='block w-full text-left px-4 py-2 hover:bg-indigo-100 dark:hover:bg-indigo-700 text-gray-900 dark:text-white'
                        disabled={isLoading}
                      >
                        {cat.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {/* <p className='text-sm text-gray-500 dark:text-gray-400 mb-2'>
                {selectedCategories.length}/5 categories selected
              </p> */}
              <button
                onClick={handleSubmitPreferences}
                disabled={isLoading || selectedCategories.length === 0}
                className='w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed'
              >
                {isLoading ? 'Saving...' : 'Save Preferences'}
              </button>
            </div>
            {/* Current Preferences */}
            <div>
              <h3 className='text-lg font-medium text-gray-900 dark:text-white mb-4'>Your Preferences</h3>
              {currentPreferences.length === 0 ? (
                <p className='text-gray-500 dark:text-gray-400'>No preferences selected yet.</p>
              ) : (
                <div className='flex flex-wrap gap-2'>
                  {currentPreferences.map((pref) => {
                    const category = CATEGORIES.find((c) => c.value === pref);
                    return (
                      <div
                        key={pref}
                        className='flex items-center px-4 py-2 rounded-full bg-indigo-100 dark:bg-indigo-700 text-indigo-800 dark:text-white shadow whitespace-nowrap'
                      >
                        <span>{category?.label}</span>
                        <button
                          onClick={() => handleRemovePreference(pref)}
                          disabled={isLoading}
                          className='ml-2 text-red-600 hover:text-red-700 dark:text-red-300 dark:hover:text-red-400 focus:outline-none rounded-full w-5 h-5 flex items-center justify-center text-xl'
                        >
                          ×
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
      <BottomNavBar />
    </div>
  );
};

export default Profile;
