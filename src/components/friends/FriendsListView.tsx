import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";

interface Friend {
  id: string;
  username: string;
  avatar?: string;
  points: number;
}

interface Props {
  friends: Friend[];
  onRemove: (id: string) => void;
}

export default function FriendsListView({ friends, onRemove }: Props) {
  const [selected, setSelected] = useState<string[]>([]);

  const toggleSelect = (id: string) => {
    setSelected((prev) => (prev.includes(id) ? prev.filter((f) => f !== id) : [...prev, id]));
  };

  const handleInvite = () => {
    if (selected.length === 0) return;
    alert(`Watch party invite created for ${selected.length} friend(s): ${selected.join(', ')}`);
    setSelected([]);
  };

  if (friends.length === 0) return <div className="text-center text-gray-400">No friends yet.</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <Button onClick={handleInvite} disabled={selected.length === 0} className="bg-primary text-primary-foreground">
          Invite to Watch Party
        </Button>
      </div>
      <div className="space-y-4">
        {friends.map((friend) => {
          const isSelected = selected.includes(friend.id);
          return (
            <div key={friend.id} className={`flex items-center justify-between bg-white/5 p-4 rounded-xl ${isSelected ? 'ring-2 ring-primary' : ''}`}>
              <div className="flex items-center gap-4 cursor-pointer" onClick={() => toggleSelect(friend.id)}>
                <Avatar className="size-12">
                  {friend.avatar ? (
                    <AvatarImage src={friend.avatar} alt={friend.username} />
                  ) : (
                    <AvatarFallback>{friend.username[0]}</AvatarFallback>
                  )}
                </Avatar>
                <div>
                  <div className="font-semibold text-white text-lg">@{friend.username}</div>
                  <div className="text-sm text-yellow-400">Watch Buddy Points: {friend.points}</div>
                </div>
              </div>
              <Button size="sm" variant="destructive" onClick={() => onRemove(friend.id)}>
                Remove
              </Button>
            </div>
          );
        })}
      </div>
    </div>
  );
} 