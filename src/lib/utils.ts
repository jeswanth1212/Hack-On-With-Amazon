import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Recommendation System API
 */

export const RECOMMENDATION_API_URL = "http://localhost:8000";

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
  last_updated?: string;
}

export interface ContextData {
  mood?: string;
  time_of_day?: string;
  day_of_week?: string;
  weather?: string;
  age?: number;
  location?: string;
}

export async function getRecommendations(
  userId: string,
  count: number = 6,
  context?: ContextData
): Promise<RecommendationItem[]> {
  try {
    let url = `${RECOMMENDATION_API_URL}/recommend?user_id=${userId}&n=${count}`;
    
    // Add context parameters if provided
    if (context) {
      if (context.mood) url += `&mood=${context.mood}`;
      if (context.time_of_day) url += `&time_of_day=${context.time_of_day}`;
      if (context.day_of_week) url += `&day_of_week=${context.day_of_week}`;
      if (context.weather) url += `&weather=${context.weather}`;
      if (context.age) url += `&age=${context.age}`;
      if (context.location) url += `&location=${context.location}`;
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

export async function validateUserId(userId: string): Promise<boolean> {
  try {
    // We'll try to get recommendations for this user
    // If it returns results, the user exists in the system
    const recommendations = await getRecommendations(userId, 1);
    return recommendations.length > 0;
  } catch (error) {
    console.error("Failed to validate user ID:", error);
    return false;
  }
}
