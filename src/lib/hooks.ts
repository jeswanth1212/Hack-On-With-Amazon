'use client';

import React, { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { useRouter } from "next/navigation";
import { validateUserId, ContextData, UserProfile, createUserProfile, getUserProfile, getFriendActivities, getFriendRequests, getNotificationCount } from './utils';

/**
 * Custom hook to handle keyboard navigation in app drawers.
 */
export function useKeyboardNavigation(items: any[], initialFocusIndex = 0) {
  const [focusIndex, setFocusIndex] = useState(initialFocusIndex);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
            e.preventDefault();
        setFocusIndex((prevIndex) => (prevIndex > 0 ? prevIndex - 1 : items.length - 1));
      } else if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
            e.preventDefault();
        setFocusIndex((prevIndex) => (prevIndex < items.length - 1 ? prevIndex + 1 : 0));
          }
    },
    [items.length]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  return { focusIndex };
}

// Define authentication context type
interface AuthContextType {
  user: UserProfile | null;
  loading: boolean;
  error: string | null;
  login: (userId: string) => Promise<boolean>;
  logout: () => void;
  userContext: ContextData;
  setUserContext: (context: ContextData) => void;
  registerUser: (userData: UserProfile) => Promise<boolean>;
}

// Create authentication context
const AuthContext = createContext<AuthContextType | null>(null);

// Authentication provider props
interface AuthProviderProps {
  children: React.ReactNode;
}

// Authentication provider component
export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [userContext, setUserContext] = useState<ContextData>({});
  const router = useRouter();
  
  // Load user from localStorage on initial render
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedUser = localStorage.getItem('user');
      const savedContext = localStorage.getItem('userContext');
      
      if (savedUser) {
        try {
          setUser(JSON.parse(savedUser));
          if (savedContext) {
            setUserContext(JSON.parse(savedContext));
          }
        } catch (e) {
          console.error("Failed to parse saved user data:", e);
          localStorage.removeItem('user');
        }
      }
    }
    
    setLoading(false);
  }, []);
  
  // Login function
  const login = async (userId: string): Promise<boolean> => {
    setLoading(true);
    setError(null);
    
    try {
      const isValid = await validateUserId(userId);
      
      if (isValid) {
        // Try to fetch full profile details
        const fetchedProfile = await getUserProfile(userId);
        const userProfile: UserProfile = fetchedProfile || { user_id: userId };
        
        setUser(userProfile);
        localStorage.setItem('user', JSON.stringify(userProfile));
        setLoading(false);
        return true;
      } else {
        setError('User ID not found');
        setLoading(false);
        return false;
      }
    } catch (e) {
      setError('Failed to login');
      setLoading(false);
      return false;
    }
  };

  // Logout function
  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
    localStorage.removeItem('userContext');
    router.push('/');
  };

  // Update user context
  const updateUserContext = (context: ContextData) => {
    const newContext = { ...userContext, ...context };
    setUserContext(newContext);
    localStorage.setItem('userContext', JSON.stringify(newContext));
  };

  // Register new user (would need to be implemented on the backend)
  const registerUser = async (userData: UserProfile): Promise<boolean> => {
    setLoading(true);
    setError(null);
    
    try {
      // Call the backend API to create a user profile
      const createdUser = await createUserProfile(userData);
      
      if (createdUser) {
        setUser(createdUser);
        localStorage.setItem('user', JSON.stringify(createdUser));
        setLoading(false);
        return true;
      } else {
        setError('Failed to create user profile');
        setLoading(false);
        return false;
      }
    } catch (e) {
      setError('Failed to register user');
      setLoading(false);
      return false;
    }
  };

  return React.createElement(
    AuthContext.Provider,
    {
      value: {
        user,
        loading,
        error,
        login,
        logout,
        userContext,
        setUserContext: updateUserContext,
        registerUser
      }
    },
    children
  );
}

// Custom hook to use the auth context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
}

// Notification Context
interface NotificationState {
  friendRequestCount: number;
  friendActivityCount: number;
  totalCount: number;
  lastCheckedActivity: number;
  markActivityAsRead: () => void;
}

const NotificationContext = createContext<NotificationState>({
  friendRequestCount: 0,
  friendActivityCount: 0,
  totalCount: 0,
  lastCheckedActivity: Date.now(),
  markActivityAsRead: () => {}
});

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [friendRequestCount, setFriendRequestCount] = useState(0);
  const [friendActivityCount, setFriendActivityCount] = useState(0);
  const [lastCheckedActivity, setLastCheckedActivity] = useState(() => {
    // Initialize with stored value or current time
    const stored = localStorage.getItem('lastCheckedActivity');
    return stored ? parseInt(stored, 10) : Date.now();
  });
  
  // Load notifications
  useEffect(() => {
    if (!user) return;
    
    const loadNotifications = async () => {
      try {
        // Get notification counts from API
        const lastCheckedISOString = new Date(lastCheckedActivity).toISOString();
        const counts = await getNotificationCount(user.user_id, lastCheckedISOString);
        
        setFriendRequestCount(counts.friend_requests);
        setFriendActivityCount(counts.friend_activities);
      } catch (error) {
        console.error('Error loading notifications:', error);
      }
    };
    
    // Initial load
    loadNotifications();
    
    // Set up polling every 60 seconds
    const interval = setInterval(loadNotifications, 60000);
    return () => clearInterval(interval);
  }, [user, lastCheckedActivity]);
  
  const markActivityAsRead = () => {
    const now = Date.now();
    setLastCheckedActivity(now);
    setFriendActivityCount(0);
    // Store the timestamp in localStorage
    localStorage.setItem('lastCheckedActivity', now.toString());
  };
  
  const totalCount = friendRequestCount + friendActivityCount;
  
  return React.createElement(
    NotificationContext.Provider,
    {
      value: { 
        friendRequestCount, 
        friendActivityCount, 
        totalCount,
        lastCheckedActivity,
        markActivityAsRead
      }
    },
    children
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  
  return context;
} 