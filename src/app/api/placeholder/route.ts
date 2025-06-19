import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  const title = req.nextUrl.searchParams.get('title') || 'No Image';
  
  // Create an SVG with the first letter of the title
  const svg = `<svg width="500" height="750" xmlns="http://www.w3.org/2000/svg">
    <rect width="100%" height="100%" fill="#1E293B" />
    <text x="50%" y="50%" font-family="Arial" font-size="48" fill="#F5A623" text-anchor="middle" dominant-baseline="middle">
      ${title.charAt(0).toUpperCase()}
    </text>
    <text x="50%" y="60%" font-family="Arial" font-size="24" fill="#F1F5F9" text-anchor="middle" dominant-baseline="middle">
      No Image Available
    </text>
  </svg>`;

  return new NextResponse(svg, {
    headers: {
      'Content-Type': 'image/svg+xml',
      'Cache-Control': 'public, max-age=31536000, immutable',
    },
  });
} 