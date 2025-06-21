import { useState } from "react";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { ThumbsUp, MessageCircle, Share } from "lucide-react";

export interface Activity {
  id: string;
  username: string;
  avatar?: string;
  content: string; // post content or message
  timestamp: number; // epoch ms
  actionLabel?: string;
  likes?: number;
  liked?: boolean;
  comments?: number;
  shares?: number;
}

interface Props {
  currentUser: { username: string; avatar?: string };
  activities: Activity[];
  onAddPost: (content: string) => void;
}

export default function ActivityView({ currentUser, activities, onAddPost }: Props) {
  const [newPost, setNewPost] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPost.trim()) return;
    onAddPost(newPost.trim());
    setNewPost("");
  };

  const relativeTime = (ts: number) => {
    const diff = Date.now() - ts;
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
  };

  return (
    <div className="space-y-6">
      {/* Feed */}
      {activities.length === 0 ? (
        <div className="text-center text-gray-400">No recent activity.</div>
      ) : (
        <div className="space-y-4">
          {activities
            .sort((a, b) => b.timestamp - a.timestamp)
            .map((act) => {
              const [liked, setLiked] = useState(act.liked || false);
              const [likes, setLikes] = useState(act.likes || 0);
              const comments = act.comments || Math.floor(Math.random()*5);
              const shares = act.shares || Math.floor(Math.random()*3);

              const toggleLike = () => {
                if (liked) {
                  setLikes(likes - 1);
                } else {
                  setLikes(likes + 1);
                }
                setLiked(!liked);
              };

              return (
                <div key={act.id} className="bg-white/5 p-4 rounded-xl space-y-3">
                  <div className="flex items-center gap-3">
                    <Avatar className="size-10">
                      {act.avatar ? (
                        <AvatarImage src={act.avatar} alt={act.username} />
                      ) : (
                        <AvatarFallback>{act.username[0]}</AvatarFallback>
                      )}
                    </Avatar>
                    <div className="flex-1 text-white">
                      <span className="font-semibold">@{act.username}</span>
                      <span className="ml-2 text-gray-400 text-xs">{relativeTime(act.timestamp)}</span>
                    </div>
                  </div>
                  <div className="text-white whitespace-pre-wrap">{act.content}</div>

                  {/* Actions */}
                  <div className="flex gap-8 pt-2 text-gray-400 text-sm">
                    <button className="flex items-center gap-1 hover:text-primary" onClick={toggleLike} type="button">
                      <ThumbsUp size={16} className={liked ? 'fill-primary text-primary' : ''} /> {likes}
                    </button>
                    <button className="flex items-center gap-1 hover:text-secondary" type="button">
                      <MessageCircle size={16} /> {comments}
                    </button>
                    <button className="flex items-center gap-1 hover:text-secondary" type="button">
                      <Share size={16} /> {shares}
                    </button>
                  </div>
                </div>
              );
            })}
        </div>
      )}

      {/* Composer sticky at bottom */}
      <form onSubmit={handleSubmit} className="bg-white/5 backdrop-blur sticky bottom-0 left-0 right-0 p-4 flex flex-col gap-3">
        <div className="flex items-start gap-3">
          <Avatar className="size-10">
            {currentUser.avatar ? (
              <AvatarImage src={currentUser.avatar} alt={currentUser.username} />
            ) : (
              <AvatarFallback>{currentUser.username[0]}</AvatarFallback>
            )}
          </Avatar>
          <textarea
            className="flex-1 bg-transparent resize-none focus:outline-none text-white placeholder:text-gray-400"
            placeholder="Share something with your friends..."
            rows={2}
            value={newPost}
            onChange={(e) => setNewPost(e.target.value)}
          />
        </div>
        <div className="flex justify-end">
          <Button size="sm" type="submit" disabled={!newPost.trim()}>
            Post
          </Button>
        </div>
      </form>
    </div>
  );
} 