import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../App';
import { useUser } from '../contexts/UserContext';

const SignUp = () => {
  const navigate = useNavigate();
  const { setLoggedIn } = useAuth();
  const { setUserId, setToken } = useUser();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [passwordMatch, setPasswordMatch] = useState<boolean | null>(null);

  useEffect(() => {
    if (formData.password && formData.confirmPassword) {
      setPasswordMatch(formData.password === formData.confirmPassword);
    } else {
      setPasswordMatch(null);
    }
  }, [formData.password, formData.confirmPassword]);

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
    console.log('Starting registration process...', { username: formData.username, email: formData.email });

    // Validate form
    if (formData.password !== formData.confirmPassword) {
      console.error('Password validation failed: Passwords do not match');
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 8) {
      console.error('Password validation failed: Password too short');
      setError('Password must be at least 8 characters long');
      return;
    }

    if (!formData.email.includes('@')) {
      console.error('Email validation failed: Invalid email format');
      setError('Please enter a valid email address');
      return;
    }

    setIsLoading(true);
    console.log('Form validation passed, proceeding with registration...');

    try {
      // First, register the user
      console.log('Sending registration request...');
      const registerResponse = await fetch('http://localhost:8000/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: formData.username,
          email: formData.email,
          password: formData.password,
        }),
      });

      const registerData = await registerResponse.json();
      console.log('Registration response:', { status: registerResponse.status, data: registerData });

      if (!registerResponse.ok) {
        throw new Error(registerData.detail || 'Registration failed');
      }

      // Then, get the access token
      console.log('Getting access token...');
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

      const tokenData = await tokenResponse.json();
      console.log('Token response:', { status: tokenResponse.status, hasToken: !!tokenData.access_token });

      if (!tokenResponse.ok) {
        throw new Error(tokenData.detail || 'Login failed');
      }

      // Finally, get the user data
      console.log('Fetching user data...');
      const userResponse = await fetch('http://localhost:8000/users/me', {
        headers: {
          Authorization: `Bearer ${tokenData.access_token}`,
        },
      });

      const userData = await userResponse.json();
      console.log('User data response:', { status: userResponse.status, userId: userData.id });

      if (!userResponse.ok) {
        throw new Error('Failed to fetch user data');
      }

      // Store the data in context
      console.log('Storing user data in context...');
      setToken(tokenData.access_token);
      setUserId(userData.id);
      setLoggedIn(true);

      console.log('Registration successful! Redirecting to home...');
      // Navigate to home page
      navigate('/home');
    } catch (err) {
      console.error('Registration error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred during registration');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className='min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8'>
      <div className='max-w-md w-full space-y-8 bg-white dark:bg-gray-800 p-8 rounded-lg shadow-md'>
        <div>
          <h2 className='mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-white'>Create an Account</h2>
          <p className='mt-2 text-center text-sm text-gray-600 dark:text-gray-400'>
            Already have an account?{' '}
            <Link to='/' className='font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400'>
              Sign in
            </Link>
          </p>
        </div>
        <form className='mt-8 space-y-6' onSubmit={handleSubmit}>
          <div className='rounded-md shadow-sm -space-y-px'>
            <div>
              <label htmlFor='username' className='sr-only'>
                Username
              </label>
              <input
                id='username'
                name='username'
                type='text'
                required
                className='appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 dark:border-gray-700 placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm dark:bg-gray-700'
                placeholder='Username'
                value={formData.username}
                onChange={handleInputChange}
                disabled={isLoading}
              />
            </div>
            <div>
              <label htmlFor='email' className='sr-only'>
                Email
              </label>
              <input
                id='email'
                name='email'
                type='email'
                required
                className='appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 dark:border-gray-700 placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm dark:bg-gray-700'
                placeholder='Email'
                value={formData.email}
                onChange={handleInputChange}
                disabled={isLoading}
              />
            </div>
            <div>
              <label htmlFor='password' className='sr-only'>
                Password
              </label>
              <input
                id='password'
                name='password'
                type='password'
                required
                className={`appearance-none rounded-none relative block w-full px-3 py-2 border ${
                  passwordMatch === false
                    ? 'border-red-500 dark:border-red-500'
                    : 'border-gray-300 dark:border-gray-700'
                } placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm dark:bg-gray-700`}
                placeholder='Password'
                value={formData.password}
                onChange={handleInputChange}
                minLength={8}
                disabled={isLoading}
              />
            </div>
            <div>
              <label htmlFor='confirm-password' className='sr-only'>
                Confirm Password
              </label>
              <input
                id='confirm-password'
                name='confirmPassword'
                type='password'
                required
                className={`appearance-none rounded-none relative block w-full px-3 py-2 border ${
                  passwordMatch === false
                    ? 'border-red-500 dark:border-red-500'
                    : 'border-gray-300 dark:border-gray-700'
                } placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm dark:bg-gray-700`}
                placeholder='Confirm Password'
                value={formData.confirmPassword}
                onChange={handleInputChange}
                minLength={8}
                disabled={isLoading}
              />
            </div>
          </div>

          {passwordMatch === false && <div className='text-red-500 text-sm text-center'>Passwords do not match</div>}
          {passwordMatch === true && <div className='text-green-500 text-sm text-center'>Passwords match</div>}

          {error && <div className='text-red-500 text-sm text-center'>{error}</div>}

          <div>
            <button
              type='submit'
              disabled={isLoading || passwordMatch === false}
              className='group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed'
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
                  Creating Account...
                </>
              ) : (
                'Sign Up'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SignUp;
