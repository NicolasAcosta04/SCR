import { useEffect, useState } from 'react';
import Article from '../components/Article';
import Header from '../components/Header';
import BottomNavBar from '../components/BottomNavBar';

interface Article {
  article_id: string;
  title: string;
  content: string;
  source: string;
  url: string;
  published_at: string;
  image_url?: string;
  category: string;
  subcategory: string;
  confidence: number;
}

const dummyArticles: Article[] = [
  {
    article_id: '1',
    title: 'Scientists Discover New Species of Deep-Sea Creatures',
    content:
      'A team of marine biologists has discovered a previously unknown species of deep-sea creatures in the Mariana Trench. The discovery was made using advanced underwater drones equipped with high-resolution cameras. The newly discovered species, tentatively named "Abyssal Mariana," exhibits unique bioluminescent patterns and has adapted to survive in extreme pressure conditions. Researchers believe this discovery could provide valuable insights into the evolution of deep-sea life and the potential for undiscovered species in Earth\'s most remote ecosystems. The team plans to conduct further studies to understand the creature\'s role in the deep-sea food chain and its potential applications in biotechnology.',
    source: 'Science Daily',
    url: 'https://example.com/article1',
    published_at: '2024-03-15T10:00:00Z',
    image_url:
      'https://images.unsplash.com/photo-1581094794329-1d3f5d1d5c1c?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80',
    category: 'Science',
    subcategory: 'Biology',
    confidence: 0.95,
  },
  {
    article_id: '2',
    title: 'Tech Giant Unveils Revolutionary AI Assistant',
    content:
      "A leading technology company has announced the launch of its next-generation AI assistant, capable of understanding and responding to complex human emotions. The new system represents a significant leap forward in artificial intelligence, featuring advanced natural language processing and emotional intelligence algorithms. The AI assistant can detect subtle changes in tone, facial expressions, and context to provide more empathetic and personalized responses. Early tests show the system can maintain coherent conversations for extended periods while adapting its communication style to match the user's emotional state. Industry experts predict this development could revolutionize customer service, mental health support, and personal productivity applications.",
    source: 'Tech News',
    url: 'https://example.com/article2',
    published_at: '2024-03-14T15:30:00Z',
    image_url:
      'https://images.unsplash.com/photo-1677442136019-21780ecad995?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80',
    category: 'Technology',
    subcategory: 'Artificial Intelligence',
    confidence: 0.92,
  },
  {
    article_id: '3',
    title: 'Global Climate Summit Reaches Historic Agreement',
    content:
      "World leaders have reached a landmark agreement at the latest climate summit, committing to unprecedented reductions in carbon emissions. The deal includes ambitious targets for renewable energy adoption and carbon capture technology. Key provisions include a 50% reduction in fossil fuel usage by 2030, mandatory carbon pricing for major industries, and significant investments in green infrastructure. The agreement also establishes a global fund to support developing nations in their transition to sustainable energy sources. Environmental groups have praised the agreement as a crucial step forward, though some critics argue the timeline for implementation should be more aggressive. The summit's success marks a turning point in international climate cooperation.",
    source: 'Global News',
    url: 'https://example.com/article3',
    published_at: '2024-03-13T09:15:00Z',
    image_url:
      'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80',
    category: 'Environment',
    subcategory: 'Climate Change',
    confidence: 0.88,
  },
  {
    article_id: '4',
    title: 'Breakthrough in Quantum Computing Achieved',
    content:
      'Researchers have achieved a major breakthrough in quantum computing, successfully maintaining quantum coherence for record-breaking durations. This development could accelerate the timeline for practical quantum computers. The team managed to extend quantum coherence to over 100 milliseconds, a significant improvement over previous records. This advancement addresses one of the major challenges in quantum computing: maintaining the delicate quantum states long enough to perform complex calculations. The breakthrough was achieved through a combination of new materials, improved error correction techniques, and innovative cooling systems. Experts suggest this could lead to quantum computers capable of solving problems that are currently intractable for classical computers, such as complex molecular simulations and optimization problems.',
    source: 'Quantum Weekly',
    url: 'https://example.com/article4',
    published_at: '2024-03-12T14:20:00Z',
    image_url:
      'https://images.unsplash.com/photo-1635070041078-e363dbe005cb?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80',
    category: 'Science',
    subcategory: 'Physics',
    confidence: 0.91,
  },
  {
    article_id: '5',
    title: 'New Study Reveals Benefits of Mediterranean Diet',
    content:
      "A comprehensive study has confirmed the long-term health benefits of the Mediterranean diet, showing significant reductions in heart disease and improved cognitive function in participants who followed the diet for over a decade. The research, involving over 10,000 participants across multiple countries, found that strict adherence to the diet was associated with a 30% lower risk of cardiovascular events and a 20% reduction in cognitive decline. The study also identified specific components of the diet that contribute most to these benefits, including olive oil, nuts, fish, and whole grains. Researchers noted that the diet's emphasis on plant-based foods and healthy fats appears to have synergistic effects on both physical and mental health. The findings support previous research and provide more detailed insights into the mechanisms behind the diet's health benefits.",
    source: 'Health Journal',
    url: 'https://example.com/article5',
    published_at: '2024-03-11T11:45:00Z',
    image_url:
      'https://images.unsplash.com/photo-1490645935967-10de6ba17061?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80',
    category: 'Health',
    subcategory: 'Nutrition',
    confidence: 0.89,
  },
];

const Home = () => {
  const [articles, setArticles] = useState<Article[]>(dummyArticles);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const fetchArticles = async (pageNum: number = 1) => {
    try {
      setLoading(true);
      // const response = await fetch('http://localhost:8000/articles/fetch', {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json',
      //   },
      //   body: JSON.stringify({
      //     page_size: 10,
      //     days_back: 7,
      //     page: pageNum,
      //   }),
      // });

      // if (!response.ok) {
      //   throw new Error('Failed to fetch articles');
      // }

      // const newArticles = await response.json();
      // if (newArticles.length === 0) {
      //   setHasMore(false);
      // } else {
      //   setArticles((prev) => [...prev, ...newArticles]);
      // }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load articles');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArticles();
  }, []);

  const handleScroll = () => {
    if (window.innerHeight + document.documentElement.scrollTop === document.documentElement.offsetHeight) {
      if (!loading && hasMore) {
        setPage((prev) => prev + 1);
        fetchArticles(page + 1);
      }
    }
  };

  useEffect(() => {
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [loading, hasMore, page]);

  if (loading && articles.length === 0) {
    return (
      <div className='min-h-screen bg-gray-50 dark:bg-gray-900 .styled-scrollbars'>
        <Header />
        <main className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24'>
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
        <BottomNavBar />
      </div>
    );
  }

  if (error) {
    return (
      <div className='min-h-screen bg-gray-50 dark:bg-gray-900 .styled-scrollbars'>
        <Header />
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
            <button
              onClick={() => {
                setError(null);
                fetchArticles();
              }}
              className='px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors'
            >
              Try Again
            </button>
          </div>
        </main>
        <BottomNavBar />
      </div>
    );
  }

  return (
    <div className='min-h-screen bg-gray-50 dark:bg-gray-900 .styled-scrollbars'>
      <Header />
      <main className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24'>
        <div className='space-y-6'>
          {articles.map((article) => (
            <Article
              key={article.article_id}
              article_id={article.article_id}
              title={article.title}
              content={article.content}
              source={article.source}
              url={article.url}
              published_at={article.published_at}
              image_url={article.image_url}
              category={article.category}
              subcategory={article.subcategory}
              confidence={article.confidence}
            />
          ))}
          {loading && articles.length > 0 && (
            <div className='text-center'>
              <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto'></div>
            </div>
          )}
        </div>
      </main>
      <BottomNavBar />
    </div>
  );
};

export default Home;
