'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import { useEffect, useState, useRef, useCallback } from 'react';
import { Play, Pause, Volume2, VolumeX, Maximize2, Clapperboard, Video, Mic, MicOff, VideoOff, Camera, RefreshCcw } from 'lucide-react';
import SearchOverlay from '@/components/ui/SearchOverlay';
import { useAuth } from '@/lib/hooks';
import { RECOMMENDATION_API_URL } from '@/lib/utils';
import { connectSocket, joinWatchParty, leaveWatchParty, updateVideoState, initUserMedia, toggleVideo, toggleAudio, cleanupMedia } from '@/lib/socket';

interface Participant {
  sid: string;
  user_id: string;
  username: string;
  joined: boolean;
  hasVideo: boolean;
  hasMic: boolean;
  stream?: MediaStream;
}

interface PartyResponse {
  success: boolean;
  participants: {
    sid: string;
    user_id: string;
    username: string;
  }[];
  video_state: {
    playing: boolean;
    currentTime: number;
    tmdbId?: number;
  };
}

export default function WatchPartySession() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user } = useAuth();
  
  const partyIdParam = searchParams.get('party');
  const partyId = partyIdParam ? parseInt(partyIdParam) : null;
  const initialTmdbId = searchParams.get('tmdb') ? parseInt(searchParams.get('tmdb') as string) : null;
  const [tmdbId, setTmdbId] = useState<number | null>(initialTmdbId);
  const [searchOpen, setSearchOpen] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [debugMode, setDebugMode] = useState(false);

  const friendsParam = searchParams.get('friends');
  const friendsList = friendsParam ? friendsParam.split(',') : [];

  const [participants, setParticipants] = useState<Participant[]>([]);
  const [playing, setPlaying] = useState(true);
  const [muted, setMuted] = useState(false);
  const [videoEnabled, setVideoEnabled] = useState(true);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [showOverlay, setShowOverlay] = useState(false);
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);

  // Video refs
  const videoPlayerRef = useRef<HTMLVideoElement>(null);
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const peerVideoRefs = useRef<Record<string, HTMLVideoElement | null>>({});

  // Set video ref callback
  const setPeerVideoRef = useCallback((sid: string, el: HTMLVideoElement | null) => {
    console.log(`Setting video ref for participant ${sid}`, el ? 'element exists' : 'element is null');
    peerVideoRefs.current[sid] = el;
    
    // If we already have a stream for this participant, set it
    const participant = participants.find(p => p.sid === sid);
    if (el && participant?.stream) {
      console.log(`Setting stream for participant ${sid}`);
      el.srcObject = participant.stream;
    }
  }, [participants]);

  // Initialize socket connection
  useEffect(() => {
    if (!partyId) return;
    
    try {
      const socket = connectSocket();

      // Listen for participant streams
      const handleStreamReceived = (event: Event) => {
        const { peerID, stream } = (event as CustomEvent).detail;
        
        console.log(`Received stream from peer ${peerID}`, stream);
        setConnectionStatus('connected');
        
        setParticipants(prev => {
          const updated = prev.map(p => {
            if (p.sid === peerID) {
              // If we have a video ref for this peer, set the stream
              const videoEl = peerVideoRefs.current[peerID];
              if (videoEl) {
                console.log(`Setting stream for video element of peer ${peerID}`);
                videoEl.srcObject = stream;
              } else {
                console.log(`No video element for peer ${peerID} yet`);
              }
              
              return { ...p, stream, hasVideo: true };
            }
            return p;
          });
          return updated;
        });
      };

      // Add event listener for stream received
      window.addEventListener('stream-received', handleStreamReceived);

      // Listen for socket connection errors
      socket.on('connect_error', (err) => {
        console.error('Socket connection error:', err);
        setConnectionStatus('error');
        setErrorMessage(`Connection error: ${err.message}. Check console for details.`);
      });

      // Listen for socket disconnection
      socket.on('disconnect', (reason) => {
        console.log('Socket disconnected:', reason);
        if (reason === 'io server disconnect') {
          setConnectionStatus('error');
          setErrorMessage('Disconnected by server. Please refresh the page.');
        } else if (reason === 'transport close') {
          setConnectionStatus('error');
          setErrorMessage('Connection closed. Please check your internet connection.');
        }
      });

      // Listen for video state changes
      socket.on('video_state_updated', ({ state }) => {
        if (videoPlayerRef.current) {
          if (state.playing !== undefined) {
            setPlaying(state.playing);
            if (state.playing) {
              videoPlayerRef.current.play().catch(err => console.error('Error playing video:', err));
            } else {
              videoPlayerRef.current.pause();
            }
          }

          if (state.currentTime !== undefined) {
            videoPlayerRef.current.currentTime = state.currentTime;
          }
          
          if (state.tmdbId !== undefined && state.tmdbId !== tmdbId) {
            setTmdbId(state.tmdbId);
          }
        }
      });

      return () => {
        window.removeEventListener('stream-received', handleStreamReceived);
        if (partyId) {
          leaveWatchParty(partyId, user?.user_id || 'guest')
            .catch(err => console.error('Error leaving watch party:', err));
          cleanupMedia();
        }
      };
    } catch (error) {
      console.error('Error setting up socket connection:', error);
      setConnectionStatus('error');
      setErrorMessage(`Failed to set up connection: ${error instanceof Error ? error.message : 'Unknown error'}`);
      return () => {};
    }
  }, [partyId, user, tmdbId]);

  // Initialize user media
  useEffect(() => {
    if (!partyId || !user) return;
    
    setConnectionStatus('connecting');

    const setupMedia = async () => {
      try {
        console.log('Initializing user media...');
        const stream = await initUserMedia({ video: true, audio: true });
        setLocalStream(stream);

        // Set the local video element's srcObject to the stream
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream;
        }
        
        console.log('User media initialized successfully');
      } catch (error) {
        console.error('Error initializing media:', error);
        // Still join the party even if media access failed
        setVideoEnabled(false);
        setAudioEnabled(false);
        setErrorMessage('Could not access camera/microphone. You will join with audio/video disabled.');
      }
      
      // Join the watch party
      try {
        console.log(`Joining watch party ${partyId} as ${user.user_id}...`);
        const result = await joinWatchParty(
          partyId, 
          user.user_id,
          user.user_id // using user_id as username for simplicity
        ) as PartyResponse;
        
        // Initialize participants from the result
        const partyParticipants = result.participants.map((p) => ({
          sid: p.sid,
          user_id: p.user_id,
          username: p.username,
          joined: true,
          hasVideo: false,
          hasMic: true
        }));
        
        setParticipants(partyParticipants);
        console.log('Joined party with participants:', partyParticipants);
        
        // Set video state if provided
        if (result.video_state) {
          if (result.video_state.tmdbId) {
            setTmdbId(result.video_state.tmdbId);
          }
          setPlaying(result.video_state.playing);
        }
      } catch (error) {
        console.error('Error joining watch party:', error);
        setConnectionStatus('error');
        setErrorMessage(`Failed to join watch party: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    };

    setupMedia();
  }, [partyId, user]);

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
  }, [partyId, tmdbId, router]);

  // Handle video play/pause
  const handlePlayPause = () => {
    if (!videoPlayerRef.current || !partyId) return;
    
    const newPlaying = !playing;
    setPlaying(newPlaying);
    
    if (newPlaying) {
      videoPlayerRef.current.play().catch(err => console.error('Error playing video:', err));
    } else {
      videoPlayerRef.current.pause();
    }
    
    updateVideoState(partyId, { playing: newPlaying });
  };

  // Handle video seeking
  const handleSeek = (e: React.SyntheticEvent<HTMLVideoElement>) => {
    if (!videoPlayerRef.current || !partyId) return;
    
    updateVideoState(partyId, { currentTime: videoPlayerRef.current.currentTime });
  };

  // Handle video muting
  const handleMute = () => {
    if (!videoPlayerRef.current) return;
    
    const newMuted = !muted;
    setMuted(newMuted);
    videoPlayerRef.current.muted = newMuted;
  };

  // Toggle user video
  const handleToggleVideo = async () => {
    const newVideoState = !videoEnabled;
    setVideoEnabled(newVideoState);
    await toggleVideo(newVideoState);
  };

  // Toggle user audio
  const handleToggleAudio = async () => {
    const newAudioState = !audioEnabled;
    setAudioEnabled(newAudioState);
    await toggleAudio(newAudioState);
  };

  // Reconnect handler
  const handleReconnect = async () => {
    setConnectionStatus('connecting');
    setErrorMessage(null);
    
    // Clean up existing connections
    cleanupMedia();
    
    // Wait a bit before reconnecting
    setTimeout(() => {
      // Re-initialize everything
      if (partyId && user) {
        const setupMedia = async () => {
          try {
            const stream = await initUserMedia({ video: true, audio: true });
            setLocalStream(stream);
            setVideoEnabled(true);
            setAudioEnabled(true);

            if (localVideoRef.current) {
              localVideoRef.current.srcObject = stream;
            }
            
            const result = await joinWatchParty(partyId, user.user_id, user.user_id) as PartyResponse;
            setParticipants(result.participants.map((p) => ({
              sid: p.sid,
              user_id: p.user_id,
              username: p.username,
              joined: true,
              hasVideo: false,
              hasMic: true
            })));
            
            if (result.video_state?.tmdbId) {
              setTmdbId(result.video_state.tmdbId);
            }
          } catch (error) {
            console.error('Error reconnecting:', error);
            setConnectionStatus('error');
            setErrorMessage(`Failed to reconnect: ${error instanceof Error ? error.message : 'Unknown error'}`);
          }
        };
        
        setupMedia();
      }
    }, 1000);
  };

  return (
    <div className="flex h-screen w-full bg-black">
      {/* Main video area */}
      <div className="flex-1 bg-black relative flex flex-col items-center justify-center">
        {/* Video player */}
        <div className="w-full h-full px-8 py-8">
          <div className="w-full h-full bg-gray-800 rounded-xl flex items-center justify-center relative overflow-hidden">
            {tmdbId ? (
              <video
                ref={videoPlayerRef}
                className="w-full h-full object-contain"
                controls={false}
                autoPlay={playing}
                muted={muted}
                onPlay={() => setPlaying(true)}
                onPause={() => setPlaying(false)}
                onSeeked={handleSeek}
              >
                <source src={`/api/video/${tmdbId}`} type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            ) : (
              <div className="flex items-center justify-center h-full w-full">
                <Clapperboard size={64} className="text-yellow-500" />
                <p className="text-white text-xl ml-4">Select a movie to watch</p>
              </div>
            )}
            
            {showOverlay && (
              <div className="absolute inset-0 bg-black/70 flex items-center justify-center text-white text-2xl">
                Video placeholder
              </div>
            )}
          </div>
        </div>

        {/* Connection status */}
        {connectionStatus === 'connecting' && (
          <div className="absolute top-6 left-1/2 -translate-x-1/2 bg-yellow-500/80 text-black px-4 py-2 rounded-lg shadow-md">
            Connecting to other participants...
          </div>
        )}

        {connectionStatus === 'error' && (
          <div className="absolute top-6 left-1/2 -translate-x-1/2 bg-red-500/80 text-white px-4 py-2 rounded-lg shadow-md flex items-center gap-2">
            <span>{errorMessage || 'Connection error'}</span>
            <button 
              onClick={handleReconnect} 
              className="bg-white text-red-500 p-1 rounded-full hover:bg-gray-100"
            >
              <RefreshCcw size={16} />
            </button>
          </div>
        )}

        {/* Debug mode toggle */}
        <div className="absolute top-6 right-6">
          <button 
            onClick={() => setDebugMode(!debugMode)} 
            className="text-xs bg-gray-800/60 text-gray-300 px-2 py-1 rounded hover:bg-gray-700/60"
          >
            {debugMode ? 'Hide Debug' : 'Debug'}
          </button>
        </div>

        {/* Debug info */}
        {debugMode && (
          <div className="absolute top-16 right-6 bg-black/80 p-4 rounded-lg text-xs text-white max-w-xs max-h-48 overflow-auto">
            <p>Connection status: {connectionStatus}</p>
            <p>Party ID: {partyId}</p>
            <p>User: {user?.user_id}</p>
            <p>Participants: {participants.length}</p>
            <p>Local media: {localStream ? 'Available' : 'Not available'}</p>
            <p>Camera: {videoEnabled ? 'On' : 'Off'}</p>
            <p>Mic: {audioEnabled ? 'On' : 'Off'}</p>
            <div className="mt-2 border-t border-gray-700 pt-2">
              <p className="font-semibold">Participants:</p>
              {participants.map(p => (
                <div key={p.sid} className="mt-1">
                  <p>{p.username} ({p.sid.substring(0, 6)}...)</p>
                  <p>Stream: {p.stream ? 'Yes' : 'No'}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-6 bg-black/60 px-6 py-3 rounded-full shadow-lg backdrop-blur-md">
          <button onClick={handlePlayPause} className="text-white hover:text-yellow-400 transition">
            {playing ? <Pause size={28} /> : <Play size={28} />}
          </button>
          <button onClick={handleMute} className="text-white hover:text-yellow-400 transition">
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
              await leaveWatchParty(partyId, user?.user_id || 'guest');
              cleanupMedia();
            }
            router.push('/');
          }} className="ml-2 text-red-400 hover:text-red-300 transition flex items-center gap-1 text-sm font-medium">
            End Session
          </button>
        </div>
      </div>

      {/* Participants panel */}
      <div className="w-80 bg-gray-900 border-l border-yellow-400 flex flex-col p-4 overflow-auto">
        <h3 className="text-yellow-400 text-lg font-bold mb-4">Participants ({participants.length})</h3>
        
        {/* Local video/camera */}
        <div className="mb-4 bg-black/50 rounded-lg p-3 border border-white/10">
          <div className="mb-2 text-white text-sm font-medium flex items-center justify-between">
            <span>{user?.user_id || 'You'} (You)</span>
            <div className="flex items-center gap-2">
              <button 
                onClick={handleToggleAudio}
                className={`p-1 rounded-full ${audioEnabled ? 'text-white' : 'text-red-500 bg-black/30'} hover:text-yellow-400 transition`}
              >
                {audioEnabled ? <Mic size={16} /> : <MicOff size={16} />}
              </button>
              <button 
                onClick={handleToggleVideo}
                className={`p-1 rounded-full ${videoEnabled ? 'text-white' : 'text-red-500 bg-black/30'} hover:text-yellow-400 transition`}
              >
                {videoEnabled ? <Camera size={16} /> : <VideoOff size={16} />}
              </button>
            </div>
          </div>
          <div className="w-full h-24 bg-gray-800 rounded-md overflow-hidden">
            {videoEnabled ? (
              <video
                ref={localVideoRef}
                className="w-full h-full object-cover"
                autoPlay
                muted
                playsInline
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <VideoOff size={24} className="text-gray-400" />
              </div>
            )}
          </div>
        </div>
        
        {/* Other participants */}
        <div className="flex flex-col gap-4">
          {participants.filter(p => p.user_id !== user?.user_id).map((p) => (
            <div key={p.sid} className="bg-black/50 rounded-lg p-3 border border-white/10">
              <div className="mb-2 text-white text-sm font-medium flex items-center justify-between">
                <span>{p.username || p.user_id}</span>
                <div className="flex items-center gap-1">
                  {p.hasVideo && <Camera size={14} className="text-green-400" />}
                  {p.hasMic && <Mic size={14} className="text-green-400" />}
                </div>
              </div>
              <div className="w-full h-24 bg-gray-800 rounded-md overflow-hidden">
                {p.stream ? (
                  <video
                    key={`video-${p.sid}`}
                    ref={(el) => setPeerVideoRef(p.sid, el)}
                    className="w-full h-full object-cover"
                    autoPlay
                    playsInline
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <VideoOff size={24} className="text-gray-400" />
                    <span className="text-xs text-gray-500 ml-2">Connecting...</span>
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {participants.filter(p => p.user_id !== user?.user_id).length === 0 && (
            <div className="text-center py-8 text-gray-400 text-sm">
              No other participants yet.<br />Invite friends to join!
            </div>
          )}
        </div>
      </div>

      {searchOpen && (
        <SearchOverlay
          isOpen={searchOpen}
          onClose={() => setSearchOpen(false)}
          partyMode
          onSelectMovie={(id) => {
            setTmdbId(id);
            setSearchOpen(false);
            if (partyId) {
              updateVideoState(partyId, { playing: true, currentTime: 0, tmdbId: id });
            }
          }}
        />
      )}
    </div>
  );
} 