'use client';

import { useEffect, useState } from 'react';
import MainLayout from '../layout/MainLayout';
import HeroBanner from '../ui/HeroBanner';
import ContentCarousel from '../ui/ContentCarousel';
import ContentCard from '../ui/ContentCard';
import AppIcon from '../ui/AppIcon';
import { fetchTrendingWeek } from '@/lib/tmdb';
import { getRecommendations, RecommendationItem } from '@/lib/utils';
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

export default function HomePage() {
  const [trendingData, setTrendingData] = useState<any[]>([]);
  const [personalizedData, setPersonalizedData] = useState<any[]>([]);
  const [heroData, setHeroData] = useState<any[]>([]);
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
        
        // Fetch personalized recommendations if user is logged in
        if (user) {
          const recs = await getRecommendations(user.user_id, 12, userContext); // get more for splitting
          
          // Fetch images for all recommendations
          const processedRecs = await Promise.all(recs.map(async (rec: RecommendationItem) => {
            const images = await fetchTmdbImages(rec.title, rec.release_year);
            let posterUrl = images.poster || '/placeholder.jpg';
            let backdropUrl = images.backdrop || posterUrl;
            const mediaType = rec.genres?.toLowerCase().includes('tv') ? 'tv' : 'movie';
            return {
              id: rec.item_id,
              title: rec.title,
              description: rec.overview || 'No description available',
              imageUrl: posterUrl, // for carousels
              posterUrl: posterUrl,
              backdropUrl: backdropUrl, // for hero banner
              mediaType: mediaType,
              releaseDate: rec.release_year ? `${rec.release_year}-01-01` : undefined,
              rating: rec.score * 10, // Scale the score to match TMDB's 0-10 rating
              provider: mediaType === 'movie' ? 'Movie' : 'TV Show'
            };
          }));
          
          // Split into hero and below carousel, no overlap
          const hero = processedRecs.slice(0, 5).map(item => ({ ...item, imageUrl: item.backdropUrl || item.posterUrl }));
          const below = processedRecs.slice(5, 11); // next 6
          setHeroData(hero);
          setPersonalizedData(below);
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
  const featuredContent = heroData.length > 0 ? heroData : trendingData.slice(0, 5);

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

        {user && personalizedData.length > 0 && (
          <ContentCarousel title={`Recommended for ${user.user_id}`}>
            {personalizedData.map((item, index) => (
              <ContentCard
                key={`recommended-${item.id}-${index}`}
                id={item.id}
                title={item.title}
                imageUrl={item.posterUrl}
                year={item.releaseDate?.substring(0, 4)}
                rating={typeof item.rating === 'number' ? item.rating.toFixed(1) : '0.0'}
                source={item.provider}
              />
            ))}
          </ContentCarousel>
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