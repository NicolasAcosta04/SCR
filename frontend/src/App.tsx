/**
 * Main application component for the news recommendation system.
 * Handles routing, authentication, and theme management.
 */

import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { UserProvider } from './contexts/UserContext';
import Home from './pages/Home';
import Login from './pages/Login';
import SignUp from './pages/SignUp';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import ArticleDetail from './pages/ArticleDetail';
import Recommendations from './pages/Recommendations';

// Create an AuthContext to manage authentication state globally
import { createContext, useContext } from 'react';
import Profile from './pages/Profile';
import RecommendationDetail from './pages/RecommendationDetail';

/**
 * Interface defining the shape of the authentication context
 * @property {boolean} loggedIn - Current authentication state
 * @property {function} setLoggedIn - Function to update authentication state
 */
interface AuthContextType {
  loggedIn: boolean;
  setLoggedIn: (value: boolean) => void;
}

// Create and export the authentication context with default values
export const AuthContext = createContext<AuthContextType>({
  loggedIn: false,
  setLoggedIn: () => {},
});

// Custom hook to easily access the auth context
export const useAuth = () => useContext(AuthContext);

/**
 * Root application component that sets up routing and authentication
 * @returns {JSX.Element} The rendered application
 */
const App = () => {
  // State for managing authentication and loading status
  const [loggedIn, setLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);

  /**
   * Effect hook to verify authentication token on component mount
   * Checks if a valid token exists in localStorage and verifies it with the backend
   */
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

  /**
   * Main application render with routing setup
   * Routes are protected based on authentication status
   */
  return (
    <AuthContext.Provider value={{ loggedIn, setLoggedIn }}>
      <ThemeProvider>
        <UserProvider>
          <div className='min-h-screen bg-gray-50 dark:bg-gray-900'>
            <Router>
              <Routes>
                {/* Public routes */}
                <Route path='/' element={!loggedIn ? <Login /> : <Navigate replace to='/home' />} />
                <Route path='/signup' element={!loggedIn ? <SignUp /> : <Navigate replace to='/home' />} />
                <Route path='/forgot-password' element={<ForgotPassword />} />
                <Route path='/reset-password' element={<ResetPassword />} />

                {/* Protected routes - require authentication */}
                <Route path='/home' element={loggedIn ? <Home /> : <Navigate replace to='/' />} />
                <Route path='/article/:id' element={loggedIn ? <ArticleDetail /> : <Navigate replace to='/' />} />
                <Route path='/profile' element={loggedIn ? <Profile /> : <Navigate replace to='/' />} />
                <Route path='/recommendations' element={loggedIn ? <Recommendations /> : <Navigate replace to='/' />} />
                <Route
                  path='/recommendations/:id'
                  element={loggedIn ? <RecommendationDetail /> : <Navigate replace to='/' />}
                />
                <Route path='/settings' element={loggedIn ? <div>Settings</div> : <Navigate replace to='/' />} />
              </Routes>
            </Router>
          </div>
        </UserProvider>
      </ThemeProvider>
    </AuthContext.Provider>
  );
};

export default App;
