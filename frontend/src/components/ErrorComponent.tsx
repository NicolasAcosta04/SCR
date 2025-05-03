const ErrorComponent = ({ error }: { error: string }) => {
  return (
    <main className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24'>
      <div className='bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6'>
        <div className='flex items-center gap-3 mb-4'>
          <svg className='w-6 h-6 text-red-500' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
            <path
              strokeLinecap='round'
              strokeLinejoin='round'
              strokeWidth={2}
              d='M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'
            />
          </svg>
          <h2 className='text-xl font-semibold text-red-800 dark:text-red-200'>Error Loading Articles</h2>
        </div>
        <p className='text-red-700 dark:text-red-300 mb-4'>{error}</p>
      </div>
    </main>
  );
};

export default ErrorComponent;
