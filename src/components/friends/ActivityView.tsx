'use client';

import { useState, useEffect } from 'react';
import { AvatarWithStatus } from '@/components/ui/avatar-with-status';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { mockActivities, mockFriends, getRelativeTimeString } from '@/lib/mock-friends-data';
import Image from 'next/image';
import { AspectRatio } from '@/components/ui/aspect-ratio';

export default function ActivityView() {
  const [activities, setActivities] = useState(mockActivities);
  
  // Combine activity data with friend data
  const activitiesWithFriendData = activities.map(activity => {
    const friend = mockFriends.find(friend => friend.id === activity.friendId);
    return {
      ...activity,
      friend: friend || { id: '', username: 'Unknown User', avatar: '' }
    };
  });

  return (
    <ScrollArea className="h-[calc(100vh-220px)]">
      <div className="space-y-3 pb-4">
        {activitiesWithFriendData.map((activity, index) => (
          <ActivityItem
            key={activity.id}
            activity={activity}
            isAlternate={index % 2 === 1}
          />
        ))}
      </div>
    </ScrollArea>
  );
}

interface ActivityItemProps {
  activity: any;
  isAlternate: boolean;
}

function ActivityItem({ activity, isAlternate }: ActivityItemProps) {
  const timeString = getRelativeTimeString(activity.timestamp);
  
  return (
    <Card 
      className={`p-4 flex items-center gap-3 ${isAlternate ? 'bg-secondary/60' : 'bg-secondary'}`}
      tabIndex={0} // Make keyboard-navigable
    >
      <AvatarWithStatus
        src={activity.friend.avatar}
        username={activity.friend.username}
        status={activity.friend.status}
      />
      
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between">
          <div>
            <span className="font-semibold text-white">
              {activity.friend.username}
            </span>
            <span className="text-gray-400 mx-2">watched</span>
            <span className="font-bold text-primary">
              {activity.contentTitle}
            </span>
          </div>
          <span className="text-sm text-gray-400 shrink-0 ml-2">
            {timeString}
          </span>
        </div>
        
        <div className="text-xs text-gray-400 mt-1">
          {activity.contentType === 'movie' ? 'Movie' : 'TV Series'}
        </div>
      </div>
      
      <div className="w-16 h-24 shrink-0 overflow-hidden rounded">
        <AspectRatio ratio={2/3} className="bg-background">
          <div className="relative h-full">
            <Image
              src={activity.contentImage}
              alt={activity.contentTitle}
              fill
              className="object-cover"
              sizes="(max-width: 768px) 100vw, 64px"
              loading="lazy"
              unoptimized // For mock images - remove in production
            />
          </div>
        </AspectRatio>
      </div>
    </Card>
  );
} 