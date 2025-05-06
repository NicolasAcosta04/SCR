/**
 * Represents a category with a value and display label
 * Used for category selection and display in the UI
 * Used in: components/Categories.tsx, components/Preferences.tsx
 */
interface Category {
  value: string; // The internal value used for the category
  label: string; // The display label shown to users
}

/**
 * Props interface for the Article component
 * Contains all the data needed to display a news article
 * Used in: components/Article.tsx, pages/Home.tsx, pages/Article.tsx
 */
interface ArticleProps {
  article_id: string; // Unique identifier for the article
  title: string; // Article headline
  content: string; // Main article content
  source: string; // News source/publisher
  url: string; // Original article URL
  published_at: string; // Publication timestamp
  image_url?: string; // Optional URL for article thumbnail
  category: string; // Article category (e.g., TECH, BUSINESS)
  confidence: number; // Model's confidence in category prediction
  onNavigate: () => void; // Callback for article click navigation
}

/**
 * Interface defining the shape of the authentication context
 * Used in: contexts/AuthContext.tsx, components/Header.tsx, pages/Login.tsx, pages/SignUp.tsx
 */
interface AuthContextType {
  loggedIn: boolean; // Current authentication state
  setLoggedIn: (value: boolean) => void; // Function to update authentication state
}

/**
 * Form data structure for user login
 * Used in: components/LoginForm.tsx, pages/Login.tsx
 */
interface LoginForm {
  username: string; // User's login username
  password: string; // User's login password
}

/**
 * Response structure from authentication endpoint
 * Used in: services/auth.ts, contexts/UserContext.tsx
 */
interface TokenResponse {
  access_token: string; // JWT access token
  token_type: string; // Token type (usually "Bearer")
}

/**
 * User profile and preference data
 * Used in: contexts/UserContext.tsx, components/UserProfile.tsx
 */
interface UserDetails {
  id: number; // User's unique identifier
  username: string; // User's display name
  preferences: string[]; // Array of user's preferred categories
}

/**
 * Detailed user preference tracking
 * Used for recommendation system and personalization
 * Used in: contexts/UserContext.tsx, services/recommendations.ts
 */
interface UserPreferences {
  categories: {
    [key: string]: {
      count: number; // Number of articles read in this category
      total_confidence: number; // Sum of confidence scores for this category
      last_interaction: string; // Timestamp of last interaction
    };
  };
  read_articles: Set<string>; // Set of article IDs that have been read
}

/**
 * Context interface for user-related state management
 * Provides user data and methods throughout the application
 * Used in: contexts/UserContext.tsx, components/Article.tsx, pages/Home.tsx
 */
interface UserContextType {
  userId: number | null; // Current user's ID
  token: string | null; // Authentication token
  userDetails: UserDetails | null; // User profile data
  articles: ArticleProps[]; // User's article list
  preferences: UserPreferences; // User's reading preferences
  setUserId: (id: number) => void; // Update user ID
  setToken: (token: string | null) => void; // Update auth token
  setUserDetails: (details: UserDetails | null) => void; // Update user details
  fetchUserDetails: () => Promise<void>; // Fetch user data from API
  addArticle: (article: ArticleProps) => void; // Add article to user's list
  updatePreferences: (category: string, confidence: number, articleId: string) => void; // Update reading preferences
  clearUserData: () => void; // Clear user data on logout
  updateUserPreferences: (preferences: string[]) => Promise<void>; // Update category preferences
}

/**
 * Theme type definition
 * Represents available application themes
 * Used in: contexts/ThemeContext.tsx, components/ThemeToggle.tsx
 */
type Theme = 'light' | 'dark';

/**
 * Context interface for theme management
 * Provides theme state and toggle functionality
 * Used in: contexts/ThemeContext.tsx, components/ThemeToggle.tsx, App.tsx
 */
interface ThemeContextType {
  theme: Theme; // Current theme
  toggleTheme: () => void; // Function to switch between themes
}

// Export all type definitions
export type { Category };
export type { ArticleProps };
export type { LoginForm };
export type { TokenResponse };
export type { UserDetails };
export type { UserPreferences };
export type { UserContextType };
export type { ThemeContextType };
export type { Theme };
export type { AuthContextType };
