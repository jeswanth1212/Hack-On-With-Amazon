"use client";

import React, { useEffect, useState } from 'react';
import MainLayout from '../layout/MainLayout';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import ContentCard from '../ui/ContentCard';
import ContentCarousel from '../ui/ContentCarousel';

// TODO: Replace with your actual TMDb API key
const TMDB_API_KEY = 'ee41666274420bb7514d6f2f779b5fd9';
const TMDB_BASE_URL = 'https://api.themoviedb.org/3';
const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/original';
const TMDB_IMAGE_POSTER = 'https://image.tmdb.org/t/p/w500';

interface MovieDetailPageProps {
  tmdbId: string;
}

const fetchMovieDetails = async (tmdbId: string) => {
  const res = await fetch(`${TMDB_BASE_URL}/movie/${tmdbId}?api_key=${TMDB_API_KEY}&append_to_response=credits,images,videos,recommendations`);
  if (!res.ok) throw new Error('Failed to fetch movie details');
  return res.json();
};

const getLanguageName = (code: string) => {
  try {
    return new Intl.DisplayNames(['en'], { type: 'language' }).of(code);
  } catch {
    return code;
  }
};

const PersonCard = ({ image, name, role }: { image: string | null, name: string, role: string }) => (
  <div className="flex flex-col items-center bg-white/5 rounded-2xl p-3 min-w-[120px] max-w-[120px] shadow-md">
    <div className="w-20 h-20 rounded-full overflow-hidden border-2 border-white/20 mb-2 bg-gradient-to-tr from-blue-900/30 to-purple-900/30 flex items-center justify-center">
      {image ? (
        <img src={image} alt={name} className="w-full h-full object-cover" />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-gray-800 text-gray-400 text-2xl">?</div>
      )}
    </div>
    <div className="text-center">
      <div className="font-semibold text-white text-sm leading-tight line-clamp-2">{name}</div>
      <div className="text-xs text-gray-300 mt-1 line-clamp-2">{role}</div>
    </div>
  </div>
);

const MovieDetailPage: React.FC<MovieDetailPageProps> = ({ tmdbId }) => {
  const [movie, setMovie] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchMovieDetails(tmdbId)
      .then(setMovie)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [tmdbId]);

  if (loading) return <div className="flex justify-center items-center h-96">Loading...</div>;
  if (error) return <div className="text-red-500">{error}</div>;
  if (!movie) return null;

  // Extract data
  const {
    title,
    overview,
    release_date,
    runtime,
    status,
    original_language,
    genres,
    vote_average,
    vote_count,
    poster_path,
    backdrop_path,
    credits,
    images,
    videos,
    recommendations,
  } = movie;

  const cast = credits?.cast?.slice(0, 10) || [];
  const crew = credits?.crew?.filter((c: any) => ['Director', 'Writer', 'Screenplay'].includes(c.job)).slice(0, 5) || [];
  const posters = images?.posters?.slice(0, 8) || [];
  const backdrops = images?.backdrops?.slice(0, 8) || [];
  const trailers = (videos?.results || []).filter((v: any) => v.site === 'YouTube' && v.type === 'Trailer');
  const similar = recommendations?.results?.slice(0, 8) || [];

  // Combine cast and crew into one array, removing duplicates by name+role
  const combinedPeople = [
    ...cast.map((actor: any) => ({
      id: `cast-${actor.cast_id}`,
      name: actor.name,
      imageUrl: actor.profile_path ? `${TMDB_IMAGE_POSTER}${actor.profile_path}` : '/placeholder.png',
      role: actor.character,
    })),
    ...crew.map((member: any) => ({
      id: `crew-${member.credit_id}`,
      name: member.name,
      imageUrl: member.profile_path ? `${TMDB_IMAGE_POSTER}${member.profile_path}` : '/placeholder.png',
      role: member.job,
    })),
  ];
  // Remove duplicates (same name+role)
  const seen = new Set();
  const uniquePeople = combinedPeople.filter((person) => {
    const key = person.name + person.role;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });

  const peopleCards = uniquePeople.map((person) => (
    <ContentCard
      key={person.id}
      id={person.id}
      title={person.name}
      imageUrl={person.imageUrl}
      year={person.role}
      rating={undefined}
      source={undefined}
    />
  ));

  return (
    <MainLayout>
      {/* Hero Section with Large Poster and Fade */}
      <div className="relative w-full min-h-[90vh] flex items-end justify-start bg-black overflow-hidden rounded-b-3xl shadow-lg mb-0">
        {/* Backdrop as background */}
        {backdrop_path && (
          <img
            src={`${TMDB_IMAGE_BASE}${backdrop_path}`}
            alt={title}
            className="absolute inset-0 w-full h-full object-cover opacity-60"
            style={{ zIndex: 0 }}
          />
        )}
        {/* Large Poster and Info */}
        <div className="relative z-10 flex flex-col md:flex-row items-end md:items-center gap-8 p-8 md:p-16 w-full">
          <div className="flex-shrink-0">
            <img
              src={poster_path ? `${TMDB_IMAGE_POSTER}${poster_path}` : '/placeholder.png'}
              alt={title}
              className="rounded-2xl shadow-2xl w-56 md:w-80 h-auto object-cover border-4 border-white/10"
              style={{ maxHeight: '75vh' }}
            />
          </div>
          <div className="flex-1 flex flex-col gap-2 text-white md:ml-8">
            <h1 className="text-4xl md:text-5xl font-extrabold mb-2 drop-shadow-lg">{title}</h1>
            <div className="flex flex-wrap gap-2 mb-2">
              {genres?.map((g: any) => (
                <span key={g.id} className="bg-yellow-500/90 text-black font-semibold px-3 py-1 rounded-full text-xs">{g.name}</span>
              ))}
              <span className="text-gray-200">{release_date?.slice(0, 4)}</span>
              <span className="text-gray-200">{runtime} min</span>
              <span className="text-gray-200">{status}</span>
              <span className="text-gray-200">{getLanguageName(original_language)}</span>
            </div>
            <div className="flex items-center gap-4 mb-2">
              <span className="text-yellow-400 font-semibold text-lg">★ {vote_average?.toFixed(1)}</span>
              <span className="text-gray-200">({vote_count} ratings)</span>
            </div>
            <p className="text-lg text-gray-100 mb-4 max-w-2xl drop-shadow">{overview}</p>
            <div className="flex gap-4 mt-2">
              <Button className="w-40 bg-yellow-500 text-black font-bold hover:bg-yellow-400 transition">Watch</Button>
            </div>
          </div>
        </div>
        {/* Fade-out gradient at the bottom */}
        <div className="absolute bottom-0 left-0 w-full h-40 pointer-events-none" style={{ zIndex: 2, background: 'linear-gradient(to bottom, rgba(0,0,0,0) 0%, #111 100%)' }} />
      </div>

      {/* Cast & Crew Carousel, starts right after the fade */}
      {peopleCards.length > 0 && (
        <div className="relative z-20 -mt-10 px-8">
          <h2 className="text-2xl font-bold mb-4 text-white">Cast & Crew</h2>
          <ContentCarousel title="" slidesToShow={7} autoplay={false} className="">
            {peopleCards}
          </ContentCarousel>
        </div>
      )}

      {/* Trailers Carousel */}
      {trailers.length > 0 && (
        <div className="mb-10 px-8 mt-8">
          <h2 className="text-2xl font-bold mb-4 text-white">Trailers</h2>
          <div className="mt-4">
            <ContentCarousel title="" slidesToShow={3.5} autoplay={false} className="">
              {trailers.map((trailer: any) => (
                <a
                  key={trailer.id}
                  href={`https://www.youtube.com/watch?v=${trailer.key}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block min-w-[320px]"
                >
                  <img
                    src={`https://img.youtube.com/vi/${trailer.key}/hqdefault.jpg`}
                    alt={trailer.name}
                    className="rounded-lg w-80 h-48 object-cover shadow mb-2"
                  />
                  <div className="font-medium text-center text-white">{trailer.name}</div>
                </a>
              ))}
            </ContentCarousel>
          </div>
        </div>
      )}

      {/* Similar Movies Carousel */}
      {similar.length > 0 && (
        <div className="mb-10 px-8">
          <h2 className="text-2xl font-bold mb-4 text-white">Similar Movies</h2>
          <div className="mt-4">
            <ContentCarousel title="" slidesToShow={5.5} autoplay={false}>
              {similar.map((rec: any) => (
                <ContentCard
                  key={rec.id}
                  id={rec.id}
                  title={rec.title}
                  imageUrl={rec.poster_path ? `${TMDB_IMAGE_POSTER}${rec.poster_path}` : '/placeholder.png'}
                  year={rec.release_date?.slice(0, 4)}
                  rating={rec.vote_average?.toFixed(1)}
                  source={rec.media_type === 'tv' ? 'TV' : 'Movie'}
                />
              ))}
            </ContentCarousel>
          </div>
        </div>
      )}
    </MainLayout>
  );
};

export default MovieDetailPage; 