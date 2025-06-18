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