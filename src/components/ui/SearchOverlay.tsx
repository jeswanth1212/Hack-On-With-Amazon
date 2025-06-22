'use client';

import { useEffect, useRef, useState } from 'react';
import { Search, X } from 'lucide-react';
import Image from 'next/image';
import { useKeyboardNavigation } from '@/lib/hooks';
import { searchMulti, discoverMoviesByLanguageGenre, fetchTrendingWeek } from '@/lib/tmdb';
import ContentCard from './ContentCard';
import { ScrollArea } from './scroll-area';
import { getRecommendations } from '@/lib/utils';
import { useAuth } from '@/lib/hooks';
import { useRouter } from 'next/navigation';
import WatchPartyBox from '@/components/watch-party/WatchPartyBox';

// Copy from HomePage for TMDb lookup
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
  } catch (e) {}
  return { poster: null, backdrop: null };
}

interface SearchOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  partyMode?: boolean;
  onSelectMovie?: (tmdbId: number) => void;
}

export default function SearchOverlay({ isOpen, onClose, partyMode = false, onSelectMovie }: SearchOverlayProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const [inputValue, setInputValue] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [debouncedValue, setDebouncedValue] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [hasSearched, setHasSearched] = useState(false);
  const { user, userContext } = useAuth();
  const [extraRecs, setExtraRecs] = useState<any[]>([]);
  const [extraLoading, setExtraLoading] = useState(false);
  const router = useRouter();
  // Load homepage TMDB IDs from localStorage (to avoid duplicates)
  const homeTmdbIds: number[] = typeof window !== 'undefined'
    ? (() => {
        try {
          return JSON.parse(localStorage.getItem('homeTmdbIds') || '[]');
        } catch {
          return [];
        }
      })()
    : [];

  // Reset state when closing
  useEffect(() => {
    if (!isOpen) {
      setInputValue('');
      setSearchResults([]);
      setSelectedIndex(-1);
      setHasSearched(false);
    }
  }, [isOpen]);
  
  // Prevent body scrolling when overlay is open
  useEffect(() => {
    if (isOpen) {
      // Save current body overflow style
      const originalStyle = window.getComputedStyle(document.body).overflow;
      // Disable scrolling on body
      document.body.style.overflow = 'hidden';
      
      // Restore original style when closing
      return () => {
        document.body.style.overflow = originalStyle;
      };
    }
  }, [isOpen]);

  // Focus input when overlay opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (overlayRef.current === e.target) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      if (inputValue.length >= 2) {
        setDebouncedValue(inputValue);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [inputValue]);

  // Fetch search results
  useEffect(() => {
    const fetchResults = async () => {
      if (debouncedValue.length >= 2) {
        setLoading(true);
        setHasSearched(true);
        try {
          const results = await searchMulti(debouncedValue);
          setSearchResults(results);
        } catch (error) {
          console.error('Error searching:', error);
          setSearchResults([]);
        } finally {
          setLoading(false);
        }
      } else {
        setSearchResults([]);
        setHasSearched(false);
      }
    };

    fetchResults();
  }, [debouncedValue]);

  // Fetch extra recommendations when overlay opens and search is empty
  useEffect(() => {
    if (isOpen && user && inputValue.length === 0) {
      setExtraLoading(true);
      (async () => {
        try {
          // ------------------------------
          // 1. TMDB filtered movies (4)
          // ------------------------------
          let tmdbMovies: any[] = [];
          try {
            const lang = (user.language_preference ?? 'en');
            const genres = (user.preferred_genres && user.preferred_genres.length > 0)
              ? user.preferred_genres
              : [];
            tmdbMovies = await discoverMoviesByLanguageGenre(lang, genres, 10);
          } catch (e) {
            console.error('Failed to fetch TMDB discover movies for search overlay:', e);
            tmdbMovies = [];
          }

          // Filter duplicates with homepage IDs and map into card objects
          const tmdbProcessed = tmdbMovies
            .filter(item => !homeTmdbIds.includes(item.id))
            .map(item => ({
              id: item.id,
              title: item.title,
              imageUrl: item.posterUrl,
              year: item.releaseDate?.substring(0,4),
              rating: item.rating,
              provider: 'Movie',
            }));

          // ------------------------------
          // 2. Backend recommendations (up to 4)
          // ------------------------------
          const recs = await getRecommendations(user.user_id, 16, userContext);
          const processedBackend = await Promise.all(recs.map(async (rec) => {
            const tmdbId = await fetchTmdbId(rec.title, rec.release_year);
            if (!tmdbId || homeTmdbIds.includes(tmdbId)) return null;
            const images = await fetchTmdbImages(rec.title, rec.release_year);
            let posterUrl = images.poster || '/placeholder.jpg';
            return {
              id: tmdbId,
              title: rec.title,
              imageUrl: posterUrl,
              year: rec.release_year,
              rating: rec.score * 10,
              provider: rec.genres?.toLowerCase().includes('tv') ? 'TV Show' : 'Movie',
            };
          }));

          // Ensure at least 4 TMDB picks
          const firstTmdb = tmdbProcessed.slice(0, 4);
          const backendPicks = processedBackend
            .filter(Boolean)
            .sort(() => Math.random() - 0.5)
            .slice(0, 4);
          let combined = [...firstTmdb, ...backendPicks];

          // If we still have < 8, take additional TMDB picks (excluding already used)
          if (combined.length < 8) {
            const remainingTmdb = tmdbProcessed.slice(4).filter(it => !combined.some((c: any) => c && c.id === it.id));
            combined = [...combined, ...remainingTmdb.slice(0, 8 - combined.length)];
          }

          // Final fallback: if still empty, use trending week
          if (combined.length === 0) {
            try {
              const trending = await fetchTrendingWeek();
              combined = trending.slice(0, 8).map((item: any) => ({
                id: item.id,
                title: item.title,
                imageUrl: item.posterUrl,
                year: item.releaseDate?.substring(0,4),
                rating: item.rating,
                provider: item.provider,
              }));
            } catch {
              combined = [];
            }
          }

          setExtraRecs(combined);
        } catch (e) {
          setExtraRecs([]);
        } finally {
          setExtraLoading(false);
        }
      })();
    } else if (!isOpen || inputValue.length > 0) {
      setExtraRecs([]);
    }
  }, [isOpen, user, inputValue]);

  if (!isOpen) return null;
  
  const shouldShowResults = inputValue.length >= 2;
  const hasResults = searchResults.length > 0;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex flex-col items-center overflow-auto"
      aria-modal="true"
      role="dialog"
    >
      {partyMode ? (
        <WatchPartyBox>
          {/* Search Input */}
          <div className="w-full max-w-2xl mx-auto animate-in fade-in slide-in-from-top duration-300">
            <div className="h-12 flex items-center px-4 gap-3 bg-black/30 backdrop-blur-xl rounded-xl border border-white/20 shadow-[0_0_15px_rgba(255,255,255,0.15)] hover:shadow-[0_0_20px_rgba(255,255,255,0.2)] transition-all duration-300">
              <Search className="text-white/90" size={24} />
              <input
                ref={inputRef}
                type="text"
                placeholder="Search for movies or TV shows..."
                className="flex-grow bg-transparent outline-none text-white placeholder:text-white/60 text-base caret-white focus:ring-0"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                autoFocus
              />
              {inputValue && (
                <button
                  onClick={() => setInputValue('')}
                  className="text-white/70 hover:text-white transition-colors"
                >
                  <X size={18} />
                </button>
              )}
              <Image
                src="/assets/alexa.png"
                alt="Alexa"
                width={24}
                height={24}
                className="opacity-80 hover:opacity-100 transition-opacity duration-300"
              />
            </div>
          </div>

          {/* Main Scrollable Area */}
          {shouldShowResults ? (
            <ScrollArea className="w-full flex-grow mt-6 pb-6 overflow-auto">
              <div className="w-full mx-auto">
                {loading ? (
                  <div className="flex items-center justify-center h-40">
                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary"></div>
                  </div>
                ) : hasResults ? (
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-8 px-6 py-4">
                    {searchResults.map((item, index) => (
                      <div
                        key={`${item.id}-${index}`}
                        className={`transform transition-all duration-200 ${
                          selectedIndex === index
                            ? 'scale-105'
                            : 'hover:scale-[1.02]'
                        }`}
                        onMouseEnter={() => setSelectedIndex(index)}
                      >
                        <ContentCard
                          id={item.id}
                          title={item.title}
                          imageUrl={item.posterUrl}
                          year={item.releaseDate?.substring(0, 4)}
                          rating={item.rating?.toFixed(1)}
                          source={item.provider}
                          className={selectedIndex === index ? 'ring-2 ring-blue-500' : ''}
                          onClick={() => {
                            if (onSelectMovie) {
                              onSelectMovie(item.id);
                              onClose();
                            } else {
                              router.push(`/movie/${item.id}${partyMode ? '?party=1' : ''}`);
                              onClose();
                            }
                          }}
                        />
                      </div>
                    ))}
                  </div>
                ) : hasSearched ? (
                  <div className="flex flex-col items-center justify-center h-40 text-center mt-10">
                    <div className="text-white text-xl mb-2">No results found</div>
                    <div className="text-gray-400">
                      Try different keywords or check the spelling
                    </div>
                    <div className="text-gray-500 text-sm mt-2">
                      Note: Only movies and shows with poster images and ratings are displayed
                    </div>
                  </div>
                ) : null}
              </div>
            </ScrollArea>
          ) : (
            /* Show extra recommendations when search is empty */
            <ScrollArea className="w-full flex-grow mt-6 pb-6 overflow-auto">
              <div className="w-full mx-auto">
                {extraLoading ? (
                  <div className="flex items-center justify-center h-40">
                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary"></div>
                  </div>
                ) : extraRecs.length > 0 ? (
                  <>
                    <div className="text-white text-lg mb-4">Recommended for you</div>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-8 px-6 py-4">
                      {extraRecs.map((item, index) => (
                        <ContentCard
                          key={`extra-rec-${item.id}-${index}`}
                          id={item.id}
                          title={item.title}
                          imageUrl={item.imageUrl}
                          year={item.year}
                          rating={typeof item.rating === 'number' ? item.rating.toFixed(1) : '0.0'}
                          source={item.provider}
                          onClick={() => {
                            if (onSelectMovie) {
                              onSelectMovie(item.id);
                              onClose();
                            } else {
                              router.push(`/movie/${item.id}${partyMode ? '?party=1' : ''}`);
                              onClose();
                            }
                          }}
                        />
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="flex flex-col items-center justify-center h-40 text-center mt-10">
                    <div className="text-white text-xl mb-2">No recommendations found</div>
                    <div className="text-gray-400">
                      Try searching for something or check your profile
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
          )}
        </WatchPartyBox>
      ) : (
        /* ===== Normal overlay content (non-party mode) ===== */
        <>
      {/* Search Input at the top */}
      <div className="w-[90%] max-w-2xl mt-24 animate-in fade-in slide-in-from-top duration-300">
        <div className="h-12 flex items-center px-4 gap-3 bg-black/30 backdrop-blur-xl rounded-xl border border-white/20 shadow-[0_0_15px_rgba(255,255,255,0.15)] hover:shadow-[0_0_20px_rgba(255,255,255,0.2)] transition-all duration-300">
          <Search className="text-white/90" size={24} />
          
          <input
            ref={inputRef}
            type="text"
            placeholder="Search for movies or TV shows..."
            className="flex-grow bg-transparent outline-none text-white placeholder:text-white/60 text-base caret-white focus:ring-0"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            autoFocus
          />
          
          {inputValue && (
            <button 
              onClick={() => setInputValue('')}
              className="text-white/70 hover:text-white transition-colors"
            >
              <X size={18} />
            </button>
          )}

          <Image 
            src="/assets/alexa.png" 
            alt="Alexa" 
            width={24} 
            height={24} 
            className="opacity-80 hover:opacity-100 transition-opacity duration-300"
          />
        </div>
      </div>

      {/* Main Scrollable Area */}
      {shouldShowResults ? (
        <ScrollArea className="w-full flex-grow mt-6 px-6 pb-10 overflow-auto">
          <div className="w-[90%] max-w-5xl mx-auto">
            {loading ? (
              <div className="flex items-center justify-center h-40">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary"></div>
              </div>
            ) : hasResults ? (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-8 px-6 py-4">
                {searchResults.map((item, index) => (
                  <div
                    key={`${item.id}-${index}`}
                    className={`transform transition-all duration-200 ${
                      selectedIndex === index
                        ? 'scale-105'
                        : 'hover:scale-[1.02]'
                    }`}
                    onMouseEnter={() => setSelectedIndex(index)}
                  >
                    <ContentCard
                      id={item.id}
                      title={item.title}
                      imageUrl={item.posterUrl}
                      year={item.releaseDate?.substring(0, 4)}
                      rating={item.rating?.toFixed(1)}
                      source={item.provider}
                      className={selectedIndex === index ? 'ring-2 ring-blue-500' : ''}
                      onClick={() => {
                        if (onSelectMovie) {
                          onSelectMovie(item.id);
                          onClose();
                        } else {
                        router.push(`/movie/${item.id}${partyMode ? '?party=1' : ''}`);
                        onClose();
                        }
                      }}
                    />
                  </div>
                ))}
              </div>
            ) : hasSearched ? (
              <div className="flex flex-col items-center justify-center h-40 text-center mt-10">
                <div className="text-white text-xl mb-2">No results found</div>
                <div className="text-gray-400">
                  Try different keywords or check the spelling
                </div>
                <div className="text-gray-500 text-sm mt-2">
                  Note: Only movies and shows with poster images and ratings are displayed
                </div>
              </div>
            ) : null}
          </div>
        </ScrollArea>
      ) : (
            /* Show extra recommendations when search is empty */
        <ScrollArea className="w-full flex-grow mt-6 px-6 pb-10 overflow-auto">
          <div className="w-[90%] max-w-5xl mx-auto">
            {extraLoading ? (
              <div className="flex items-center justify-center h-40">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary"></div>
              </div>
            ) : extraRecs.length > 0 ? (
              <>
                <div className="text-white text-lg mb-4">Recommended for you</div>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8 px-6 py-4">
                  {extraRecs.map((item, index) => (
                    <ContentCard
                      key={`extra-rec-${item.id}-${index}`}
                      id={item.id}
                      title={item.title}
                      imageUrl={item.imageUrl}
                      year={item.year}
                      rating={typeof item.rating === 'number' ? item.rating.toFixed(1) : '0.0'}
                      source={item.provider}
                      onClick={() => {
                        if (onSelectMovie) {
                          onSelectMovie(item.id);
                          onClose();
                        } else {
                        router.push(`/movie/${item.id}${partyMode ? '?party=1' : ''}`);
                        onClose();
                        }
                      }}
                    />
                  ))}
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-40 text-center mt-10">
                <div className="text-white text-xl mb-2">No recommendations found</div>
                <div className="text-gray-400">
                  Try searching for something or check your profile
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
          )}
        </>
      )}
    </div>
  );
} 