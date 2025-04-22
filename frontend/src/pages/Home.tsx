import Article from '../components/Article';
import Header from '../components/Header';
import BottomNavBar from '../components/BottomNavBar';

const Home = () => {
  // Sample data - in a real app, this would come from an API
  const articles = [
    {
      id: 1,
      title: 'First Article',
      datePublished: 'March 15, 2024',
      content: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco labori...',
    },
    {
      id: 2,
      title: 'Second Article',
      datePublished: 'March 14, 2024',
      content: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco labori...',
    },
    {
      id: 3,
      title: 'Third Article',
      datePublished: 'March 13, 2024',
      content: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco labori...',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 .styled-scrollbars">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24">
        <div className="space-y-6">
          {articles.map((article) => (
            <Article
              key={article.id}
              title={article.title}
              datePublished={article.datePublished}
              content={article.content}
            />
          ))}
        </div>
      </main>
      <BottomNavBar />
    </div>
  );
};

export default Home;
