'use client';

import { useEffect, useState } from 'react';
import MainLayout from '../layout/MainLayout';
import HeroBanner from '../ui/HeroBanner';
import ContentCarousel from '../ui/ContentCarousel';
import ContentCard from '../ui/ContentCard';
import AppIcon from '../ui/AppIcon';
import { fetchTrendingWeek, discoverMoviesByLanguageGenre } from '@/lib/tmdb';
import { getRecommendations, RecommendationItem, getFriendRecommendations, getFriendActivities, FriendActivity } from '@/lib/utils';
import { Users } from 'lucide-react';
import { useAuth } from '@/lib/hooks';
import { Carousel, CarouselContent, CarouselItem, CarouselNext, CarouselPrevious } from "@/components/ui/carousel";

// App icons data
const appsData = [
  { id: 1, name: 'Netflix', iconFile: 'netflix.png' },
  { id: 2, name: 'Prime Video', iconFile: 'prime.png' },
  { id: 3, name: 'Freevee', iconFile: 'freevee.png' },
  { id: 4, name: 'YouTube', iconFile: 'youtube.png' },
  { id: 5, name: 'Disney+', iconFile: 'disney.png' },
  { id: 6, name: 'HBO Max', iconFile: 'hbo.png' },
  { id: 7, name: 'Apple TV+', iconFile: 'apple.png' },
  { id: 8, name: 'Hulu', iconFile: 'hulu.png' },
];

// Helper function to duplicate array items to reach desired length
const duplicateToLength = (array: any[], targetLength: number) => {
  const result = [...array];
  while (result.length < targetLength) {
    result.push(...array.slice(0, Math.min(array.length, targetLength - result.length)));
  }
  return result;
};

// Helper to fetch TMDB poster and backdrop for a movie or TV show by title/year
async function fetchTmdbImages(title: string, year?: number) {
  const apiKey = 'ee41666274420bb7514d6f2f779b5fd9';
  const query = encodeURIComponent(title);
  let url = `https://api.themoviedb.org/3/search/multi?api_key=${apiKey}&language=en-US&query=${query}&page=1&include_adult=false`;
  if (year) url += `&year=${year}`;
  try {
    const res = await fetch(url);
    if (!res.ok) return { poster: null, backdrop: null };
    const data = await res.json();
    const result = data.results && data.results.length > 0 ? data.results[0] : null;
    return {
      poster: result && result.poster_path ? `https://image.tmdb.org/t/p/w500${result.poster_path}` : null,
      backdrop: result && result.backdrop_path ? `https://image.tmdb.org/t/p/original${result.backdrop_path}` : null
    };
  } catch (e) {
    // ignore
  }
  return { poster: null, backdrop: null };
}

// Helper to fetch TMDB ID for a movie by title/year
async function fetchTmdbId(title: string, year?: number) {
  const apiKey = 'ee41666274420bb7514d6f2f779b5fd9';
  const query = encodeURIComponent(title);
  let url = `https://api.themoviedb.org/3/search/movie?api_key=${apiKey}&query=${query}`;
  if (year) url += `&year=${year}`;
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    const data = await res.json();
    if (data.results && data.results.length > 0) {
      return data.results[0].id;
    }
  } catch (e) {}
  return null;
}

export default function HomePage() {
  const [trendingData, setTrendingData] = useState<any[]>([]);
  const [personalizedData, setPersonalizedData] = useState<any[]>([]);
  const [heroData, setHeroData] = useState<any[]>([]);
  const [friendRecommendationsData, setFriendRecommendationsData] = useState<any[]>([]);
  const [friendActivitiesData, setFriendActivitiesData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user, userContext } = useAuth();

  // Fetch trending data and personalized recommendations
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch trending data
        const trending = await fetchTrendingWeek();
        setTrendingData(trending);
        
        // Only continue if user is logged in
        if (user) {
          // ----------------------------------------------
          // 1. Fetch TMDB movies based on user preferences
          // ----------------------------------------------
          let tmdbFiltered: any[] = [];

          if (user.language_preference && user.preferred_genres && user.preferred_genres.length > 0) {
            try {
              tmdbFiltered = await discoverMoviesByLanguageGenre(
                user.language_preference,
                user.preferred_genres,
                10 // get enough for hero, carousel, search overlay
              );
            } catch (e) {
              console.error('Failed to fetch TMDB-filtered movies:', e);
              tmdbFiltered = [];
            }
          }

          // -------------------------------------------------
          // 2. Fetch backend recommendations (existing logic)
          // -------------------------------------------------
          let processedRecs: any[] = [];
          try {
            // Enhanced context with preferred languages
            const enhancedContext = {
              ...userContext,
              preferred_languages: user.language_preference ? user.language_preference : 'en',
              user_unique_id: user.user_id + "_" + Date.now() // Ensure uniqueness
            };
            
            // Get unique recommendations based on user context
            const recs = await getRecommendations(
              user.user_id, 
              12, 
              enhancedContext, 
              true,  // includeLocalLanguage
              0.95,  // languageWeight
              true   // ensureLanguageDiversity
            );
            
            // Fetch TMDb ID and images for all recommendations
            processedRecs = await Promise.all(recs.map(async (rec) => {
              const tmdbId = await fetchTmdbId(rec.title, rec.release_year);
              if (!tmdbId) return null; // skip if not found
              const images = await fetchTmdbImages(rec.title, rec.release_year);
              let posterUrl = images.poster || '/placeholder.jpg';
              let backdropUrl = images.backdrop || posterUrl;
              const mediaType = rec.genres?.toLowerCase().includes('tv') ? 'tv' : 'movie';
              return {
                id: tmdbId,
                title: rec.title,
                description: rec.overview || 'No description available',
                imageUrl: posterUrl,
                posterUrl: posterUrl,
                backdropUrl: backdropUrl,
                mediaType: mediaType,
                releaseDate: rec.release_year ? `${rec.release_year}-01-01` : undefined,
                rating: rec.score * 10,
                provider: mediaType === 'movie' ? 'Movie' : 'TV Show',
                genres: rec.genres
              };
            }));
          } catch (err) {
            console.error("Failed to get recommendations from API, using trending data as fallback", err);
            // If recommendations API fails, just use trending data as fallback
            processedRecs = trending.slice(0, 12);
          }
          // Filter out invalid entries
          const filteredRecs = processedRecs.filter(Boolean);

          // If no backend recommendations were returned, fall back to trending data (skipping any overlap with heroTmdb)
          let fallbackBackend: any[] = [];
          if (filteredRecs.length === 0) {
            fallbackBackend = trending
              .filter((item: any) => !tmdbFiltered.some(t => t.id === item.id))
              .slice(0, 6);
          }

          const backendPoolRaw = filteredRecs.length > 0 ? filteredRecs : fallbackBackend;
          // Shuffle backend pool for variety
          const backendPool = [...backendPoolRaw].sort(() => Math.random() - 0.5);

          // -------------------------------------------------
          // 3. Build Hero Banner data (3 TMDB + 2 backend recs)
          // -------------------------------------------------

          // Make sure TMDB movies are unique across sections
          const heroTmdb = tmdbFiltered.slice(0, 3).map(item => ({
            ...item,
            imageUrl: item.imageUrl,
          }));

          const heroBackend = backendPool.slice(0, 2).map(item => ({
            ...item,
            imageUrl: item.backdropUrl || item.posterUrl,
          }));

          const heroCombined = [...heroTmdb, ...heroBackend];
          setHeroData(heroCombined);

          // -------------------------------------------------
          // 4. Build Recommendation carousel (4 TMDB + rest backend)
          // -------------------------------------------------

          // For carousel, skip TMDB movies already used in hero
          const carouselTmdb = tmdbFiltered.slice(3, 7).map(item => ({
            ...item,
            posterUrl: item.posterUrl,
          }));

          const carouselBackend = backendPool;

          const carouselCombined = [...carouselTmdb, ...carouselBackend];
          setPersonalizedData(carouselCombined);

          // -------------------------------------------------
          // 5. Persist TMDB IDs used on home page for SearchOverlay
          // -------------------------------------------------
          const usedTmdbIds = [...heroTmdb, ...carouselTmdb].map(m => m.id);
          if (typeof window !== 'undefined') {
            localStorage.setItem('homeTmdbIds', JSON.stringify(usedTmdbIds));
            // Remove recommendation caching
          }

          // -------------------------------------------------
          // 6. Fetch friend recommendations
          // -------------------------------------------------
          try {
            const friendRecs = await getFriendRecommendations(user.user_id, 6);
            
            // Fetch TMDb ID and images for friend recommendations
            const processedFriendRecs = await Promise.all(friendRecs.map(async (rec) => {
              const tmdbId = await fetchTmdbId(rec.title, rec.release_year);
              if (!tmdbId) return null; // skip if not found
              const images = await fetchTmdbImages(rec.title, rec.release_year);
              let posterUrl = images.poster || '/placeholder.jpg';
              let backdropUrl = images.backdrop || posterUrl;
              const mediaType = rec.genres?.toLowerCase().includes('tv') ? 'tv' : 'movie';
              return {
                id: tmdbId,
                title: rec.title,
                description: rec.overview || 'No description available',
                imageUrl: posterUrl,
                posterUrl: posterUrl,
                backdropUrl: backdropUrl,
                mediaType: mediaType,
                releaseDate: rec.release_year ? `${rec.release_year}-01-01` : undefined,
                rating: rec.score * 10,
                provider: mediaType === 'movie' ? 'Movie' : 'TV Show',
                genres: rec.genres,
                // Add friend info if available
                friendRecommended: true,
                friends: (rec as any).friends
              };
            }));
            
            // Filter out invalid entries
            const filteredFriendRecs = processedFriendRecs.filter(Boolean);
            setFriendRecommendationsData(filteredFriendRecs);
          } catch (err) {
            console.error("Failed to get friend recommendations", err);
            setFriendRecommendationsData([]);
          }

          // -------------------------------------------------
          // 7. Fetch friend activities for "Continue Watching with Friends"
          // -------------------------------------------------
          try {
            const friendActivities = await getFriendActivities(user.user_id, 10);
            
            // Process friend activities to get TMDB data
            const processedActivities = await Promise.all(friendActivities.map(async (activity) => {
              const tmdbId = await fetchTmdbId(activity.title, activity.release_year);
              if (!tmdbId) return null; // skip if not found
              
              const images = await fetchTmdbImages(activity.title, activity.release_year);
              let posterUrl = images.poster || '/placeholder.jpg';
              let backdropUrl = images.backdrop || posterUrl;
              const mediaType = activity.genres?.toLowerCase().includes('tv') ? 'tv' : 'movie';
              
              // Get sentiment description
              let sentimentDescription = "watched";
              if (activity.sentiment_score !== undefined) {
                if (activity.sentiment_score > 0.7) sentimentDescription = "loved";
                else if (activity.sentiment_score > 0.5) sentimentDescription = "liked";
                else if (activity.sentiment_score < 0.3) sentimentDescription = "disliked";
                else if (activity.sentiment_score < 0.5) sentimentDescription = "felt neutral about";
              }
              
              return {
                id: tmdbId,
                title: activity.title,
                imageUrl: posterUrl,
                posterUrl: posterUrl,
                backdropUrl: backdropUrl,
                mediaType: mediaType,
                releaseDate: activity.release_year ? `${activity.release_year}-01-01` : undefined,
                friendId: activity.friend_id,
                timestamp: activity.timestamp,
                sentimentScore: activity.sentiment_score,
                sentimentDescription
              };
            }));
            
            // Filter out invalid entries and sort by timestamp (most recent first)
            const filteredActivities = processedActivities
              .filter(Boolean)
              .sort((a, b) => new Date(b!.timestamp).getTime() - new Date(a!.timestamp).getTime());
            
            setFriendActivitiesData(filteredActivities);
          } catch (err) {
            console.error("Failed to get friend activities", err);
          }
        }
        setLoading(false);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Failed to load content');
        setLoading(false);
      }
    };
    fetchData();
  }, [user, userContext]);

  // Show loading state
  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-primary"></div>
        </div>
      </MainLayout>
    );
  }

  // Show error state
  if (error) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="text-white text-xl">{error}</div>
        </div>
      </MainLayout>
    );
  }

  // Filter trending data by media type
  const movies = trendingData.filter(item => item.mediaType === 'movie');
  const tvShows = trendingData.filter(item => item.mediaType === 'tv');
  
  // Create genre-based collections and duplicate to have ~15 items
  const actionMovies = duplicateToLength(movies.slice(0, 5), 15);
  const comedyMovies = duplicateToLength(movies.slice(5, 10), 15);
  const popularSeries = duplicateToLength(tvShows.slice(0, 5), 15);
  const trendingThisWeek = duplicateToLength(trendingData.slice(0, 7), 15);

  // Use heroData for banner if available, else trending
  const featuredContent = heroData.length > 0 ? heroData : trendingData.slice(0, 5).map(item => ({ ...item, genres: item.genres }));

  return (
    <MainLayout>
      <HeroBanner featuredContent={featuredContent} />
      <div className="max-w-full mx-auto">
        {/* App Icons with Shadcn Carousel */}
        <div className="mb-10 px-8">
          <h2 className="text-2xl font-bold mb-4 text-white">My Apps</h2>
          <div className="relative">
            <Carousel
              opts={{
                align: "start",
                loop: true,
              }}
              className="w-full carousel"
            >
              <CarouselContent>
                {appsData.map((app) => (
                  <CarouselItem 
                    key={app.id} 
                    className="basis-1/4 md:basis-1/5"
                  >
                    <div className="h-[140px] aspect-video p-1">
                      <AppIcon
                        id={app.id}
                        name={app.name}
                        iconFile={app.iconFile}
                      />
                    </div>
                  </CarouselItem>
                ))}
              </CarouselContent>
              <div className="hidden md:block">
                <CarouselPrevious className="carousel-prev left-2 bg-background/80 hover:bg-background" />
                <CarouselNext className="carousel-next right-2 bg-background/80 hover:bg-background" />
              </div>
            </Carousel>
          </div>
        </div>

         {/* Personalized Recommendations */}
         <section className="px-4 py-8 md:px-8">
            <h2 className="text-2xl md:text-3xl font-bold mb-6 text-white">
              {user ? 'Recommended for You' : 'Popular Picks'}
            </h2>
            <ContentCarousel title="">
              {personalizedData.map((item, i) => (
                <ContentCard 
                  key={`personalized-${i}-${item.id}`} 
                  id={item.id}
                  title={item.title}
                  imageUrl={item.posterUrl || item.imageUrl}
                  rating={item.rating ? item.rating.toString() : undefined}
                  year={item.releaseDate?.substring(0, 4)}
                />
              ))}
            </ContentCarousel>
          </section>

                  {/* Friend Activities - Continue Watching with Friends */}
          {user && friendActivitiesData.length > 0 && (
            <section className="px-8 mt-4">
              <div className="flex items-center gap-2 mb-4">
                <Users size={20} className="text-primary" />
                <h2 className="text-xl font-semibold">Continue Watching with Friends</h2>
              </div>
              <Carousel className="w-full">
                <CarouselContent>
                  {friendActivitiesData.map((item) => (
                    <CarouselItem key={`${item.id}-${item.friendId}`} className="basis-1/2 md:basis-1/3 lg:basis-1/4 xl:basis-1/5">
                      <ContentCard
                        id={item.id}
                        title={item.title}
                        imageUrl={item.posterUrl}
                        badge={`Friend ${item.friendId} ${item.sentimentDescription}`}
                        type={item.mediaType}
                      />
                    </CarouselItem>
                  ))}
                </CarouselContent>
                <CarouselPrevious />
                <CarouselNext />
              </Carousel>
            </section>
          )}

          {/* Friend Recommendations */}
          {user && friendRecommendationsData.length > 0 && (
            <section className="px-8 mt-4">
              <h2 className="text-xl font-semibold mb-4">Recommended by Friends</h2>
              <ContentCarousel items={friendRecommendationsData} />
            </section>
          )}

        <ContentCarousel title="Trending this week">
          {trendingThisWeek.map((item, index) => (
            <ContentCard
              key={`trending-${item.id}-${index}`}
              id={item.id}
              title={item.title}
              imageUrl={item.posterUrl}
              year={item.releaseDate?.substring(0, 4)}
              rating={item.rating.toFixed(1)}
              source={item.provider}
            />
          ))}
        </ContentCarousel>

        <ContentCarousel title="Action Movies">
          {actionMovies.map((item, index) => (
            <ContentCard
              key={`action-${item.id}-${index}`}
              id={item.id}
              title={item.title}
              imageUrl={item.posterUrl}
              year={item.releaseDate?.substring(0, 4)}
              rating={item.rating.toFixed(1)}
              source={item.provider}
            />
          ))}
        </ContentCarousel>

        <ContentCarousel title="Comedy Movies">
          {comedyMovies.map((item, index) => (
            <ContentCard
              key={`comedy-${item.id}-${index}`}
              id={item.id}
              title={item.title}
              imageUrl={item.posterUrl}
              year={item.releaseDate?.substring(0, 4)}
              rating={item.rating.toFixed(1)}
              source={item.provider}
            />
          ))}
        </ContentCarousel>

        <ContentCarousel title="Popular TV Shows">
          {popularSeries.map((item, index) => (
            <ContentCard
              key={`tv-${item.id}-${index}`}
              id={item.id}
              title={item.title}
              imageUrl={item.posterUrl}
              year={item.releaseDate?.substring(0, 4)}
              rating={item.rating.toFixed(1)}
              source={item.provider}
            />
          ))}
        </ContentCarousel>
      </div>
    </MainLayout>
  );
} 