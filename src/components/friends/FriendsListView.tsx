'use client';

import { useState } from 'react';
import { AvatarWithStatus } from '@/components/ui/avatar-with-status';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose } from '@/components/ui/dialog';
import { mockFriends } from '@/lib/mock-friends-data';
import { Search, UserPlus, Trash2, Mail } from 'lucide-react';

export default function FriendsListView() {
  const [friends, setFriends] = useState(mockFriends);
  const [searchQuery, setSearchQuery] = useState('');
  const [newFriendEmail, setNewFriendEmail] = useState('');

  const filteredFriends = friends.filter(friend => 
    friend.username.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleRemoveFriend = (friendId: string) => {
    setFriends(prev => prev.filter(friend => friend.id !== friendId));
  };

  const handleAddFriend = () => {
    // In a real app, this would send an invitation request
    setNewFriendEmail('');
    // We'd typically add optimistic UI updates here
  };

  return (
    <div className="space-y-4">
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

      {/* Friends List */}
      <ScrollArea className="h-[calc(100vh-280px)]">
        <div className="space-y-3 pb-4">
          {filteredFriends.length > 0 ? (
            filteredFriends.map((friend) => (
              <FriendCard
                key={friend.id}
                friend={friend}
                onRemove={() => handleRemoveFriend(friend.id)}
              />
            ))
          ) : (
            <Card className="p-6 bg-secondary/60 text-center">
              <p className="text-gray-400">
                {searchQuery ? 'No friends match your search' : 'No friends added yet'}
              </p>
            </Card>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

interface FriendCardProps {
  friend: any;
  onRemove: () => void;
}

function FriendCard({ friend, onRemove }: FriendCardProps) {
  return (
    <Card 
      className="p-4 bg-secondary flex items-center gap-3"
      tabIndex={0}
    >
      <AvatarWithStatus
        src={friend.avatar}
        username={friend.username}
        status={friend.status}
      />
      
      <div className="flex-1 min-w-0">
        <div className="font-semibold text-white">
          {friend.username}
        </div>
        <div className="text-xs text-primary">
          {friend.status === 'online' && 'Online'}
          {friend.status === 'watching' && 'Watching now'}
          {friend.status === 'offline' && 'Offline'}
        </div>
      </div>
      
      <Dialog>
        <DialogTrigger asChild>
          <Button 
            size="icon" 
            variant="ghost" 
            className="text-gray-400 hover:text-red-400 hover:bg-red-900/20"
          >
            <Trash2 size={18} />
          </Button>
        </DialogTrigger>
        <DialogContent className="bg-secondary border-gray-700">
          <DialogHeader>
            <DialogTitle className="text-white">Remove Friend</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <p className="text-gray-300">
              Are you sure you want to remove <span className="font-semibold text-white">{friend.username}</span> from your friends list?
            </p>
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline" className="text-white border-white/30">
                Cancel
              </Button>
            </DialogClose>
            <Button 
              className="bg-red-500 hover:bg-red-600 text-white"
              onClick={onRemove}
            >
              Remove
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
} 