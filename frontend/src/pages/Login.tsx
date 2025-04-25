import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
// import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from '../App';

interface LoginForm {
  username: string;
  password: string;
}

const Login = () => {
  const navigate = useNavigate();
  const { setLoggedIn } = useAuth();
  const [formData, setFormData] = useState<LoginForm>({
    username: '',
    password: '',
  });
  const [error, setError] = useState<string>('');

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

    try {
      const response = await fetch('http://localhost:8000/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username: formData.username,
          password: formData.password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
      }

      localStorage.setItem('token', data.access_token);
      setLoggedIn(true);
      navigate('/home');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  // const handleGoogleSuccess = async (credentialResponse: any) => {
  //   try {
  //     const response = await fetch('http://localhost:8000/login/google', {
  //       method: 'POST',
  //       headers: {
  //         'Content-Type': 'application/json',
  //       },
  //       body: JSON.stringify({ token: credentialResponse.credential }),
  //     });

  //     const data = await response.json();

  //     if (!response.ok) {
  //       throw new Error(data.detail || 'Google login failed');
  //     }

  //     localStorage.setItem('token', data.access_token);
  //     setLoggedIn(true);
  //     navigate('/home');
  //   } catch (err) {
  //     setError(err instanceof Error ? err.message : 'An error occurred');
  //   }
  // };

  // const handleAppleLogin = async () => {
  //   // Apple Sign In implementation will go here
  //   setError('Apple Sign In not implemented yet');
  // };

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
              />
            </div>
          </div>

          {error && <div className='text-red-500 text-sm text-center'>{error}</div>}

          <div>
            <button
              type='submit'
              className='group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500'
            >
              Sign In
            </button>
          </div>
        </form>

        {/* <div className='mt-6'>
          <div className='relative'>
            <div className='absolute inset-0 flex items-center'>
              <div className='w-full border-t border-gray-300 dark:border-gray-700'></div>
            </div>
            <div className='relative flex justify-center text-sm'>
              <span className='px-2 bg-white dark:bg-gray-800 text-gray-500'>Or continue with</span>
            </div>
          </div>

          <div className='mt-6 grid grid-cols-2 gap-3'>
            <div>
              <GoogleLogin onSuccess={handleGoogleSuccess} onError={() => setError('Google login failed')} />
            </div>
            <button
              onClick={handleAppleLogin}
              className='w-full inline-flex justify-center py-2 px-4 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm bg-white dark:bg-gray-700 text-sm font-medium text-gray-500 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
            >
              <span className='sr-only'>Sign in with Apple</span>
              <svg className='w-5 h-5' fill='currentColor' viewBox='0 0 20 20'>
                <path d='M17.569 12.6254C17.597 15.652 20.2179 16.6592 20.25 16.674C20.229 16.7476 19.7574 18.2517 18.5697 19.8079C17.5379 21.1475 16.4661 22.478 14.8164 22.5116C13.2084 22.5444 12.7118 21.6401 10.8743 21.6401C9.03686 21.6401 8.48957 22.478 6.96311 22.5444C5.37282 22.6108 4.14479 21.1149 3.10328 19.7809C0.97916 17.0712 -0.623873 11.8506 1.55466 8.40719C2.63682 6.69672 4.44822 5.6087 6.42299 5.57588C7.97401 5.54306 9.42503 6.5457 10.3741 6.5457C11.3232 6.5457 13.0847 5.37237 14.9376 5.54306C15.6886 5.57588 17.7403 5.83813 19.1085 7.69297C18.9902 7.77017 17.5465 8.61733 17.569 12.6254ZM14.5858 3.77854C15.4521 2.74792 16.0495 1.30779 15.8985 0C14.6632 0.0544153 13.1795 0.847292 12.2805 1.87791C11.4715 2.79943 10.7623 4.26593 10.9461 5.54306C12.3143 5.64664 13.7198 4.80904 14.5858 3.77854Z' />
              </svg>
            </button>
          </div>
        </div> */}

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
