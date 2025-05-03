import ActiveRefreshSVG from './ActiveRefreshSVG';
import UnActiveRefreshSVG from './UnActiveRefreshSVG';

const RefreshArticlesButton = ({ handleRefresh, refreshing }: { handleRefresh: () => void; refreshing: boolean }) => {
  return (
    <button
      onClick={handleRefresh}
      disabled={refreshing}
      className='inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed'
    >
      {refreshing ? <ActiveRefreshSVG /> : <UnActiveRefreshSVG />}
    </button>
  );
};

export default RefreshArticlesButton;
