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
  includeLocalLanguage: boolean = true
): Promise<RecommendationItem[]> {
  try {
    let url = `${RECOMMENDATION_API_URL}/recommend?user_id=${userId}&n=${count}&include_local_language=${includeLocalLanguage}`;
    
    // Add context parameters if provided
    if (context) {
      if (context.mood) url += `&mood=${context.mood}`;
      if (context.time_of_day) url += `&time_of_day=${context.time_of_day}`;
      if (context.day_of_week) url += `&day_of_week=${context.day_of_week}`;
      if (context.weather) url += `&weather=${context.weather}`;
      if (context.age) url += `&age=${context.age}`;
      if (context.location) url += `&location=${context.location}`;
      if (context.language) url += `&language=${context.language}`;
    }
    
    const response = await fetch(url);
    
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
