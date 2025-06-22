'use client';

import { useState, useEffect } from 'react';
import MainLayout from '../layout/MainLayout';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import SearchUsersView from './SearchUsersView';
import RequestsView from './RequestsView';
import FriendsListView from './FriendsListView';
import ActivityView from './ActivityView';
import TiersView from './TiersView';
import WatchPartyRequestsView from './WatchPartyRequestsView';
import { Badge } from '@/components/ui/badge';
import { getFriendRequests } from '@/lib/utils';
import { useAuth, useNotifications } from '@/lib/hooks';

export default function FriendsPage() {
  const [pendingCount, setPendingCount] = useState(0);
  const { user } = useAuth();
  const { watchPartyCount } = useNotifications();
  
  // Current user ID from auth context
  const currentUserId = user?.user_id || "guest";
  
  // Current user info (in a real app, get from profile)
  const currentUser = { username: currentUserId, avatar: undefined };

  useEffect(() => {
    // Load pending requests count
    const loadPendingRequests = async () => {
      if (!user) return; // Don't load requests if not logged in
      
      try {
        const requests = await getFriendRequests(currentUserId);
        setPendingCount(requests.length);
      } catch (error) {
        console.error('Error loading friend requests:', error);
      }
    };

    loadPendingRequests();
  }, [currentUserId, user]);

  // Handlers
  const handleSendRequest = (user: any) => {
    // This is handled in the SearchUsersView component now
  };

  const handleAcceptRequest = (id: string) => {
    // Decrement pending count when a request is accepted
    setPendingCount(prev => Math.max(0, prev - 1));
  };

  const handleRejectRequest = (id: string) => {
    // Decrement pending count when a request is rejected
    setPendingCount(prev => Math.max(0, prev - 1));
  };

  const handleRemoveFriend = (id: string) => {
    // This is handled in the FriendsListView component now
  };

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
              <TabsTrigger value="wp" className="flex-1 py-3 data-[state=active]:bg-secondary flex items-center justify-center gap-2">
                Watch Party {watchPartyCount > 0 && <Badge variant="secondary">{watchPartyCount}</Badge>}
              </TabsTrigger>
              <TabsTrigger value="friends" className="flex-1 py-3 data-[state=active]:bg-secondary">Friends</TabsTrigger>
              <TabsTrigger value="activity" className="flex-1 py-3 data-[state=active]:bg-secondary">Activity</TabsTrigger>
              <TabsTrigger value="tiers" className="flex-1 py-3 data-[state=active]:bg-secondary">Tiers</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="search"><SearchUsersView onSendRequest={handleSendRequest} /></TabsContent>
          <TabsContent value="requests"><RequestsView onAccept={handleAcceptRequest} onReject={handleRejectRequest} /></TabsContent>
          <TabsContent value="friends"><FriendsListView onRemove={handleRemoveFriend} /></TabsContent>
          <TabsContent value="wp"><WatchPartyRequestsView /></TabsContent>
          <TabsContent value="activity"><ActivityView currentUser={currentUser} /></TabsContent>
          <TabsContent value="tiers"><TiersView currentPoints={100} /></TabsContent>
        </Tabs>
      </div>
    </MainLayout>
  );
}
