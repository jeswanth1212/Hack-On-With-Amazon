'use client';

import { useState, useEffect } from 'react';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { getFriendRequests, respondToFriendRequest, FriendRequest } from '@/lib/utils';
import { useAuth } from '@/lib/hooks';

interface RequestsViewProps {
  onAccept: (id: string) => void;
  onReject: (id: string) => void;
}

export default function RequestsView({ onAccept, onReject }: RequestsViewProps) {
  const [requests, setRequests] = useState<FriendRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [pendingActions, setPendingActions] = useState<Record<number, boolean>>({});
  const { user } = useAuth();

  // Current user ID from auth context
  const currentUserId = user?.user_id || "guest";

  useEffect(() => {
    const loadRequests = async () => {
      if (!user) {
        setLoading(false);
        return;
      }
      
      try {
        const friendRequests = await getFriendRequests(currentUserId);
        setRequests(friendRequests);
      } catch (error) {
        console.error('Error loading friend requests:', error);
      } finally {
        setLoading(false);
      }
    };

    loadRequests();
  }, [currentUserId, user]);

  const handleAccept = async (requestId: number, senderId: string) => {
    setPendingActions(prev => ({ ...prev, [requestId]: true }));
    try {
      const success = await respondToFriendRequest(requestId, 'accepted');
      if (success) {
        setRequests(prev => prev.filter(r => r.request_id !== requestId));
        onAccept(senderId);
      }
    } catch (error) {
      console.error('Error accepting friend request:', error);
    } finally {
      setPendingActions(prev => ({ ...prev, [requestId]: false }));
    }
  };

  const handleReject = async (requestId: number, senderId: string) => {
    setPendingActions(prev => ({ ...prev, [requestId]: true }));
    try {
      const success = await respondToFriendRequest(requestId, 'rejected');
      if (success) {
        setRequests(prev => prev.filter(r => r.request_id !== requestId));
        onReject(senderId);
      }
    } catch (error) {
      console.error('Error rejecting friend request:', error);
    } finally {
      setPendingActions(prev => ({ ...prev, [requestId]: false }));
    }
  };

  // Function to get initials from user ID
  const getInitials = (userId: string) => {
    return userId.substring(0, 2).toUpperCase();
  };

  if (!user) {
    return (
      <div className="py-12 text-center">
        <p className="text-muted-foreground">Please log in to see friend requests</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="py-12 text-center">
        <p className="text-muted-foreground">Loading requests...</p>
      </div>
    );
  }

  if (requests.length === 0) {
    return (
      <div className="py-12 text-center">
        <p className="text-muted-foreground">No pending friend requests</p>
      </div>
    );
  }

  return (
    <div className="py-6">
      <h2 className="text-2xl font-bold mb-6">Friend Requests</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {requests.map((request) => (
          <Card key={request.request_id} className="bg-gray-950/60">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <Avatar className="h-12 w-12">
                  <AvatarFallback className="bg-primary/20">{getInitials(request.sender_id)}</AvatarFallback>
                </Avatar>
                <div>
                  <h3 className="font-medium text-lg">{request.sender_id}</h3>
                  <p className="text-sm text-muted-foreground">
                    {request.location && `${request.location} • `}
                    {request.age && `${request.age} years old`}
                  </p>
                </div>
              </div>
            </CardContent>
            <CardFooter className="px-6 py-4 border-t border-gray-800 flex justify-between gap-2">
              <Button 
                onClick={() => handleAccept(request.request_id, request.sender_id)} 
                disabled={pendingActions[request.request_id]}
                className="flex-1"
              >
                Accept
              </Button>
              <Button 
                onClick={() => handleReject(request.request_id, request.sender_id)} 
                variant="destructive" 
                disabled={pendingActions[request.request_id]}
                className="flex-1"
              >
                Reject
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
} 