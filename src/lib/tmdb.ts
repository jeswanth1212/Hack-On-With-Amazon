const API_KEY = "ee41666274420bb7514d6f2f779b5fd9";
const BASE_URL = "https://api.themoviedb.org/3";
const IMAGE_BASE_URL = "https://image.tmdb.org/t/p";

// Function to fetch trending data for the week
export async function fetchTrendingWeek() {
  const response = await fetch(
    `${BASE_URL}/trending/all/week?api_key=${API_KEY}&language=en-US`
  );
  
  if (!response.ok) {
    throw new Error("Failed to fetch trending data");
  }
  
  const data = await response.json();
  
  // Process the data to get formatted information for our UI
  return data.results.map((item: any) => {
    const title = item.title || item.name;
    const imageUrl = `${IMAGE_BASE_URL}/original${item.backdrop_path}`;
    const posterUrl = `${IMAGE_BASE_URL}/w500${item.poster_path}`;
    
    return {
      id: item.id,
      title,
      description: item.overview,
      imageUrl,
      posterUrl,
      mediaType: item.media_type,
      releaseDate: item.release_date || item.first_air_date,
      rating: item.vote_average,
      provider: item.media_type === "movie" ? "Movie" : "TV Show"
    };
  });
}

// Function to get poster images for carousels
export function getPosterUrl(path: string, size = "w500") {
  return `${IMAGE_BASE_URL}/${size}${path}`;
}

// Function to get backdrop images for banners
export function getBackdropUrl(path: string, size = "original") {
  return `${IMAGE_BASE_URL}/${size}${path}`;
}

// Function to search for movies and TV shows
export async function searchMulti(query: string, limit: number = 15) {
  if (!query || query.length < 2) {
    return [];
  }
  
  const response = await fetch(
    `${BASE_URL}/search/multi?api_key=${API_KEY}&language=en-US&query=${encodeURIComponent(query)}&page=1&include_adult=false`
  );
  
  if (!response.ok) {
    throw new Error("Failed to search");
  }
  
  const data = await response.json();
  
  // Filter out people and items without poster images or with zero rating
  const filteredResults = data.results
    .filter((item: any) => 
      // Only include movies and TV shows
      (item.media_type === 'movie' || item.media_type === 'tv') &&
      // Only include items with poster images
      item.poster_path &&
      // Only include items with ratings > 0
      item.vote_average > 0
    );
  
  // Sort by rating (highest first)
  const sortedResults = [...filteredResults].sort((a, b) => b.vote_average - a.vote_average);
  
  // Limit the number of results
  const limitedResults = sortedResults.slice(0, limit);
  
  // Process the data to get formatted information for our UI
  return limitedResults.map((item: any) => {
    const title = item.title || item.name;
    const posterPath = `${IMAGE_BASE_URL}/w500${item.poster_path}`;
    
    return {
      id: item.id,
      title,
      description: item.overview,
      posterUrl: posterPath,
      mediaType: item.media_type,
      releaseDate: item.release_date || item.first_air_date,
      rating: item.vote_average,
      provider: item.media_type === "movie" ? "Movie" : "TV Show"
    };
  });
} 