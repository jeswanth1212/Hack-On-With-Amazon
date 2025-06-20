'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose } from '@/components/ui/dialog';
import { Search, UserPlus, Mail } from 'lucide-react';
import { mockFriends } from '@/lib/mock-friends-data';
import { fetchTrendingWeek } from '@/lib/tmdb';
import Image from 'next/image';

// Extended friend interface with movie data
interface FriendWithMovies {
  id: string;
  username: string;
  avatar: string;
  status?: 'online' | 'offline' | 'watching';
  films: number;
  reviews: number;
  recentMovies: Array<{
    id: string;
    posterUrl: string;
  }>;
}

export default function FriendsListView() {
  const [friends, setFriends] = useState<FriendWithMovies[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [newFriendEmail, setNewFriendEmail] = useState('');
  const [loading, setLoading] = useState(true);

  // Fetch trending movies to use as mock data for friend's recent movies
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const trendingData = await fetchTrendingWeek();
        
        // Create extended friends data with movie information
        const friendsWithMovies = mockFriends.map((friend) => {
          // Get 4 random movies for each friend
          const shuffled = [...trendingData].sort(() => 0.5 - Math.random());
          const recentMovies = shuffled.slice(0, 4).map(movie => ({
            id: movie.id.toString(),
            posterUrl: movie.posterUrl
          }));
          
          return {
            ...friend,
            films: Math.floor(Math.random() * 5000) + 1000, // Random number between 1000-6000
            reviews: Math.floor(Math.random() * 3000) + 500, // Random number between 500-3500
            recentMovies
          };
        });
        
        setFriends(friendsWithMovies);
      } catch (error) {
        console.error('Error loading data:', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, []);

  const filteredFriends = friends.filter(friend => 
    friend.username.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleAddFriend = () => {
    // In a real app, this would send an invitation request
    setNewFriendEmail('');
  };

  return (
    <div className="space-y-6">
      {/* Search and Add Friend Header */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
          <Input 
            className="pl-10 bg-secondary border-0 text-white focus-visible:ring-1 focus-visible:ring-primary"
            placeholder="Find a friend..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        
        <Dialog>
          <DialogTrigger asChild>
            <Button className="bg-primary text-background hover:bg-primary/90">
              <UserPlus size={18} className="mr-2" />
              Add Friend
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-secondary border-gray-700">
            <DialogHeader>
              <DialogTitle className="text-white">Add a Friend</DialogTitle>
            </DialogHeader>
            <div className="py-4 space-y-4">
              <div>
                <label htmlFor="email" className="text-sm text-gray-400 block mb-2">
                  Enter email address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
                  <Input 
                    id="email"
                    className="pl-10 bg-background/50 border-0 text-white focus-visible:ring-1 focus-visible:ring-primary"
                    placeholder="friend@example.com"
                    type="email"
                    value={newFriendEmail}
                    onChange={(e) => setNewFriendEmail(e.target.value)}
                  />
                </div>
              </div>
            </div>
            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline" className="text-white border-white/30">
                  Cancel
                </Button>
              </DialogClose>
              <Button 
                className="bg-primary text-background hover:bg-primary/90"
                onClick={handleAddFriend}
              >
                Send Invitation
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Friends Grid */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary"></div>
        </div>
      ) : filteredFriends.length > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-8">
          {filteredFriends.map((friend) => (
            <FriendProfileCard key={friend.id} friend={friend} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-secondary/60 rounded-lg">
          <p className="text-gray-400">
            {searchQuery ? 'No friends match your search' : 'No friends added yet'}
          </p>
        </div>
      )}
    </div>
  );
}

interface FriendProfileCardProps {
  friend: FriendWithMovies;
}

function FriendProfileCard({ friend }: FriendProfileCardProps) {
  // Generate a unique gradient for each friend based on their ID
  const getGradientStyle = (id: string) => {
    // Use the friend's ID to generate a consistent but unique gradient
    const hash = id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const hue1 = hash % 360;
    const hue2 = (hash * 2) % 360;
    
    return {
      background: `linear-gradient(135deg, hsl(${hue1}, 70%, 60%), hsl(${hue2}, 70%, 40%))`
    };
  };

  return (
    <div className="flex flex-col items-center space-y-4 group cursor-pointer p-4 rounded-lg border border-gray-800 hover:border-blue-500 transition-all duration-300 transform hover:scale-105 outline-none focus:ring-2 focus:ring-blue-500">
      {/* Profile Picture with Status Indicator */}
      <div className="relative">
        <div 
          className="w-[140px] h-[140px] rounded-full overflow-hidden flex items-center justify-center transition-all duration-300"
          style={getGradientStyle(friend.id)}
        >
          <span className="text-3xl font-bold text-white">
            {friend.username.charAt(0).toUpperCase()}
          </span>
        </div>
        
        {/* Status Indicator */}
        <div 
          className={`absolute bottom-2 right-2 w-4 h-4 rounded-full border-2 border-background ${
            friend.status === 'online' ? 'bg-green-500' : 
            friend.status === 'watching' ? 'bg-orange-500' : 'bg-gray-500'
          }`}
        />
      </div>
      
      {/* Username */}
      <h3 className="font-medium text-white text-center">{friend.username}</h3>
      
      {/* Stats */}
      <div className="flex items-center justify-center space-x-4 text-sm text-gray-300">
        <div className="flex flex-col items-center">
          <span className="font-semibold">{friend.films.toLocaleString()}</span>
          <span className="text-xs text-gray-400">films</span>
        </div>
        <div className="w-px h-8 bg-gray-700"></div>
        <div className="flex flex-col items-center">
          <span className="font-semibold">{friend.reviews.toLocaleString()}</span>
          <span className="text-xs text-gray-400">reviews</span>
        </div>
      </div>
      
      {/* Recent Movies */}
      <div className="grid grid-cols-4 gap-1 w-full">
        {friend.recentMovies.map((movie) => (
          <div 
            key={movie.id} 
            className="aspect-[2/3] rounded-sm overflow-hidden"
          >
            <Image 
              src={movie.posterUrl} 
              alt="Movie poster" 
              width={50} 
              height={75}
              className="object-cover w-full h-full"
            />
          </div>
        ))}
      </div>
    </div>
  );
} 