import { useState } from 'react';
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface User {
  id: string;
  username: string;
  email: string;
  avatar?: string;
  bio?: string;
}

interface Props {
  onSendRequest: (user: User) => void;
}

const MOCK_USERS: User[] = [
  { id: 'user-123', username: 'User123', email: 'user123@example.com', avatar: '/assets/avatars/avatar-1.jpg', bio: 'Movie buff and series addict.' },
  { id: 'user-456', username: 'MovieFan', email: 'moviefan@example.com', avatar: '/assets/avatars/avatar-2.jpg', bio: 'Always up for a watch party!' },
  { id: 'user-789', username: 'SeriesGuru', email: 'seriesguru@example.com', avatar: '/assets/avatars/avatar-3.jpg', bio: 'Binge-watcher supreme.' },
];

export default function SearchUsersView({ onSendRequest }: Props) {
  const [query, setQuery] = useState('');

  const filtered = query.length === 0
    ? []
    : MOCK_USERS.filter((u) => {
        const q = query.replace(/^@/, '').toLowerCase();
        return (
          u.username.toLowerCase().includes(q) ||
          u.email.toLowerCase().includes(q)
        );
      });

  return (
    <div className="space-y-6">
      <Input
        placeholder="Search by @User123 or email"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="text-lg px-4 py-3"
      />

      <div className="space-y-4">
        {filtered.map((user) => (
          <div key={user.id} className="flex items-center justify-between bg-white/5 p-4 rounded-xl">
            <div className="flex items-center gap-4">
              <Avatar className="size-12">
                {user.avatar ? (
                  <AvatarImage src={user.avatar} alt={user.username} />
                ) : (
                  <AvatarFallback>{user.username[0]}</AvatarFallback>
                )}
              </Avatar>
              <div>
                <div className="font-semibold text-white text-lg">@{user.username}</div>
                {user.bio && <div className="text-sm text-gray-400">{user.bio}</div>}
              </div>
            </div>
            <Button onClick={() => onSendRequest(user)} variant="secondary">
              Send Request
            </Button>
          </div>
        ))}
        {query && filtered.length === 0 && (
          <div className="text-center text-gray-400">No users found.</div>
        )}
      </div>
    </div>
  );
} 