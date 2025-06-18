'use client';

import { useEffect, useState } from 'react';
import MainLayout from '../layout/MainLayout';
import HeroBanner from '../ui/HeroBanner';
import ContentCarousel from '../ui/ContentCarousel';
import ContentCard from '../ui/ContentCard';
import AppIcon from '../ui/AppIcon';
import { fetchTrendingWeek } from '@/lib/tmdb';
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

export default function HomePage() {
  const [trendingData, setTrendingData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const getTrendingData = async () => {
      try {
        const data = await fetchTrendingWeek();
        setTrendingData(data);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching trending data:', err);
        setError('Failed to load trending content');
        setLoading(false);
      }
    };

    getTrendingData();
  }, []);

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

  // Split the trending data for different sections
  const featuredContent = trendingData.slice(0, 5);

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