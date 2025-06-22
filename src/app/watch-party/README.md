# Watch Party Feature

This feature allows users to watch videos together in real-time while sharing their webcam and microphone. It uses WebRTC for peer-to-peer video/audio streaming and Socket.io for signaling and synchronization.

## Features

- Real-time video and audio streaming between participants
- Synchronized video playback controls
- Video selection from the recommendation system
- Camera and microphone controls
- Debug mode for troubleshooting connections

## Technical Implementation

### Frontend Components

- **WebRTC Peer Connections**: Managed through the simple-peer library
- **Socket.io Client**: Handles signaling and synchronization
- **MediaStreams**: Manages webcam and microphone access
- **Video Controls**: Synchronizes video playback state between participants

### Backend Components

- **Socket.io Server**: Manages rooms, participants, and signaling
- **Watch Party API**: Creates and manages watch party sessions in the database
- **Mock Video API**: Serves video content for the watch party

## How It Works

1. **Session Creation**: A user creates a watch party session via the API
2. **Connection**: Users connect to the session via Socket.io
3. **Media Access**: Users grant access to their webcam and microphone
4. **Signaling**: The Socket.io server handles WebRTC signaling between peers
5. **Streaming**: WebRTC establishes peer-to-peer connections for video/audio streaming
6. **Synchronization**: Video playback state is synchronized between participants

## File Structure

- `src/app/watch-party/session/page.tsx`: Main watch party session UI component
- `src/lib/socket.ts`: Socket.io client and WebRTC connection management
- `recommendation_system_backend/src/api/main.py`: Socket.io server implementation
- `src/app/api/video/[tmdb_id]/route.ts`: Mock video API endpoint

## Architecture

```
┌──────────────┐     WebRTC     ┌──────────────┐
│              │◄────Peer────►  │              │
│  Client A    │                │  Client B    │
│              │                │              │
└──────┬───────┘                └──────┬───────┘
       │                               │
       │ Socket.io                     │ Socket.io
       ▼                               ▼
┌─────────────────────────────────────────────┐
│                                             │
│            Socket.io Server                 │
│      (Signaling & Synchronization)          │
│                                             │
└─────────────────────────────────────────────┘
```

## Troubleshooting

If you encounter connection issues:

1. Enable debug mode using the button in the top-right corner of the watch party UI
2. Check the browser console for connection errors
3. Verify that the backend Socket.io server is running
4. Make sure your webcam and microphone permissions are granted
5. Try the Reconnect button if connection fails

### Common WebSocket Errors

#### "WebSocket connection to 'ws://localhost:8080/socket.io/?EIO=4&transport=websocket' failed"

This specific error occurs when the Socket.IO server is not properly configured to handle WebSocket connections.

**Solution:**

1. **Start the backend server with WebSocket support:**
   ```bash
   cd recommendation_system_backend
   python run.py --step api
   ```

2. **Verify server is running correctly:**
   The console output should show:
   ```
   Starting API server with WebSocket support...
   Server will be available at http://localhost:8080
   WebSocket will be available at ws://localhost:8080/socket.io/
   ```

3. **Check for network issues:**
   - Ensure no firewall is blocking WebSocket connections on port 8080
   - Verify no other service is using port 8080
   - Try accessing http://localhost:8080 in your browser to verify the server is running

4. **Browser compatibility:**
   - Make sure your browser supports WebSocket connections
   - Try using a different browser if issues persist
   - Clear browser cache and cookies if you continue to have connection problems

## Future Improvements

- Add chat feature for text communication
- Implement user reactions and emojis
- Add screen sharing capability
- Improve bandwidth management for multiple participants
- Add automatic reconnection on network instability 