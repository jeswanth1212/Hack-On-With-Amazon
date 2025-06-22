'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Play, Pause, Volume2, VolumeX, Maximize2, Clapperboard, Video, Mic, MicOff, VideoOff } from 'lucide-react';
import SearchOverlay from '@/components/ui/SearchOverlay';
import { useAuth } from '@/lib/hooks';
import { RECOMMENDATION_API_URL } from '@/lib/utils';

interface Participant {
  id: string;
  joined: boolean;
}

export default function WatchPartySession() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const partyIdParam = searchParams.get('party');
  const partyId = partyIdParam ? parseInt(partyIdParam) : null;
  const initialTmdbId = searchParams.get('tmdb') ? parseInt(searchParams.get('tmdb') as string) : null;
  const [tmdbId, setTmdbId] = useState<number | null>(initialTmdbId);
  const [searchOpen, setSearchOpen] = useState(false);

  const friendsParam = searchParams.get('friends');
  const friendsList = friendsParam ? friendsParam.split(',') : [];

  const [participants, setParticipants] = useState<Participant[]>([]);
  const [playing, setPlaying] = useState(true);
  const [muted, setMuted] = useState(false);
  const [showOverlay, setShowOverlay] = useState(false);

  useEffect(() => {
    // Initialize participant list (self + friends)
    const selfId = 'you'; // replace later with auth user id
    const initial: Participant[] = [
      { id: selfId, joined: true },
      ...friendsList.map((fr) => ({ id: fr, joined: false })),
    ];
    setParticipants(initial);
  }, [friendsParam]);

  // Poll party status
  useEffect(() => {
    if (!partyId) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${RECOMMENDATION_API_URL}/watchparty/details/${partyId}`);
        if (!res.ok) throw new Error('Failed');
        const data = await res.json();
        if (data.status === 'ended') {
          router.push('/');
        }
        if (tmdbId === null && data.tmdb_id) setTmdbId(data.tmdb_id);
      } catch {}
    }, 5000);
    return () => clearInterval(interval);
  }, [partyId, tmdbId]);

  return (
    <div className="flex h-screen w-full bg-black">
      {/* Video area */}
      <div className="flex-1 bg-black relative flex flex-col items-center justify-center">
        {/* Placeholder poster or video */}
        <div className="w-full h-full px-8 py-8">
          <div className="w-full h-full bg-gray-800 rounded-xl flex items-center justify-center relative overflow-hidden">
            <Clapperboard size={64} className="text-yellow-500" />
            {showOverlay && (
              <div className="absolute inset-0 bg-black/70 flex items-center justify-center text-white text-2xl">
                Video placeholder
              </div>
            )}
          </div>
        </div>

        {/* Controls */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-6 bg-black/60 px-6 py-3 rounded-full shadow-lg backdrop-blur-md">
          <button onClick={() => setPlaying((p) => !p)} className="text-white hover:text-yellow-400 transition">
            {playing ? <Pause size={28} /> : <Play size={28} />}
          </button>
          <button onClick={() => setMuted((m) => !m)} className="text-white hover:text-yellow-400 transition">
            {muted ? <VolumeX size={24} /> : <Volume2 size={24} />}
          </button>
          <button className="text-white hover:text-yellow-400 transition">
            <Maximize2 size={22} />
          </button>
          <button onClick={() => setSearchOpen(true)} className="ml-4 text-white hover:text-yellow-400 transition flex items-center gap-2 text-sm font-medium">
            <Clapperboard size={20} /> Change Movie
          </button>
          <button onClick={async () => {
            if (partyId) {
              await fetch(`${RECOMMENDATION_API_URL}/watchparty/end?party_id=${partyId}`, { method: 'POST' });
            }
            router.push('/');
          }} className="ml-2 text-red-400 hover:text-red-300 transition flex items-center gap-1 text-sm font-medium">
            End Session
          </button>
        </div>
      </div>

      {/* Participants panel */}
      <div className="w-80 bg-gray-900 border-l border-yellow-400 flex flex-col p-4 overflow-auto">
        <h3 className="text-yellow-400 text-lg font-bold mb-4">Participants</h3>
        <div className="flex flex-col gap-4">
          {participants.map((p) => (
            <div key={p.id} className="bg-black/50 rounded-lg p-3 flex items-center gap-3 border border-white/10">
              <div className="w-16 h-12 bg-gray-700 rounded-md flex items-center justify-center text-gray-400 text-sm">
                {p.joined ? <Video size={24} /> : '?'}
              </div>
              <div className="flex-1 text-white text-sm font-medium">
                {p.id === 'you' ? 'You' : p.id}
                <div className="text-xs text-gray-400">
                  {p.joined ? 'In party' : 'Waiting...'}
                </div>
              </div>
              {p.id === 'you' && (
                <div className="flex items-center gap-2">
                  <button onClick={() => setMuted((m) => !m)} className="text-white hover:text-yellow-400 transition">
                    {muted ? <MicOff size={18} /> : <Mic size={18} />}
                  </button>
                  <button className="text-white hover:text-yellow-400 transition">
                    <VideoOff size={18} />
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {searchOpen && (
        <SearchOverlay
          isOpen={searchOpen}
          onClose={() => setSearchOpen(false)}
          partyMode
          onSelectMovie={(id) => {
            const redirect = `/movie/${id}?party=1&session=1&friends=${encodeURIComponent(friendsParam ?? '')}`;
            router.push(redirect);
          }}
        />
      )}
    </div>
  );
} 