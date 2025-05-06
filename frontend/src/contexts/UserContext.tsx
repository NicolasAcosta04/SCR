/**
 * UserContext Module
 * Manages user state, authentication, and preferences across the application.
 * Provides a centralized way to handle user data, article history, and preferences.
 */

import { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { ArticleProps, UserContextType, UserDetails, UserPreferences } from '../interfaces/Interfaces';

// Create the context with undefined as initial value
const UserContext = createContext<UserContextType | undefined>(undefined);

/**
 * UserProvider Component
 * Manages user state and provides it to the application through context
 */
export const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { loggedIn } = useAuth();

  // State management for user data
  const [userId, setUserId] = useState<number | null>(null);
  const [token, setToken] = useState<string | null>(() => {
    console.log('Loading token from localStorage...');
    const storedToken = localStorage.getItem('token');
    console.log('Token loaded:', storedToken ? 'Token exists' : 'No token found');
    return storedToken;
  });

  // Initialize user details from localStorage if available
  const [userDetails, setUserDetails] = useState<UserDetails | null>(() => {
    console.log('Loading user details from localStorage...');
    const storedDetails = localStorage.getItem('userDetails');
    if (storedDetails) {
      console.log('User details loaded from localStorage');
      return JSON.parse(storedDetails);
    }
    console.log('No user details found in localStorage');
    return null;
  });

  // State for articles and user preferences
  const [articles, setArticles] = useState<ArticleProps[]>([]);
  const [preferences, setPreferences] = useState<UserPreferences>({
    categories: {},
    read_articles: new Set(),
  });

  // Load persisted data from localStorage on component mount
  useEffect(() => {
    console.log('Loading user data from localStorage...');
    const storedArticles = localStorage.getItem('articles');
    const storedPreferences = localStorage.getItem('preferences');

    if (storedArticles) {
      console.log('Found stored articles:', JSON.parse(storedArticles).length);
      setArticles(JSON.parse(storedArticles));
    }
    if (storedPreferences) {
      console.log('Found stored preferences');
      const parsedPrefs = JSON.parse(storedPreferences);
      setPreferences({
        ...parsedPrefs,
        read_articles: new Set(parsedPrefs.read_articles),
      });
    }
  }, []);

  // Fetch user details when token changes or user logs in
  useEffect(() => {
    if (token && loggedIn) {
      console.log('Token changed and user is logged in, fetching user details...');
      fetchUserDetails().catch((error) => {
        console.error('Failed to fetch user details after token change:', error);
      });
    }
  }, [token, loggedIn]);

  // Persist user data to localStorage when it changes
  useEffect(() => {
    console.log('Saving user data to localStorage...');
    if (token) {
      console.log('Saving token:', token.substring(0, 10) + '...');
      localStorage.setItem('token', token);
    } else {
      console.log('Removing token from localStorage');
      localStorage.removeItem('token');
    }
    if (userDetails) {
      console.log('Saving user details to localStorage:', userDetails);
      localStorage.setItem('userDetails', JSON.stringify(userDetails));
      localStorage.setItem('userId', userDetails.id.toString());
    } else {
      console.log('Removing user details from localStorage');
      localStorage.removeItem('userDetails');
      localStorage.removeItem('userId');
    }
    localStorage.setItem('articles', JSON.stringify(articles));
    localStorage.setItem(
      'preferences',
      JSON.stringify({
        ...preferences,
        read_articles: Array.from(preferences.read_articles),
      })
    );
  }, [token, userDetails, articles, preferences]);

  // Clear user data when logged out
  useEffect(() => {
    if (!loggedIn) {
      console.log('User logged out, clearing data...');
      clearUserData();
    }
  }, [loggedIn]);

  /**
   * Fetches user details from the authentication API
   * @throws Error if no token is available or if the request fails
   */
  const fetchUserDetails = async () => {
    console.log('Fetching user details...');
    if (!token) {
      console.error('No token available to fetch user details');
      throw new Error('No token available');
    }

    try {
      console.log('Making request to /users/me endpoint...');
      const response = await fetch('http://localhost:8000/users/me', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        console.error('Failed to fetch user details:', response.status);
        throw new Error('Failed to fetch user details');
      }

      const data = await response.json();
      console.log('User details received:', data);
      setUserDetails(data);
      setUserId(data.id);
    } catch (error) {
      console.error('Error fetching user details:', error);
      throw error;
    }
  };

  /**
   * Updates user preferences in both backend and local state
   * @param newPreferences Array of category preferences
   * @throws Error if update fails
   */
  const updateUserPreferences = async (newPreferences: string[]): Promise<void> => {
    if (!token || !userDetails) return;

    try {
      // Update preferences in the backend
      const response = await fetch('http://localhost:8000/users/me/preferences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          categories: newPreferences,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update preferences');
      }

      // Update local state
      setUserDetails((prev) => (prev ? { ...prev, preferences: newPreferences } : null));

      // Save to localStorage
      const updatedUserDetails = { ...userDetails, preferences: newPreferences };
      localStorage.setItem('userDetails', JSON.stringify(updatedUserDetails));
    } catch (error) {
      console.error('Error updating preferences:', error);
      throw error;
    }
  };

  /**
   * Adds a new article to the user's article history if not already present
   * @param article The article to add
   */
  const addArticle = (article: ArticleProps) => {
    setArticles((prev) => {
      // Check if article already exists
      if (prev.some((a) => a.article_id === article.article_id)) {
        return prev;
      }
      return [...prev, article];
    });
  };

  /**
   * Updates user preferences based on article interaction
   * @param category Article category
   * @param confidence Confidence score of the category
   * @param articleId ID of the article being read
   */
  const updatePreferences = (category: string, confidence: number, articleId: string) => {
    setPreferences((prev) => {
      const newPreferences = { ...prev };

      // Update category preferences
      if (!newPreferences.categories[category]) {
        newPreferences.categories[category] = {
          count: 0,
          total_confidence: 0,
          last_interaction: new Date().toISOString(),
        };
      }

      newPreferences.categories[category].count += 1;
      newPreferences.categories[category].total_confidence += confidence;
      newPreferences.categories[category].last_interaction = new Date().toISOString();

      // Add article to read articles
      newPreferences.read_articles.add(articleId);

      return newPreferences;
    });
  };

  /**
   * Clears all user data from state and localStorage
   */
  const clearUserData = () => {
    console.log('Clearing all user data...');
    setUserId(null);
    setToken(null);
    setUserDetails(null);
    setArticles([]);
    setPreferences({
      categories: {},
      read_articles: new Set(),
    });
    localStorage.removeItem('userId');
    localStorage.removeItem('token');
    localStorage.removeItem('userDetails');
    localStorage.removeItem('articles');
    localStorage.removeItem('preferences');
  };

  // Context value object
  const value = {
    userId,
    token,
    userDetails,
    articles,
    preferences,
    setUserId,
    setToken,
    setUserDetails,
    fetchUserDetails,
    addArticle,
    updatePreferences,
    clearUserData,
    updateUserPreferences,
  };

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
};

/**
 * Custom hook to use the UserContext
 * @throws Error if used outside of UserProvider
 */
export const useUser = () => {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};
