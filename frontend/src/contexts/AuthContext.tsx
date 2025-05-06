/**
 * Authentication context for managing user login state across the application
 * Provides a way to access and update authentication state from any component
 */

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { AuthContextType } from '../interfaces/Interfaces';

// Create the authentication context with default values
const AuthContext = createContext<AuthContextType>({
  loggedIn: false,
  setLoggedIn: () => {},
});

/**
 * Custom hook to easily access the auth context
 * @returns {AuthContextType} The authentication context
 */
export const useAuth = (): AuthContextType => useContext(AuthContext);

/**
 * Props interface for the AuthProvider component
 */
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Provider component that wraps the application and provides authentication context
 * @param {AuthProviderProps} props - Component props
 * @returns {JSX.Element} The provider component
 */
export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [loggedIn, setLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const verifyToken = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        // Verify token with backend
        const response = await fetch('http://localhost:8000/users/me', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          setLoggedIn(true);
        } else {
          // Token is invalid, remove it from storage
          localStorage.removeItem('token');
        }
      } catch (error) {
        console.error('Token verification failed:', error);
        localStorage.removeItem('token');
      }
      setLoading(false);
    };

    verifyToken();
  }, []);

  // Show loading state while verifying authentication
  if (loading) {
    return (
      <div className='min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900'>
        <div className='text-xl text-gray-700 dark:text-gray-200'>Loading...</div>
      </div>
    );
  }

  return <AuthContext.Provider value={{ loggedIn, setLoggedIn }}>{children}</AuthContext.Provider>;
};
