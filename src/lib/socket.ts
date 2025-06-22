import { io, Socket } from 'socket.io-client';
import SimplePeer from 'simple-peer';
import { RECOMMENDATION_API_URL } from './utils';

// Socket.io connection
let socket: Socket | null = null;

// Store for active peer connections
const peers: Record<string, SimplePeer.Instance> = {};

// Store for local media stream
let localStream: MediaStream | null = null;

// Connect to socket server
export const connectSocket = (): Socket => {
  if (!socket) {
    console.log('Connecting to socket server at:', RECOMMENDATION_API_URL);
    
    socket = io(RECOMMENDATION_API_URL, {
      transports: ['websocket', 'polling'],
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000,
      path: '/socket.io/socket.io', // Updated path to match the server side
      forceNew: true,
      autoConnect: true
    });

    // Set up socket event handlers
    socket.on('connect', () => {
      console.log('Connected to socket server with ID:', socket?.id);
    });

    socket.on('connect_error', (err) => {
      console.error('Socket connection error:', err);
      console.log('Connection details:', {
        url: RECOMMENDATION_API_URL,
        transports: ['websocket', 'polling']
      });
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from socket server');
      // Clean up peer connections on disconnect
      Object.values(peers).forEach(peer => peer.destroy());
      Object.keys(peers).forEach(key => delete peers[key]);
    });

    // Handle WebRTC signaling
    socket.on('signal_received', ({ signal, from_sid }: { signal: SimplePeer.SignalData, from_sid: string }) => {
      console.log('Received signal from peer:', from_sid);
      
      // If we already have a peer for this connection, apply the signal
      if (peers[from_sid]) {
        try {
          peers[from_sid].signal(signal);
        } catch (err) {
          console.error('Error applying signal:', err);
        }
      } else {
        // Create a new peer connection as the receiving end
        createPeer(from_sid, false, signal);
      }
    });

    // Handle participant joining
    socket.on('participant_joined', (data) => {
      console.log('New participant joined:', data);
      // If we have a local stream, initiate a new peer connection
      if (localStream && socket?.id !== data.sid) {
        // We're the initiator for this peer connection
        createPeer(data.sid, true);
      }
    });

    // Handle participant leaving
    socket.on('participant_left', (data) => {
      console.log('Participant left:', data);
      // Clean up peer connection
      if (peers[data.sid]) {
        peers[data.sid].destroy();
        delete peers[data.sid];
      }
    });

    // Handle video state updates from other participants
    socket.on('video_state_updated', ({ state }) => {
      console.log('Video state updated:', state);
      // This event will be handled by the component
    });
    
    // Debug logging
    socket.onAny((event, ...args) => {
      console.log(`Socket event: ${event}`, args);
    });
  }

  return socket;
};

// Initialize user media
export const initUserMedia = async (constraints = { video: true, audio: true }): Promise<MediaStream> => {
  try {
    // Get user media
    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    localStream = stream;
    return stream;
  } catch (error) {
    console.error('Error getting user media:', error);
    throw error;
  }
};

// Toggle video track
export const toggleVideo = async (enabled: boolean): Promise<void> => {
  if (!localStream) return;
  
  const videoTracks = localStream.getVideoTracks();
  videoTracks.forEach(track => {
    track.enabled = enabled;
  });
};

// Toggle audio track
export const toggleAudio = async (enabled: boolean): Promise<void> => {
  if (!localStream) return;
  
  const audioTracks = localStream.getAudioTracks();
  audioTracks.forEach(track => {
    track.enabled = enabled;
  });
};

// Create a new peer connection
const createPeer = (peerID: string, isInitiator: boolean, incomingSignal?: SimplePeer.SignalData): SimplePeer.Instance => {
  if (!socket) throw new Error('Socket not connected');
  
  console.log(`Creating peer connection with ${peerID}, initiator: ${isInitiator}`);
  
  try {
    // Create a new simple-peer instance
    const peer = new SimplePeer({
      initiator: isInitiator,
      trickle: true,
      stream: localStream || undefined,
      config: {
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' } // Added public STUN server
        ]
      }
    });

    // Handle signals
    peer.on('signal', (signal) => {
      console.log(`Signal generated for peer ${peerID}:`, signal);
      if (!socket) throw new Error('Socket not connected');
      
      // Use socket to send the signal to remote peer
      socket.emit('send_signal', {
        target_sid: peerID,
        signal,
        party_id: localStorage.getItem('current_party_id'),
      });
    });

    // Handle stream from remote peer
    peer.on('stream', (stream) => {
      console.log(`Stream received from peer ${peerID}`);
      // Create a custom event to pass the stream to the React component
      const event = new CustomEvent('stream-received', { 
        detail: { peerID, stream }
      });
      window.dispatchEvent(event);
    });

    // Handle errors
    peer.on('error', (err) => {
      console.error(`Error in peer connection with ${peerID}:`, err);
      // Clean up the peer connection
      if (peers[peerID]) {
        peers[peerID].destroy();
        delete peers[peerID];
      }
    });

    // Handle peer closing
    peer.on('close', () => {
      console.log(`Peer connection with ${peerID} closed`);
      if (peers[peerID]) {
        delete peers[peerID];
      }
    });

    // If we're receiving a connection, apply the incoming signal
    if (!isInitiator && incomingSignal) {
      console.log(`Applying initial signal for peer ${peerID}`);
      peer.signal(incomingSignal);
    }

    // Store the peer connection
    peers[peerID] = peer;
    
    return peer;
  } catch (error) {
    console.error(`Error creating peer connection with ${peerID}:`, error);
    throw error;
  }
};

// Join a watch party
export const joinWatchParty = async (partyId: number, userId: string, username: string) => {
  if (!socket) throw new Error('Socket not connected');
  
  console.log(`Joining watch party ${partyId} as user ${userId}`);
  
  // Store party ID in local storage for signal routing
  localStorage.setItem('current_party_id', partyId.toString());
  
  return new Promise((resolve, reject) => {
    socket?.emit('join_watch_party', {
      party_id: partyId,
      user_id: userId,
      username
    }, (response: any) => {
      if (response?.success) {
        console.log('Successfully joined watch party:', response);
        resolve(response);
      } else {
        console.error('Failed to join watch party:', response);
        reject(new Error(response?.error || 'Failed to join watch party'));
      }
    });
  });
};

// Leave a watch party
export const leaveWatchParty = async (partyId: number, userId: string) => {
  if (!socket) throw new Error('Socket not connected');
  
  console.log(`Leaving watch party ${partyId}`);
  
  // Remove party ID from local storage
  localStorage.removeItem('current_party_id');
  
  return new Promise((resolve, reject) => {
    socket?.emit('leave_watch_party', {
      party_id: partyId,
      user_id: userId
    }, (response: any) => {
      if (response?.success) {
        console.log('Successfully left watch party');
        resolve(response);
      } else {
        console.error('Failed to leave watch party:', response);
        reject(new Error(response?.error || 'Failed to leave watch party'));
      }
    });
    
    // Clean up all peer connections
    Object.values(peers).forEach(peer => peer.destroy());
    Object.keys(peers).forEach(key => delete peers[key]);
  });
};

// Update video state
export const updateVideoState = (partyId: number, state: { playing?: boolean, currentTime?: number, tmdbId?: number }) => {
  if (!socket) return false;
  
  return new Promise((resolve, reject) => {
    socket?.emit('video_state_change', {
      party_id: partyId,
      state
    }, (response: any) => {
      if (response?.success) {
        resolve(response);
      } else {
        reject(new Error(response?.error || 'Failed to update video state'));
      }
    });
  });
};

// Cleanup media resources
export const cleanupMedia = () => {
  // Stop all tracks in the local stream
  if (localStream) {
    localStream.getTracks().forEach(track => track.stop());
    localStream = null;
  }
  
  // Destroy all peer connections
  Object.values(peers).forEach(peer => peer.destroy());
  Object.keys(peers).forEach(key => delete peers[key]);
};

export default {
  connectSocket,
  initUserMedia,
  toggleVideo,
  toggleAudio,
  joinWatchParty,
  leaveWatchParty,
  updateVideoState,
  cleanupMedia
}; 