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

// Create an AuthContext to manage authentication state globally
import { createContext, useContext } from 'react';
import Profile from './pages/Profile';

interface AuthContextType {
  loggedIn: boolean;
  setLoggedIn: (value: boolean) => void;
}

export const AuthContext = createContext<AuthContextType>({
  loggedIn: false,
  setLoggedIn: () => {},
});

export const useAuth = () => useContext(AuthContext);

const App = () => {
  const [loggedIn, setLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);

  // Check for token on mount and verify it's valid
  useEffect(() => {
    const verifyToken = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/users/me', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          setLoggedIn(true);
        } else {
          // Token is invalid
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

  if (loading) {
    return (
      <div className='min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900'>
        <div className='text-xl text-gray-700 dark:text-gray-200'>Loading...</div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ loggedIn, setLoggedIn }}>
      <ThemeProvider>
        <UserProvider>
          <div className='min-h-screen bg-gray-50 dark:bg-gray-900'>
            <Router>
              <Routes>
                <Route path='/' element={!loggedIn ? <Login /> : <Navigate replace to='/home' />} />
                <Route path='/signup' element={!loggedIn ? <SignUp /> : <Navigate replace to='/home' />} />
                <Route path='/home' element={loggedIn ? <Home /> : <Navigate replace to='/' />} />
                <Route path='/article/:id' element={loggedIn ? <ArticleDetail /> : <Navigate replace to='/' />} />
                <Route path='/profile' element={loggedIn ? <Profile /> : <Navigate replace to='/' />} />
                <Route path='/settings' element={loggedIn ? <div>Settings</div> : <Navigate replace to='/' />} />
                <Route path='/forgot-password' element={<ForgotPassword />} />
                <Route path='/reset-password' element={<ResetPassword />} />
              </Routes>
            </Router>
          </div>
        </UserProvider>
      </ThemeProvider>
    </AuthContext.Provider>
  );
};

export default App;
