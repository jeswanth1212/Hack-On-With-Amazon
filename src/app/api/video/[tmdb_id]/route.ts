import { NextRequest, NextResponse } from 'next/server';

// This is a mock video API for the watch party feature
// In a real application, this would fetch and stream actual video content
// based on the tmdb_id parameter or integrate with a proper streaming service API

export async function GET(
  request: NextRequest,
  { params }: { params: { tmdb_id: string } }
) {
  try {
    const tmdbId = params.tmdb_id;
    
    // This is a simple mock endpoint that redirects to a sample video
    // In a real implementation, this would fetch the actual video URL from a media service
    
    // List of sample videos we can use for testing
    const sampleVideos = [
      'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
      'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
      'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
      'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4',
      'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4',
      'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4',
      'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4',
      'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4',
      'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/SubaruOutbackOnStreetAndDirt.mp4',
      'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4',
    ];
    
    // Select a video based on the TMDB ID to ensure consistency for the same movie
    const videoIndex = parseInt(tmdbId) % sampleVideos.length;
    const videoUrl = sampleVideos[videoIndex];
    
    // Log which video is being served
    console.log(`Serving video for TMDB ID ${tmdbId}: ${videoUrl}`);
    
    // Redirect to the sample video
    return NextResponse.redirect(videoUrl);
  } catch (error) {
    console.error('Error serving video:', error);
    return new NextResponse('Error serving video', { status: 500 });
  }
} 