'use client';

import { useState, useEffect } from 'react';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { searchUsers, sendFriendRequest, UserProfile } from '@/lib/utils';
import { useAuth } from '@/lib/hooks';

interface SearchUsersViewProps {
  onSendRequest: (user: any) => void; 
}

export default function SearchUsersView({ onSendRequest }: SearchUsersViewProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(false);
  const [sentRequests, setSentRequests] = useState<string[]>([]);
  const { user } = useAuth();
  
  // Current user ID from auth context
  const currentUserId = user?.user_id || "guest";
  
  const handleSearch = async () => {
    if (!query.trim() || !user) return;
    
    setLoading(true);
    try {
      const searchResults = await searchUsers(query, currentUserId);
      setResults(searchResults);
    } catch (error) {
      console.error('Error searching for users:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleSendRequest = async (user: UserProfile) => {
    if (!currentUserId || currentUserId === "guest") {
      alert("Please log in to send friend requests");
      return;
    }
    
    try {
      const success = await sendFriendRequest(currentUserId, user.user_id);
      if (success) {
        setSentRequests(prev => [...prev, user.user_id]);
        onSendRequest(user);
      }
    } catch (error) {
      console.error('Error sending friend request:', error);
    }
  };
  
  // Function to get initials from user ID
  const getInitials = (userId: string) => {
    return userId.substring(0, 2).toUpperCase();
  };
  
  // Handle search on Enter key
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };
  
  return (
    <div className="py-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-4">Find Friends</h2>
        <div className="flex gap-2">
          <Input
            placeholder="Search by username..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyPress}
            className="flex-1"
          />
          <Button onClick={handleSearch} disabled={loading || !user}>
            {loading ? 'Searching...' : 'Search'}
          </Button>
        </div>
      </div>
      
      {!user ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">Please log in to search for friends</p>
        </div>
      ) : results.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {results.map((user) => (
            <Card key={user.user_id} className="bg-gray-950/60">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <Avatar className="h-12 w-12">
                    <AvatarFallback className="bg-primary/20">{getInitials(user.user_id)}</AvatarFallback>
                  </Avatar>
                  <div>
                    <h3 className="font-medium text-lg">{user.user_id}</h3>
                    <p className="text-sm text-muted-foreground">
                      {user.location && `${user.location} • `}
                      {user.age && `${user.age} years old`}
                    </p>
                  </div>
                </div>
                
                {user.preferred_genres && user.preferred_genres.length > 0 && (
                  <div className="mt-3">
                    <p className="text-sm text-muted-foreground">
                      Enjoys: {user.preferred_genres.slice(0, 3).join(', ')}
                      {user.preferred_genres.length > 3 && '...'}
                    </p>
                  </div>
                )}
              </CardContent>
              <CardFooter className="px-6 py-4 border-t border-gray-800">
                <Button 
                  onClick={() => handleSendRequest(user)} 
                  disabled={sentRequests.includes(user.user_id)}
                  variant={sentRequests.includes(user.user_id) ? "secondary" : "default"}
                  className="w-full"
                >
                  {sentRequests.includes(user.user_id) ? 'Request Sent' : 'Send Request'}
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      ) : query && !loading ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No users found matching "{query}"</p>
        </div>
      ) : !loading && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">Search for users to add as friends</p>
        </div>
      )}
    </div>
  );
} 