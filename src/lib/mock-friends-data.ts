// Mock data for friends functionality

export interface Friend {
  id: string;
  username: string;
  avatar: string;
  status?: 'online' | 'offline' | 'watching';
}

export interface ActivityItem {
  id: string;
  friendId: string;
  contentType: 'movie' | 'series';
  contentTitle: string;
  contentImage: string;
  timestamp: number; // Unix timestamp
}

export interface FriendRequest {
  id: string;
  type: 'incoming' | 'outgoing';
  user: {
    id: string;
    username: string;
    avatar: string;
  };
  timestamp: number;
}

// Mock friends data
export const mockFriends: Friend[] = [
  {
    id: 'friend-1',
    username: 'Alex Johnson',
    avatar: '/assets/avatars/avatar-1.jpg',
    status: 'online'
  },
  {
    id: 'friend-2',
    username: 'Jamie Smith',
    avatar: '/assets/avatars/avatar-2.jpg',
    status: 'watching'
  },
  {
    id: 'friend-3',
    username: 'Taylor Wilson',
    avatar: '/assets/avatars/avatar-3.jpg',
    status: 'offline'
  },
  {
    id: 'friend-4',
    username: 'Casey Brown',
    avatar: '/assets/avatars/avatar-4.jpg',
    status: 'online'
  },
  {
    id: 'friend-5',
    username: 'Morgan Davis',
    avatar: '/assets/avatars/avatar-5.jpg',
    status: 'offline'
  },
  {
    id: 'friend-6',
    username: 'Riley Garcia',
    avatar: '/assets/avatars/avatar-6.jpg',
    status: 'watching'
  }
];

// Mock activity data
export const mockActivities: ActivityItem[] = [
  {
    id: 'activity-1',
    friendId: 'friend-1',
    contentType: 'movie',
    contentTitle: 'The Tomorrow War',
    contentImage: '/assets/content/movie-1.jpg',
    timestamp: Date.now() - 1000 * 60 * 10 // 10 minutes ago
  },
  {
    id: 'activity-2',
    friendId: 'friend-2',
    contentType: 'movie',
    contentTitle: 'Inception',
    contentImage: '/assets/content/movie-2.jpg',
    timestamp: Date.now() - 1000 * 60 * 30 // 30 minutes ago
  },
  {
    id: 'activity-3',
    friendId: 'friend-3',
    contentType: 'series',
    contentTitle: 'Stranger Things',
    contentImage: '/assets/content/series-1.jpg',
    timestamp: Date.now() - 1000 * 60 * 60 * 2 // 2 hours ago
  },
  {
    id: 'activity-4',
    friendId: 'friend-1',
    contentType: 'series',
    contentTitle: 'The Boys',
    contentImage: '/assets/content/series-2.jpg',
    timestamp: Date.now() - 1000 * 60 * 60 * 5 // 5 hours ago
  },
  {
    id: 'activity-5',
    friendId: 'friend-1',
    contentType: 'series',
    contentTitle: 'The Mandalorian',
    contentImage: '/assets/content/series-3.jpg',
    timestamp: Date.now() - 1000 * 60 * 60 * 24 // 1 day ago
  },
  {
    id: 'activity-6',
    friendId: 'friend-4',
    contentType: 'movie',
    contentTitle: 'Dune',
    contentImage: '/assets/content/movie-3.jpg',
    timestamp: Date.now() - 1000 * 60 * 60 * 25 // 25 hours ago
  },
  {
    id: 'activity-7',
    friendId: 'friend-5',
    contentType: 'series',
    contentTitle: 'House of the Dragon',
    contentImage: '/assets/content/series-4.jpg',
    timestamp: Date.now() - 1000 * 60 * 60 * 48 // 2 days ago
  }
];

// Mock friend requests
export const mockFriendRequests: FriendRequest[] = [
  {
    id: 'request-1',
    type: 'incoming',
    user: {
      id: 'user-1',
      username: 'Jordan Lee',
      avatar: '/assets/avatars/avatar-7.jpg',
    },
    timestamp: Date.now() - 1000 * 60 * 60 * 3 // 3 hours ago
  },
  {
    id: 'request-2',
    type: 'incoming',
    user: {
      id: 'user-2',
      username: 'Quinn Martinez',
      avatar: '/assets/avatars/avatar-8.jpg',
    },
    timestamp: Date.now() - 1000 * 60 * 60 * 12 // 12 hours ago
  },
  {
    id: 'request-3',
    type: 'outgoing',
    user: {
      id: 'user-3',
      username: 'Skyler Patel',
      avatar: '/assets/avatars/avatar-9.jpg',
    },
    timestamp: Date.now() - 1000 * 60 * 60 * 6 // 6 hours ago
  },
  {
    id: 'request-4',
    type: 'outgoing',
    user: {
      id: 'user-4',
      username: 'Avery Thompson',
      avatar: '/assets/avatars/avatar-10.jpg',
    },
    timestamp: Date.now() - 1000 * 60 * 60 * 24 * 2 // 2 days ago
  }
];

// Helper function to get relative time string
export function getRelativeTimeString(timestamp: number): string {
  const now = Date.now();
  const diff = now - timestamp;
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return days === 1 ? 'Yesterday' : `${days} days ago`;
  } else if (hours > 0) {
    return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`;
  } else if (minutes > 0) {
    return `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} ago`;
  } else {
    return 'Just now';
  }
} 