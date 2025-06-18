'use client';

import { useEffect, useState } from 'react';
import MainLayout from '../layout/MainLayout';
import HeroBanner from '../ui/HeroBanner';
import ContentCarousel from '../ui/ContentCarousel';
import ContentCard from '../ui/ContentCard';
import AppIcon from '../ui/AppIcon';
import { fetchTrendingWeek } from '@/lib/tmdb';

// App icons data
const appsData = [
  { id: 1, name: 'Netflix', iconFile: 'netflix.png' },
  { id: 2, name: 'Prime Video', iconFile: 'prime.png' },
  { id: 3, name: 'Freevee', iconFile: 'freevee.png' },
  { id: 4, name: 'YouTube', iconFile: 'YouTube.jpg' },
  { id: 5, name: 'Disney+', iconFile: 'disney.png' },
  { id: 6, name: 'HBO Max', iconFile: 'hbo.png' },
];

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
  
  // Create genre-based collections
  const actionMovies = movies.slice(0, 5);
  const comedyMovies = movies.slice(5, 10);
  const popularSeries = tvShows.slice(0, 5);

  // Split the trending data for different sections
  const featuredContent = trendingData.slice(0, 5);

  return (
    <MainLayout>
      <HeroBanner featuredContent={featuredContent} />
      <div className="max-w-full px-4 md:px-6 lg:px-8 mx-auto">
        <ContentCarousel title="My Apps" slidesToShow={6} compact={true}>
          {appsData.map((app) => (
            <AppIcon
              key={app.id}
              id={app.id}
              name={app.name}
              iconFile={app.iconFile}
            />
          ))}
        </ContentCarousel>

        <ContentCarousel title="Action Movies" slidesToShow={5}>
          {actionMovies.map((item) => (
            <ContentCard
              key={item.id}
              id={item.id}
              title={item.title}
              imageUrl={item.posterUrl}
              year={item.releaseDate?.substring(0, 4)}
              rating={item.rating.toFixed(1)}
              source={item.provider}
            />
          ))}
        </ContentCarousel>

        <ContentCarousel title="Comedy Movies" slidesToShow={5}>
          {comedyMovies.map((item) => (
            <ContentCard
              key={item.id}
              id={item.id}
              title={item.title}
              imageUrl={item.posterUrl}
              year={item.releaseDate?.substring(0, 4)}
              rating={item.rating.toFixed(1)}
              source={item.provider}
            />
          ))}
        </ContentCarousel>

        <ContentCarousel title="Popular TV Shows" slidesToShow={5}>
          {popularSeries.map((item) => (
            <ContentCard
              key={item.id}
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