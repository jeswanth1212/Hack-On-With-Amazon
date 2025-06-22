import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Recommendation System API
 */

export const RECOMMENDATION_API_URL = "http://localhost:8080";

export interface RecommendationItem {
  item_id: string;
  title: string;
  score: number;
  genres?: string;
  release_year?: number;
  overview?: string;
}

export interface UserProfile {
  user_id: string;
  age?: number;
  age_group?: string;
  location?: string;
  language_preference?: string;
  preferred_genres?: string[];
  last_updated?: string;
}

export interface ContextData {
  mood?: string;
  time_of_day?: string;
  day_of_week?: string;
  weather?: string;
  age?: number;
  location?: string;
  language?: string;
  preferred_languages?: string;
}

export interface SelectionOption {
  id: string;
  name: string;
}

export interface RegistrationOptions {
  genres: SelectionOption[];
  languages: SelectionOption[];
}

export async function getRecommendations(
  userId: string,
  count: number = 6,
  context?: ContextData,
  includeLocalLanguage: boolean = true,
  languageWeight: number = 0.95,
  ensureLanguageDiversity: boolean = true
): Promise<RecommendationItem[]> {
  try {
    // Create a unique URL with the user ID to ensure unique recommendations
    let url = `${RECOMMENDATION_API_URL}/recommend?user_id=${userId}&n=${count}`;
    
    // Add language preferences to ensure diversity and proper filtering
    url += `&include_local_language=${includeLocalLanguage}`;
    url += `&language_weight=${languageWeight}`;
    url += `&ensure_language_diversity=${ensureLanguageDiversity}`;
    
    // Add context parameters if provided
    if (context) {
      if (context.mood) url += `&mood=${encodeURIComponent(context.mood)}`;
      if (context.time_of_day) url += `&time_of_day=${encodeURIComponent(context.time_of_day)}`;
      if (context.day_of_week) url += `&day_of_week=${encodeURIComponent(context.day_of_week)}`;
      if (context.weather) url += `&weather=${encodeURIComponent(context.weather)}`;
      if (context.age) url += `&age=${context.age}`;
      if (context.location) url += `&location=${encodeURIComponent(context.location)}`;
      if (context.language) url += `&language=${encodeURIComponent(context.language)}`;
      
      // Add preferred languages if available from user context
      if (context.preferred_languages) {
        url += `&preferred_languages=${encodeURIComponent(context.preferred_languages)}`;
      }
    }
    
    // Force unique results every time by adding random value and timestamp
    url += `&_uuid=${crypto.randomUUID()}`;
    url += `&_t=${Date.now()}`;
    
    // Disable browser caching
    const response = await fetch(url, {
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Error fetching recommendations: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch recommendations:", error);
    return [];
  }
}

export async function recordInteraction(
  userId: string,
  itemId: string,
  sentimentScore: number = 0.5,
  context?: ContextData
) {
  try {
    const payload = {
      user_id: userId,
      item_id: itemId,
      sentiment_score: sentimentScore,
      ...context
    };
    
    const response = await fetch(`${RECOMMENDATION_API_URL}/interaction`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    
    if (!response.ok) {
      throw new Error(`Error recording interaction: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error("Failed to record interaction:", error);
    return null;
  }
}

export async function getUserHistory(userId: string, limit: number = 10) {
  try {
    const response = await fetch(`${RECOMMENDATION_API_URL}/user/${userId}/history?limit=${limit}`);
    
    if (!response.ok) {
      throw new Error(`Error fetching user history: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch user history:", error);
    return [];
  }
}

export async function getRegistrationOptions(): Promise<RegistrationOptions> {
  try {
    const response = await fetch(`${RECOMMENDATION_API_URL}/options`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      mode: 'cors', // Add explicit CORS mode
    });
    
    if (!response.ok) {
      throw new Error(`Error fetching registration options: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch registration options:", error);
    // Return fallback options if API fails
    return { 
      genres: [
        {id: "action", name: "Action"},
        {id: "comedy", name: "Comedy"},
        {id: "drama", name: "Drama"},
        {id: "horror", name: "Horror"},
        {id: "romance", name: "Romance"},
        {id: "science_fiction", name: "Science Fiction"}
      ], 
      languages: [
        {id: "en", name: "English"},
        {id: "hi", name: "Hindi"},
        {id: "ta", name: "Tamil"},
        {id: "te", name: "Telugu"}
      ] 
    };
  }
}

export async function createUserProfile(userData: UserProfile): Promise<UserProfile | null> {
  try {
    const response = await fetch(`${RECOMMENDATION_API_URL}/user`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      mode: 'cors', // Add explicit CORS mode
      body: JSON.stringify({
        user_id: userData.user_id,
        age: userData.age ? parseInt(userData.age.toString()) : undefined,
        location: userData.location,
        language_preference: userData.language_preference,
        preferred_genres: userData.preferred_genres
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Error creating user profile: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error("Failed to create user profile:", error);
    // Create a mock success response for testing
    if (userData.user_id) {
      return {
        ...userData,
        age_group: userData.age && userData.age < 30 ? "Young Adult" : "Adult"
      };
    }
    return null;
  }
}

export async function validateUserId(userId: string): Promise<boolean> {
  try {
    // Check if the user exists by trying to get their history
    const response = await fetch(`${RECOMMENDATION_API_URL}/user/${userId}/history?limit=1`);
    
    // If we get a successful response, the user exists
    return response.ok;
  } catch (error) {
    console.error("Failed to validate user ID:", error);
    return false;
  }
}

// -------------------------------------------------------------
// Fetch full user profile (language preference, genres, etc.)
// -------------------------------------------------------------

export async function getUserProfile(userId: string): Promise<UserProfile | null> {
  try {
    const response = await fetch(`${RECOMMENDATION_API_URL}/user/${userId}`);
    if (!response.ok) {
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch user profile:", error);
    return null;
  }
}

interface RecommendationContext {
  mood?: string;
  time_of_day?: string;
  day_of_week?: string;
  weather?: string;
  age?: number;
  location?: string;
  language?: string;
}

// Friend system types and functions
export interface Friend {
  user_id: string;
  age?: number;
  age_group?: string;
  location?: string;
  language_preference?: string;
  preferred_genres?: string[];
  friendship_date: string;
}

export interface FriendRequest {
  request_id: number;
  sender_id: string;
  receiver_id: string;
  status: string;
  created_at: string;
  updated_at?: string;
  age?: number;
  location?: string;
  language_preference?: string;
}

export interface FriendActivity {
  friend_id: string;
  item_id: string;
  title: string;
  timestamp: string;
  genres?: string;
  release_year?: number;
  sentiment_score?: number;
}

export interface NotificationCount {
  friend_requests: number;
  friend_activities: number;
  watch_parties: number;
  total: number;
}

export interface WatchPartyInvite {
  party_id: number;
  host_id: string;
  tmdb_id: number;
  created_at: string;
}

// Search for users
export const searchUsers = async (query: string, userId: string): Promise<UserProfile[]> => {
  try {
    const response = await fetch(
      `http://localhost:8080/friends/search?user_id=${encodeURIComponent(userId)}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to search users');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error searching users:', error);
    return [];
  }
};

// Send friend request
export const sendFriendRequest = async (senderId: string, receiverId: string): Promise<boolean> => {
  try {
    const response = await fetch('http://localhost:8080/friends/request', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sender_id: senderId,
        receiver_id: receiverId,
      }),
    });
    
    return response.ok;
  } catch (error) {
    console.error('Error sending friend request:', error);
    return false;
  }
};

// Get friend requests
export const getFriendRequests = async (userId: string): Promise<FriendRequest[]> => {
  try {
    const response = await fetch(`http://localhost:8080/friends/requests/${userId}`);
    
    if (!response.ok) {
      throw new Error('Failed to get friend requests');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error getting friend requests:', error);
    return [];
  }
};

// Respond to friend request
export const respondToFriendRequest = async (
  requestId: number, 
  status: 'accepted' | 'rejected'
): Promise<boolean> => {
  try {
    const response = await fetch(`http://localhost:8080/friends/requests/${requestId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ status }),
    });
    
    return response.ok;
  } catch (error) {
    console.error('Error responding to friend request:', error);
    return false;
  }
};

// Get friends
export const getFriends = async (userId: string): Promise<Friend[]> => {
  try {
    const response = await fetch(`http://localhost:8080/friends/${userId}`);
    
    if (!response.ok) {
      throw new Error('Failed to get friends');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error getting friends:', error);
    return [];
  }
};

// Get friend activities
export const getFriendActivities = async (userId: string, limit: number = 20): Promise<FriendActivity[]> => {
  try {
    const response = await fetch(`${RECOMMENDATION_API_URL}/friends/${userId}/activities?limit=${limit}`);
    if (!response.ok) throw new Error(`Error fetching friend activities: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch friend activities:', error);
    return [];
  }
};

// Get notification count
export const getNotificationCount = async (userId: string, sinceTimestamp?: string): Promise<NotificationCount> => {
  try {
    let url = `${RECOMMENDATION_API_URL}/friends/${userId}/notifications`;
    if (sinceTimestamp) {
      url += `?since_timestamp=${encodeURIComponent(sinceTimestamp)}`;
    }
    
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Error fetching notification count: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch notification count:', error);
    return { friend_requests: 0, friend_activities: 0, watch_parties: 0, total: 0 };
  }
};

// Get friend recommendations
export const getFriendRecommendations = async (userId: string, n: number = 5): Promise<RecommendationItem[]> => {
  try {
    const response = await fetch(`http://localhost:8080/friends/recommendations/${userId}?n=${n}`);
    
    if (!response.ok) {
      throw new Error('Failed to get friend recommendations');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error getting friend recommendations:', error);
    return [];
  }
};

export const getWatchPartyInvites = async (userId: string): Promise<WatchPartyInvite[]> => {
  try {
    const res = await fetch(`${RECOMMENDATION_API_URL}/watchparty/notifications/${userId}`);
    if (!res.ok) throw new Error('Failed to fetch watch party invites');
    return await res.json();
  } catch (e) {
    console.error('Error fetching watch party invites:', e);
    return [];
  }
};

export const acceptWatchPartyInvite = async (partyId: number, userId: string): Promise<boolean> => {
  try {
    const res = await fetch(`${RECOMMENDATION_API_URL}/watchparty/accept?party_id=${partyId}&user_id=${encodeURIComponent(userId)}`, {
      method: 'POST'
    });
    return res.ok;
  } catch (e) {
    console.error('Error accepting watch party invite:', e);
    return false;
  }
};
