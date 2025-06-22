'use client';

import { useState, useEffect } from 'react';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getFriendActivities, FriendActivity } from '@/lib/utils';
import { useAuth } from '@/lib/hooks';

interface FormattedActivity {
  id: string;
  friendId: string;
  itemId: string;
  title: string;
  message: string;
  timestamp: number;
  friendInitials: string;
}

interface ActivityViewProps {
  currentUser: {
    username: string;
    avatar?: string;
  };
}

export default function ActivityView({ currentUser }: ActivityViewProps) {
  const [activities, setActivities] = useState<FormattedActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  // Current user ID from auth context
  const currentUserId = user?.user_id || "guest";

  useEffect(() => {
    const loadActivities = async () => {
      if (!user) {
        setLoading(false);
        return;
      }
      
      try {
        const friendActivities = await getFriendActivities(currentUserId, 50);
        
        // Format the activities for display
        const formatted = friendActivities.map(activity => {
          // Create a message based on the activity
          const sentimentText = getSentimentText(activity.sentiment_score);
          const message = `watched "${activity.title}" ${sentimentText}`;
          
          return {
            id: `${activity.friend_id}-${activity.item_id}-${activity.timestamp}`,
            friendId: activity.friend_id,
            itemId: activity.item_id,
            title: activity.title,
            message: message,
            timestamp: new Date(activity.timestamp).getTime(),
            friendInitials: activity.friend_id.substring(0, 2).toUpperCase(),
          };
        });
        
        // Sort by timestamp (newest first)
        formatted.sort((a, b) => b.timestamp - a.timestamp);
        
        setActivities(formatted);
      } catch (error) {
        console.error('Error loading friend activities:', error);
      } finally {
        setLoading(false);
      }
    };

    loadActivities();
  }, [currentUserId, user]);

  const getSentimentText = (score?: number): string => {
    if (!score) return '';
    
    if (score > 0.8) return 'and absolutely loved it!';
    if (score > 0.6) return 'and enjoyed it';
    if (score > 0.4) return '';
    if (score > 0.2) return 'but was not impressed';
    return 'and did not like it';
  };

  const formatTimeAgo = (timestamp: number) => {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);
    
    let interval = Math.floor(seconds / 31536000);
    if (interval > 1) return interval + " years ago";
    
    interval = Math.floor(seconds / 2592000);
    if (interval > 1) return interval + " months ago";
    
    interval = Math.floor(seconds / 86400);
    if (interval > 1) return interval + " days ago";
    
    interval = Math.floor(seconds / 3600);
    if (interval > 1) return interval + " hours ago";
    
    interval = Math.floor(seconds / 60);
    if (interval > 1) return interval + " minutes ago";
    
    return Math.floor(seconds) + " seconds ago";
  };

  const handleWatchMovie = (itemId: string) => {
    // In a real app, this would navigate to the movie page
    window.location.href = `/movie/${itemId}`;
  };

  if (!user) {
    return (
      <div className="py-12 text-center">
        <p className="text-muted-foreground">Please log in to see friend activity</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="py-12 text-center">
        <p className="text-muted-foreground">Loading activities...</p>
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="py-12 text-center">
        <p className="text-muted-foreground">No recent friend activity</p>
      </div>
    );
  }

  return (
    <div className="py-6">
      <h2 className="text-2xl font-bold mb-6">Friend Activity</h2>
      <div className="space-y-4">
        {activities.map((activity) => (
          <Card key={activity.id} className="bg-gray-950/60">
            <CardContent className="p-6">
              <div className="flex gap-4">
                <Avatar className="h-12 w-12">
                  <AvatarFallback className="bg-primary/20">{activity.friendInitials}</AvatarFallback>
                </Avatar>
                <div className="flex-1">
                  <div className="flex justify-between items-start">
                    <p className="font-medium">
                      <span className="text-primary">{activity.friendId}</span> {activity.message}
                    </p>
                    <Badge variant="outline" className="text-xs">
                      {formatTimeAgo(activity.timestamp)}
                    </Badge>
                  </div>
                  
                  <div className="mt-4 flex justify-end">
                    <Button size="sm" onClick={() => handleWatchMovie(activity.itemId)}>
                      Watch This
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
} 