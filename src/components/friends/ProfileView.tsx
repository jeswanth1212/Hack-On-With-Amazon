'use client';

import { useEffect, useMemo, useState } from 'react';
import { getUserHistory } from '@/lib/utils';
import { useAuth } from '@/lib/hooks';
import { Badge } from '@/components/ui/badge';
import ContentCarousel from '@/components/ui/ContentCarousel';
import { cn } from '@/lib/utils';

interface DayCell {
  date: string; // YYYY-MM-DD
  count: number;
}

// Five shades of yellow (plus one for "no data" which will be transparent / gray)
const COLOR_SCALE = [
  'transparent', // 0 – no activity
  '#FFFDE7',     // level 1 (lightest)
  '#FFF176',     // level 2
  '#FFC107',     // level 3
  '#FFA000',     // level 4 (darkest)
];

function getDateString(date: Date) {
  return date.toISOString().slice(0, 10); // YYYY-MM-DD
}

// Deterministic seeded random generator for per-user mock data
function seededRand(seed: number) {
  return () => {
    seed = (seed * 1664525 + 1013904223) % 4294967296;
    return seed / 4294967296;
  };
}

// Helper functions to fetch TMDB IDs and poster images (simplified)
async function fetchTmdbId(title: string, year?: number) {
  const apiKey = 'ee41666274420bb7514d6f2f779b5fd9';
  const query = encodeURIComponent(title);
  let url = `https://api.themoviedb.org/3/search/movie?api_key=${apiKey}&query=${query}`;
  if (year) url += `&year=${year}`;
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    const data = await res.json();
    if (data.results && data.results.length > 0) return data.results[0].id;
  } catch {}
  return null;
}

async function fetchTmdbImages(title: string, year?: number) {
  const apiKey = 'ee41666274420bb7514d6f2f779b5fd9';
  const query = encodeURIComponent(title);
  let url = `https://api.themoviedb.org/3/search/multi?api_key=${apiKey}&language=en-US&query=${query}&page=1&include_adult=false`;
  if (year) url += `&year=${year}`;
  try {
    const res = await fetch(url);
    if (!res.ok) return { poster: null };
    const data = await res.json();
    const result = data.results && data.results.length > 0 ? data.results[0] : null;
    return {
      poster: result && result.poster_path ? `https://image.tmdb.org/t/p/w500${result.poster_path}` : null,
    };
  } catch {}
  return { poster: null };
}

export default function ProfileView() {
  const { user } = useAuth();
  const [recent, setRecent] = useState<any[]>([]); // last 5 real interactions enriched
  const [loading, setLoading] = useState(false);

  // Fetch recent (real) history and enrich with TMDB posters
  useEffect(() => {
    const fetchRecent = async () => {
      if (!user) return;
      setLoading(true);
      try {
        const data = await getUserHistory(user.user_id, 5);
        const enrichedRaw = await Promise.all(
          data.map(async (it: any) => {
            const tmdbId = await fetchTmdbId(it.title, it.release_year);
            const images = await fetchTmdbImages(it.title, it.release_year);
            return {
              id: tmdbId || it.item_id,
              title: it.title,
              posterUrl: images.poster || '/placeholder.jpg',
              releaseDate: it.release_year ? `${it.release_year}-01-01` : undefined,
              rating: it.sentiment_score ? (it.sentiment_score * 10).toFixed(1) : undefined,
            };
          })
        );
        // Deduplicate by TMDB id/title
        const seen = new Set<string>();
        const unique: any[] = [];
        for (const item of enrichedRaw) {
          const key = String(item.id ?? item.title);
          if (!seen.has(key)) {
            seen.add(key);
            unique.push(item);
          }
        }
        setRecent(unique.slice(0, 5));
      } catch (e) {
        setRecent([]);
      } finally {
        setLoading(false);
      }
    };
    fetchRecent();
  }, [user]);

  // Generate deterministic mock daily counts for badges & heatmap
  const dateCounts = useMemo(() => {
    if (!user) return new Map<string, number>();
    const rand = seededRand(
      Array.from(user.user_id).reduce((sum, ch) => sum + ch.charCodeAt(0), 0)
    );
    const map = new Map<string, number>();
    const today = new Date();
    for (let i = 0; i < 365; i++) {
      const d = new Date(today);
      d.setDate(today.getDate() - i);
      const ds = getDateString(d);
      // Random 0-3 with bias: 50% zero, else 1-3
      const r = rand();
      let count = 0;
      if (r > 0.5) {
        count = 1 + Math.floor(rand() * 3);
      }
      map.set(ds, count);
    }
    return map;
  }, [user]);

  // Build day cells for the last 1 year (inclusive of today)
  const days: DayCell[] = useMemo(() => {
    const cells: DayCell[] = [];
    const today = new Date();
    const pastYear = new Date();
    pastYear.setFullYear(today.getFullYear() - 1);
    for (let d = new Date(pastYear); d <= today; d.setDate(d.getDate() + 1)) {
      const ds = getDateString(d);
      cells.push({ date: ds, count: dateCounts.get(ds) || 0 });
    }
    return cells;
  }, [dateCounts]);

  // Compute stats
  const totalWatched = Array.from(dateCounts.values()).reduce((a, b) => a + b, 0);
  const activeDays = Array.from(dateCounts.values()).filter((c) => c > 0).length;

  // Streaks
  const { currentStreak, maxStreak } = useMemo(() => {
    let cur = 0;
    let max = 0;
    for (let i = days.length - 1; i >= 0; i--) {
      if (days[i].count > 0) {
        cur++;
      } else {
        if (cur > 0) break; // break for current streak calc
      }
    }
    let running = 0;
    days.forEach((d) => {
      if (d.count > 0) {
        running++;
        if (running > max) max = running;
      } else {
        running = 0;
      }
    });
    return { currentStreak: cur, maxStreak: max };
  }, [days]);

  // Determine levels relative to max daily count (ignore zeros)
  const maxCount = Math.max(...days.map((d) => d.count));
  function getLevel(count: number) {
    if (count === 0) return 0;
    if (maxCount <= 4) return Math.min(count, 4); // if counts small, map directly
    const ratio = count / maxCount;
    if (ratio > 0.75) return 4;
    if (ratio > 0.5) return 3;
    if (ratio > 0.25) return 2;
    return 1;
  }

  // Organise by weeks (each column is a week starting Sunday)
  const weeks: DayCell[][] = [];
  let week: DayCell[] = [];
  days.forEach((day) => {
    const date = new Date(day.date);
    if (date.getDay() === 0 && week.length) {
      // Start of a new week (Sunday)
      // Push previous week (ensure 7 cells)
      while (week.length < 7) week.push({ date: '', count: 0 });
      weeks.push(week);
      week = [];
    }
    week.push(day);
  });
  // Push last week
  while (week.length < 7) week.push({ date: '', count: 0 });
  weeks.push(week);

  // Month labels based on first week cell
  interface LabelInfo { index: number; name: string; }

  const { monthLabels, weekOffsetPx, totalWidth } = useMemo(() => {
    const labels: LabelInfo[] = [];
    const offsets: number[] = [];
    let lastMonth = -1;
    let extraPx = 0;
    weeks.forEach((wk, idx) => {
      const dayCell = wk[0];
      if (!dayCell || !dayCell.date) {
        offsets[idx] = extraPx;
        return;
      }
      const month = new Date(dayCell.date).getMonth();
      if (month !== lastMonth) {
        if (idx !== 0) {
          // add 4px gap before this week to separate months
          extraPx += 4;
        }
        labels.push({ index: idx, name: new Date(dayCell.date).toLocaleString('default', { month: 'short' }) });
        lastMonth = month;
      }
      offsets[idx] = extraPx;
    });
    const width = weeks.length * 14 + extraPx;
    return { monthLabels: labels, weekOffsetPx: offsets, totalWidth: width };
  }, [weeks]);

  // ------------------ Achievement Badges ------------------
  interface Achievement {
    id: string;
    label: string;
    value: number;
    color: string; // background color
  }

  const achievements: Achievement[] = useMemo(() => {
    const list: Achievement[] = [];
    // Total watched thresholds
    const watchedThresholds = [25, 50, 100, 250, 500];
    watchedThresholds.forEach((t) => {
      if (totalWatched >= t) list.push({ id: `watched-${t}`, label: `${t} MOV`, value: t, color: '#38bdf8' });
    });
    // Active days thresholds
    const activeThresholds = [5, 25, 50, 100, 200];
    activeThresholds.forEach((t) => {
      if (activeDays >= t) list.push({ id: `days-${t}`, label: `${t} DAYS`, value: t, color: '#a3e635' });
    });
    // Streak thresholds
    const streakThresholds = [5, 10, 25, 50];
    streakThresholds.forEach((t) => {
      if (maxStreak >= t) list.push({ id: `streak-${t}`, label: `${t} STREAK`, value: t, color: '#facc15' });
    });
    return list;
  }, [totalWatched, activeDays, maxStreak]);

  const mostRecentBadge = achievements[achievements.length - 1];

  // Hexagon badge component
  const HexBadge = ({ label, color }: { label: string; color: string }) => (
    <div
      className="relative w-16 h-18 flex items-center justify-center text-[10px] font-bold text-black select-none"
      style={{ clipPath: 'polygon(25% 3%, 75% 3%, 100% 50%, 75% 97%, 25% 97%, 0% 50%)', backgroundColor: color }}
    >
      <span className="px-1 text-center leading-tight uppercase">{label}</span>
    </div>
  );

  return (
    <div className="py-6">
      {loading ? (
        <div className="flex justify-center items-center h-32">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary"></div>
        </div>
      ) : !user ? (
        <div className="text-center text-muted-foreground">Please log in to view your profile.</div>
      ) : (
        <>
          {/* Achievement Badges */}
          {achievements.length > 0 && (
            <div className="mb-6 p-4 rounded-lg border border-gray-700 bg-background/60 w-full px-8">
              <h3 className="text-lg font-semibold mb-2 text-white">Badges <span className="text-primary">{achievements.length}</span></h3>
              <div className="flex items-center gap-4 overflow-x-auto py-2">
                {achievements.map((b) => (
                  <HexBadge key={b.id} label={b.label} color={b.color} />
                ))}
              </div>
              {mostRecentBadge && (
                <p className="mt-2 text-sm text-muted-foreground">Most Recent Badge: <span className="font-medium text-white">{mostRecentBadge.label}</span></p>
              )}
            </div>
          )}

          {/* Stat Pills (centered) */}
          <div className="flex flex-wrap gap-4 mb-6 justify-center w-full px-8">
            <Badge>Total Watched&nbsp;&nbsp;{totalWatched}</Badge>
            <Badge>Active Days&nbsp;&nbsp;{activeDays}</Badge>
            <Badge>Current Streak&nbsp;&nbsp;{currentStreak}</Badge>
            <Badge>Max Streak&nbsp;&nbsp;{maxStreak}</Badge>
          </div>

          {/* Heatmap (SVG) */}
          <div className="overflow-x-auto px-8 flex justify-center">
            <svg
              width={totalWidth}
              height={7 * 14 + 20}
              className="block"
            >
              {/* Month labels */}
              {monthLabels.map((m) => (
                <text
                  key={m.index}
                  x={m.index * 14 + weekOffsetPx[m.index]}
                  y={10}
                  fontSize={10}
                  fill="#888"
                >
                  {m.name}
                </text>
              ))}

              {/* Day squares */}
              {weeks.map((w, weekIdx) => (
                w.map((d, dayIdx) => {
                  const color = COLOR_SCALE[getLevel(d.count)];
                  return (
                    <rect
                      key={`${weekIdx}-${dayIdx}`}
                      x={weekIdx * 14 + weekOffsetPx[weekIdx]}
                      y={dayIdx * 14 + 14}
                      width={10}
                      height={10}
                      rx={2}
                      ry={2}
                      fill={color}
                      stroke="#2a2a2a"
                      strokeWidth={color === 'transparent' ? 0.5 : 0}
                    >
                      <title>{`${d.date || 'N/A'}: ${d.count} movie(s)`}</title>
                    </rect>
                  );
                })
              ))}
            </svg>
          </div>

          {/* Recently watched */}
          {recent.length > 0 && (
            <div className="mt-8">
              <ContentCarousel title="Recently Watched" items={recent} slidesToShow={5} />
            </div>
          )}
        </>
      )}
    </div>
  );
} 