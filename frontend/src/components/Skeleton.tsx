const Skeleton = () => {
  return (
    <main className='max-w-7xl mx-auto px-4 sm:px-4 lg:px-8 pt-8 pb-24'>
      <div className='space-y-6'>
        {[...Array(3)].map((_, i) => (
          <div key={i} className='animate-pulse'>
            <div className='h-48 bg-gray-200 dark:bg-gray-700 rounded-lg mb-4'></div>
            <div className='h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2'></div>
            <div className='h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2'></div>
          </div>
        ))}
      </div>
    </main>
  );
};

export default Skeleton;
