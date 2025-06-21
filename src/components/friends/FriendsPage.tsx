'use client';

import { useState, useEffect } from 'react';
import MainLayout from '../layout/MainLayout';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import SearchUsersView from './SearchUsersView';
import RequestsView from './RequestsView';
import FriendsListView from './FriendsListView';
import ActivityView, { Activity } from './ActivityView';
import TiersView from './TiersView';
import { Badge } from '@/components/ui/badge';

// Types
interface User { id: string; username: string; avatar?: string; email?: string; bio?: string; }
interface Request { id: string; username: string; avatar?: string; }
interface Friend { id: string; username: string; avatar?: string; points: number; }

export default function FriendsPage() {
  // State
  const [requests, setRequests] = useState<Request[]>([
    { id: 'req-1', username: 'NewFriend', avatar: '/assets/avatars/avatar-4.jpg' },
  ]);
  const [friends, setFriends] = useState<Friend[]>([
    { id: 'friend-1', username: 'Alex', avatar: '/assets/avatars/avatar-1.jpg', points: 140 },
    { id: 'friend-2', username: 'Jamie', avatar: '/assets/avatars/avatar-2.jpg', points: 60 },
  ]);
  const [activities, setActivities] = useState<Activity[]>([
    { id: 'act-1', username: 'Alex', avatar: '/assets/avatars/avatar-1.jpg', content: 'posted a Squid Game reel!', actionLabel: 'Watch Now', timestamp: Date.now() - 1000 * 60 * 30, likes: 5 },
    { id: 'act-2', username: 'Jamie', avatar: '/assets/avatars/avatar-2.jpg', content: 'hosted a Stranger Things watch party.', timestamp: Date.now() - 1000 * 60 * 60 * 2, likes: 2 },
    { id: 'act-3', username: 'Alex', avatar: '/assets/avatars/avatar-1.jpg', content: 'shared an interesting article about AI in movies.', timestamp: Date.now() - 1000 * 60 * 90, likes: 3 },
    { id: 'act-4', username: 'Jamie', avatar: '/assets/avatars/avatar-2.jpg', content: 'is looking for recommendations: "Any good thrillers?"', timestamp: Date.now() - 1000 * 60 * 180, likes: 1 },
  ]);
  const [points, setPoints] = useState(140);

  // Current user info (mock)
  const currentUser = { username: 'Me', avatar: '/assets/avatars/avatar-3.jpg' };

  // Handlers
  const handleSendRequest = (user: User) => {
    if (requests.find((r) => r.id === user.id) || friends.find((f) => f.id === user.id)) return;
    setRequests((prev) => [...prev, { id: user.id, username: user.username, avatar: user.avatar }]);
  };

  const handleAcceptRequest = (id: string) => {
    const req = requests.find((r) => r.id === id);
    if (!req) return;
    setFriends((prev) => [...prev, { id: req.id, username: req.username, avatar: req.avatar, points: 0 }]);
    setRequests((prev) => prev.filter((r) => r.id !== id));
  };

  const handleRejectRequest = (id: string) => {
    setRequests((prev) => prev.filter((r) => r.id !== id));
  };

  const handleRemoveFriend = (id: string) => {
    setFriends((prev) => prev.filter((f) => f.id !== id));
  };

  const pendingCount = requests.length;

  const addPost = (content: string) => {
    const newAct: Activity = {
      id: `post-${Date.now()}`,
      username: currentUser.username,
      avatar: currentUser.avatar,
      content,
      timestamp: Date.now(),
    };
    setActivities((prev) => [...prev, newAct]);
  };

  // Keyboard navigation (optional) – keep simple
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      // Example: shortcuts to tabs if needed
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, []);

  return (
    <MainLayout>
      <div className="max-w-5xl mx-auto px-6 pt-24 pb-16">
        <Tabs defaultValue="search" className="w-full">
          {/* Sticky header within Tabs */}
          <div className="sticky top-20 z-20 bg-background/90 backdrop-blur pb-4">
            <h1 className="text-4xl font-bold text-white mb-4">Friends</h1>
            <TabsList className="w-full max-w-lg bg-background border border-gray-800">
              <TabsTrigger value="search" className="flex-1 py-3 data-[state=active]:bg-secondary">Search</TabsTrigger>
              <TabsTrigger value="requests" className="flex-1 py-3 data-[state=active]:bg-secondary flex items-center justify-center gap-2">
                Requests {pendingCount > 0 && <Badge variant="secondary">{pendingCount}</Badge>}
              </TabsTrigger>
              <TabsTrigger value="friends" className="flex-1 py-3 data-[state=active]:bg-secondary">Friends</TabsTrigger>
              <TabsTrigger value="activity" className="flex-1 py-3 data-[state=active]:bg-secondary">Activity</TabsTrigger>
              <TabsTrigger value="tiers" className="flex-1 py-3 data-[state=active]:bg-secondary">Tiers</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="search"><SearchUsersView onSendRequest={handleSendRequest} /></TabsContent>
          <TabsContent value="requests"><RequestsView requests={requests} onAccept={handleAcceptRequest} onReject={handleRejectRequest} /></TabsContent>
          <TabsContent value="friends"><FriendsListView friends={friends} onRemove={handleRemoveFriend} /></TabsContent>
          <TabsContent value="activity"><ActivityView currentUser={currentUser} activities={activities} onAddPost={addPost} /></TabsContent>
          <TabsContent value="tiers"><TiersView currentPoints={points} /></TabsContent>
        </Tabs>
      </div>
    </MainLayout>
  );
}
