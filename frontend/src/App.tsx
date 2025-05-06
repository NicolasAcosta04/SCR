/**
 * Main application component for the news recommendation system.
 * Handles routing, authentication, and theme management.
 */
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
import Profile from './pages/Profile';
import RecommendationDetail from './pages/RecommendationDetail';
import { useAuth } from './contexts/AuthContext';
import { JSX } from 'react';

/**
 * Root application component that sets up routing and authentication
 * @returns {JSX.Element} The rendered application
 */
const App = (): JSX.Element => {
  const { loggedIn } = useAuth();

  /**
   * Main application render with routing setup
   * Routes are protected based on authentication status
   */
  return (
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
  );
};

export default App;
