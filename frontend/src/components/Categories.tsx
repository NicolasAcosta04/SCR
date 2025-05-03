const Categories = ({
  activePreference,
  setActivePreference,
  setLoading,
  setPage,
  fetchArticles,
  setSkeleton,
  userDetails,
  getCategoryLabel,
}: {
  activePreference: string;
  setActivePreference: (value: string) => void;
  setLoading: (value: boolean) => void;
  setPage: (value: number) => void;
  fetchArticles: (page: number, refresh: boolean, skeleton: boolean, category: string) => void;
  setSkeleton: (value: boolean) => void;
  userDetails: any;
  getCategoryLabel: (value: string) => string;
}) => {
  return (
    <div className='relative'>
      <select
        value={activePreference || ''}
        onChange={(e) => {
          const value = e.target.value;
          setLoading(true);
          setActivePreference(value || '');
          setPage(1);
          fetchArticles(1, false, true, value || '');
          setSkeleton(true);
        }}
        className='appearance-none bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'
      >
        <option value=''>All Categories</option>
        {userDetails.preferences.map((cat: string) => (
          <option key={cat} value={cat}>
            {getCategoryLabel(cat)}
          </option>
        ))}
      </select>
      <div className='pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700 dark:text-gray-300'>
        <svg className='fill-current h-4 w-4' xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20'>
          <path d='M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z' />
        </svg>
      </div>
    </div>
  );
};

export default Categories;
