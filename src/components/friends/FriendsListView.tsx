'use client';

import { useState, useEffect } from 'react';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getFriends, Friend } from '@/lib/utils';
import { useAuth } from '@/lib/hooks';

interface FriendsListViewProps {
  onRemove: (id: string) => void;
}

export default function FriendsListView({ onRemove }: FriendsListViewProps) {
  const [friends, setFriends] = useState<Friend[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  // Current user ID from auth context
  const currentUserId = user?.user_id || "guest";

  useEffect(() => {
    const loadFriends = async () => {
      if (!user) {
        setLoading(false);
        return;
      }
      
      try {
        const userFriends = await getFriends(currentUserId);
        setFriends(userFriends);
      } catch (error) {
        console.error('Error loading friends:', error);
      } finally {
        setLoading(false);
      }
    };

    loadFriends();
  }, [currentUserId, user]);

  const handleRemoveFriend = async (friendId: string) => {
    // In a real app, you'd have an API call to remove a friend
    // For now, just remove from local state
    setFriends(prev => prev.filter(f => f.user_id !== friendId));
    onRemove(friendId);
  };

  // Function to get initials from user ID
  const getInitials = (userId: string) => {
    return userId.substring(0, 2).toUpperCase();
  };

  if (!user) {
    return (
      <div className="py-12 text-center">
        <p className="text-muted-foreground">Please log in to see your friends</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="py-12 text-center">
        <p className="text-muted-foreground">Loading friends...</p>
      </div>
    );
  }

  if (friends.length === 0) {
    return (
      <div className="py-12 text-center">
        <p className="text-muted-foreground">You don't have any friends yet. Start by searching for users!</p>
      </div>
    );
  }

  return (
    <div className="py-6">
      <h2 className="text-2xl font-bold mb-6">Your Friends</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {friends.map((friend) => (
          <Card key={friend.user_id} className="bg-gray-950/60">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <Avatar className="h-12 w-12">
                  <AvatarFallback className="bg-primary/20">{getInitials(friend.user_id)}</AvatarFallback>
                </Avatar>
                <div className="flex-1">
                  <div className="flex justify-between items-start">
                    <h3 className="font-medium text-lg">{friend.user_id}</h3>
                    <Badge variant="outline" className="text-xs">
                      {new Date(friend.friendship_date).toLocaleDateString()}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {friend.location && `${friend.location} • `}
                    {friend.age_group || (friend.age && `${friend.age} years old`)}
                  </p>
                </div>
              </div>
              
              {friend.preferred_genres && friend.preferred_genres.length > 0 && (
                <div className="mt-3">
                  <p className="text-sm text-muted-foreground">
                    Enjoys: {friend.preferred_genres.slice(0, 3).join(', ')}
                    {friend.preferred_genres.length > 3 && '...'}
                  </p>
                </div>
              )}
            </CardContent>
            <CardFooter className="px-6 py-4 border-t border-gray-800">
              <Button 
                onClick={() => handleRemoveFriend(friend.user_id)} 
                variant="ghost"
                className="w-full text-muted-foreground hover:text-destructive"
                size="sm"
              >
                Remove Friend
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
} 