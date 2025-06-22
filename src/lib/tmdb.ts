const API_KEY = "ee41666274420bb7514d6f2f779b5fd9";
const BASE_URL = "https://api.themoviedb.org/3";
const IMAGE_BASE_URL = "https://image.tmdb.org/t/p";

// TMDb genre map for movies and TV
const GENRE_MAP: { [id: number]: string } = {
  28: 'Action',
  12: 'Adventure',
  16: 'Animation',
  35: 'Comedy',
  80: 'Crime',
  99: 'Documentary',
  18: 'Drama',
  10751: 'Family',
  14: 'Fantasy',
  36: 'History',
  27: 'Horror',
  10402: 'Music',
  9648: 'Mystery',
  10749: 'Romance',
  878: 'Science Fiction',
  10770: 'TV Movie',
  53: 'Thriller',
  10752: 'War',
  37: 'Western',
  10759: 'Action & Adventure',
  10762: 'Kids',
  10763: 'News',
  10764: 'Reality',
  10765: 'Sci-Fi & Fantasy',
  10766: 'Soap',
  10767: 'Talk',
  10768: 'War & Politics',
  10769: 'Foreign',
};

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
    // Map genre_ids to names if present
    let genres: string[] = [];
    if (Array.isArray(item.genre_ids)) {
      genres = item.genre_ids.map((id: number) => GENRE_MAP[id]).filter(Boolean);
    }
    return {
      id: item.id,
      title,
      description: item.overview,
      imageUrl,
      posterUrl,
      mediaType: item.media_type,
      releaseDate: item.release_date || item.first_air_date,
      rating: item.vote_average,
      provider: item.media_type === "movie" ? "Movie" : "TV Show",
      genres,
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

export { GENRE_MAP };

// ------------------------------------------------------------------
// Discover movies by language, genre(s) and release date >= 2020-01-01
// ------------------------------------------------------------------

// Build reverse map from genre name (lower-case) -> id for quick lookup
const GENRE_NAME_TO_ID: { [name: string]: number } = Object.entries(GENRE_MAP).reduce((acc, [id, name]) => {
  acc[name.toLowerCase()] = Number(id);
  return acc;
}, {} as { [name: string]: number });

export interface DiscoveredMovie {
  id: number;
  title: string;
  description: string;
  imageUrl: string;
  posterUrl: string;
  mediaType: 'movie';
  releaseDate: string;
  rating: number;
  provider: string;
  genres: string[];
}

/**
 * Discover movies on TMDB filtered by language, genres and released after 2020.
 *
 * @param language ISO 639-1 original language code (e.g. 'hi', 'en').
 * @param genres   Array of genre names (e.g. ['action', 'comedy']). Only the first
 *                 few that map to TMDB genre IDs will be used.
 * @param count    Max number of movies to return (defaults to 10).
 */
export async function discoverMoviesByLanguageGenre(
  language: string,
  genres: string[] = [],
  count: number = 10
): Promise<DiscoveredMovie[]> {
  if (!language) language = 'en';

  // Resolve genre IDs
  const genreIds: number[] = [];
  for (const g of genres) {
    const normalized = g.replace(/_/g, ' ').toLowerCase();
    const id = GENRE_NAME_TO_ID[normalized];
    if (id) genreIds.push(id);
  }

  // Choose a random page (TMDB allows up to 500). Limiting to first 5 pages keeps results relevant
  const randomPage = Math.floor(Math.random() * 5) + 1; // 1 – 5

  // Build discover URL (use randomPage for variety on every reload)
  let url = `${BASE_URL}/discover/movie?api_key=${API_KEY}` +
            `&with_original_language=${language}` +
            `&sort_by=popularity.desc` +
            `&primary_release_date.gte=2020-01-01` +
            `&page=${randomPage}`;

  if (genreIds.length > 0) {
    url += `&with_genres=${genreIds.join(',')}`;
  }

  const response = await fetch(url);
  if (!response.ok) {
    console.error('TMDB discover request failed:', response.status);
    return [];
  }

  const data = await response.json();
  // Shuffle results for extra randomness, then take the requested count
  const shuffled = Array.isArray(data.results)
    ? [...data.results].sort(() => Math.random() - 0.5)
    : [];
  const results = shuffled.slice(0, count);

  return results.map((item: any) => {
    const title = item.title || item.name;
    const imageUrl = `${IMAGE_BASE_URL}/original${item.backdrop_path}`;
    const posterUrl = `${IMAGE_BASE_URL}/w500${item.poster_path}`;
    const mappedGenres = Array.isArray(item.genre_ids)
      ? item.genre_ids.map((id: number) => GENRE_MAP[id]).filter(Boolean)
      : [];

    return {
      id: item.id,
      title,
      description: item.overview,
      imageUrl,
      posterUrl,
      mediaType: 'movie',
      releaseDate: item.release_date,
      rating: item.vote_average,
      provider: 'Movie',
      genres: mappedGenres,
    } as DiscoveredMovie;
  });
}

// Function to fetch trending data for the week for a specific region (country code)
export async function fetchTrendingWeekByRegion(region: string) {
  if (!region) region = 'US';
  const response = await fetch(
    `${BASE_URL}/trending/all/week?api_key=${API_KEY}&language=en-US&region=${region}`
  );
  if (!response.ok) {
    console.error('Failed to fetch region-based trending');
    return fetchTrendingWeek(); // fallback
  }
  const data = await response.json();
  return data.results.map((item: any) => {
    const title = item.title || item.name;
    const imageUrl = `${IMAGE_BASE_URL}/original${item.backdrop_path}`;
    const posterUrl = `${IMAGE_BASE_URL}/w500${item.poster_path}`;
    let genres: string[] = [];
    if (Array.isArray(item.genre_ids)) {
      genres = item.genre_ids.map((id: number) => GENRE_MAP[id]).filter(Boolean);
    }
    return {
      id: item.id,
      title,
      description: item.overview,
      imageUrl,
      posterUrl,
      mediaType: item.media_type,
      releaseDate: item.release_date || item.first_air_date,
      rating: item.vote_average,
      provider: item.media_type === 'movie' ? 'Movie' : 'TV Show',
      genres,
    };
  });
}

// Fetch trending TV shows for the week for a region
export async function fetchTrendingTvWeekByRegion(region: string) {
  if (!region) region = 'US';
  const response = await fetch(
    `${BASE_URL}/trending/tv/week?api_key=${API_KEY}&language=en-US&region=${region}`
  );
  if (!response.ok) {
    console.error('Failed to fetch trending TV');
    return [];
  }
  const data = await response.json();
  return data.results.map((item: any) => {
    const title = item.name;
    const imageUrl = `${IMAGE_BASE_URL}/original${item.backdrop_path}`;
    const posterUrl = `${IMAGE_BASE_URL}/w500${item.poster_path}`;
    let genres: string[] = [];
    if (Array.isArray(item.genre_ids)) {
      genres = item.genre_ids.map((id: number) => GENRE_MAP[id]).filter(Boolean);
    }
    return {
      id: item.id,
      title,
      description: item.overview,
      imageUrl,
      posterUrl,
      mediaType: 'tv',
      releaseDate: item.first_air_date,
      rating: item.vote_average,
      provider: 'TV Show',
      genres,
    };
  });
} 