'use client';

import { useState } from 'react';
import { AvatarWithStatus } from '@/components/ui/avatar-with-status';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { mockFriendRequests, getRelativeTimeString } from '@/lib/mock-friends-data';
import { Check, X, UserPlus2 } from 'lucide-react';

export default function RequestsView() {
  const [requests, setRequests] = useState(mockFriendRequests);

  const incomingRequests = requests.filter(req => req.type === 'incoming');
  const outgoingRequests = requests.filter(req => req.type === 'outgoing');

  const handleAccept = (requestId: string) => {
    setRequests(prev => prev.filter(req => req.id !== requestId));
  };

  const handleDecline = (requestId: string) => {
    setRequests(prev => prev.filter(req => req.id !== requestId));
  };

  const handleCancel = (requestId: string) => {
    setRequests(prev => prev.filter(req => req.id !== requestId));
  };

  return (
    <ScrollArea className="h-[calc(100vh-220px)]">
      <div className="space-y-6 pb-4">
        {/* Incoming Requests Section */}
        <div>
          <h3 className="text-lg font-semibold text-white mb-3">
            Incoming Requests
          </h3>
          
          {incomingRequests.length > 0 ? (
            <div className="space-y-3">
              {incomingRequests.map(request => (
                <RequestCard
                  key={request.id}
                  request={request}
                  onAccept={() => handleAccept(request.id)}
                  onDecline={() => handleDecline(request.id)}
                />
              ))}
            </div>
          ) : (
            <Card className="p-6 bg-secondary/60 text-center">
              <p className="text-gray-400">No incoming friend requests</p>
            </Card>
          )}
        </div>
        
        <Separator className="bg-gray-800" />
        
        {/* Outgoing Invites Section */}
        <div>
          <h3 className="text-lg font-semibold text-white mb-3">
            Outgoing Invites
          </h3>
          
          {outgoingRequests.length > 0 ? (
            <div className="space-y-3">
              {outgoingRequests.map(request => (
                <OutgoingRequestCard
                  key={request.id}
                  request={request}
                  onCancel={() => handleCancel(request.id)}
                />
              ))}
            </div>
          ) : (
            <Card className="p-6 bg-secondary/60 text-center">
              <p className="text-gray-400">No outgoing invites</p>
            </Card>
          )}
        </div>
        
        {/* Add Friend CTA Section */}
        {requests.length === 0 && (
          <div className="mt-6 text-center">
            <Card className="p-6 bg-secondary/60 inline-block mx-auto">
              <div className="flex flex-col items-center space-y-3">
                <UserPlus2 size={36} className="text-primary" />
                <h4 className="text-lg font-medium text-white">No Friend Requests</h4>
                <Button className="bg-primary text-background hover:bg-primary/90">
                  Invite Friends
                </Button>
              </div>
            </Card>
          </div>
        )}
      </div>
    </ScrollArea>
  );
}

interface RequestCardProps {
  request: any;
  onAccept: () => void;
  onDecline: () => void;
}

function RequestCard({ request, onAccept, onDecline }: RequestCardProps) {
  const timeString = getRelativeTimeString(request.timestamp);
  
  return (
    <Card className="p-4 bg-secondary flex items-center gap-3">
      <AvatarWithStatus
        src={request.user.avatar}
        username={request.user.username}
      />
      
      <div className="flex-1 min-w-0">
        <div className="font-semibold text-white">
          {request.user.username}
        </div>
        <div className="text-xs text-gray-400">
          {timeString}
        </div>
      </div>
      
      <div className="flex gap-2">
        <Button 
          size="sm" 
          className="bg-primary text-background hover:bg-primary/90"
          onClick={onAccept}
        >
          <Check size={16} className="mr-1" />
          Accept
        </Button>
        <Button 
          size="sm" 
          variant="outline" 
          className="text-white border-white/30 hover:bg-white/10"
          onClick={onDecline}
        >
          <X size={16} className="mr-1" />
          Decline
        </Button>
      </div>
    </Card>
  );
}

interface OutgoingRequestCardProps {
  request: any;
  onCancel: () => void;
}

function OutgoingRequestCard({ request, onCancel }: OutgoingRequestCardProps) {
  const timeString = getRelativeTimeString(request.timestamp);
  
  return (
    <Card className="p-4 bg-secondary/60 flex items-center gap-3">
      <AvatarWithStatus
        src={request.user.avatar}
        username={request.user.username}
      />
      
      <div className="flex-1 min-w-0">
        <div className="font-semibold text-white">
          {request.user.username}
        </div>
        <div className="text-xs text-gray-400">
          Sent {timeString}
        </div>
      </div>
      
      <Button 
        size="sm" 
        variant="ghost" 
        className="text-red-400 hover:text-red-300 hover:bg-red-900/20"
        onClick={onCancel}
      >
        Cancel
      </Button>
    </Card>
  );
} 