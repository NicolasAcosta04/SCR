import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useUser } from '../contexts/UserContext';
import { LoginForm, TokenResponse } from '../interfaces/Interfaces';

const Login = () => {
  const navigate = useNavigate();
  const { setLoggedIn } = useAuth();
  const { setToken } = useUser();
  const [formData, setFormData] = useState<LoginForm>({
    username: '',
    password: '',
  });
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  // Log initial context state
  useEffect(() => {
    console.log('Login component mounted');
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    console.log('Starting login process...', { username: formData.username });

    try {
      // First, get the access token
      console.log('Requesting access token...');
      const tokenResponse = await fetch('http://localhost:8000/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username: formData.username,
          password: formData.password,
        }),
      });

      if (!tokenResponse.ok) {
        const errorData = await tokenResponse.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      const tokenData: TokenResponse = await tokenResponse.json();
      console.log('Token received:', {
        type: tokenData.token_type,
        token: tokenData.access_token,
      });

      // Store the token in context and localStorage
      console.log('Storing token in context and localStorage...');
      setToken(tokenData.access_token);

      // Update auth state
      console.log('Login successful! Updating auth state...');
      setLoggedIn(true);

      // Navigate to home page
      console.log('Redirecting to home...');
      navigate('/home');
    } catch (err) {
      console.error('Login error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className='min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8'>
      <div className='max-w-md w-full space-y-4 bg-white dark:bg-gray-800 p-8 rounded-lg shadow-md'>
        <div>
          <h2 className='mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-white'>Login</h2>
        </div>
        <form className='mt-8 space-y-6' onSubmit={handleSubmit}>
          <div className='rounded-md shadow-sm -space-y-px'>
            <div className='mt-4'>
              <label htmlFor='username' className='sr-only'>
                Username
              </label>
              <input
                id='username'
                name='username'
                type='text'
                required
                className='appearance-none rounded relative block w-full px-3 py-2 border border-gray-300 dark:border-gray-700 placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm dark:bg-gray-700'
                placeholder='Username'
                value={formData.username}
                onChange={handleInputChange}
                disabled={isLoading}
              />
            </div>
            <div className='mt-4'>
              <label htmlFor='password' className='sr-only'>
                Password
              </label>
              <input
                id='password'
                name='password'
                type='password'
                required
                className='appearance-none rounded relative block w-full px-3 py-2 border border-gray-300 dark:border-gray-700 placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm dark:bg-gray-700'
                placeholder='Password'
                value={formData.password}
                onChange={handleInputChange}
                disabled={isLoading}
              />
            </div>
          </div>

          {error && <div className='text-red-500 text-sm text-center'>{error}</div>}

          <div>
            <button
              type='submit'
              className='group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed'
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <svg
                    className='animate-spin -ml-1 mr-3 h-5 w-5 text-white'
                    xmlns='http://www.w3.org/2000/svg'
                    fill='none'
                    viewBox='0 0 24 24'
                  >
                    <circle
                      className='opacity-25'
                      cx='12'
                      cy='12'
                      r='10'
                      stroke='currentColor'
                      strokeWidth='4'
                    ></circle>
                    <path
                      className='opacity-75'
                      fill='currentColor'
                      d='M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z'
                    ></path>
                  </svg>
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </div>
        </form>

        <div className='mt-6 text-center'>
          <Link to='/forgot-password' className='text-sm text-indigo-600 hover:text-indigo-500 dark:text-indigo-400'>
            Forgot password?
          </Link>
        </div>

        <div className='mt-4 text-center'>
          <span className='text-sm text-gray-600 dark:text-gray-400'>Don't have an account? </span>
          <Link to='/signup' className='text-sm text-indigo-600 hover:text-indigo-500 dark:text-indigo-400'>
            Sign up
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Login;
