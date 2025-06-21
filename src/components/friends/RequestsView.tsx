import { Button } from "@/components/ui/button";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";

interface Request {
  id: string;
  username: string;
  avatar?: string;
}

interface Props {
  requests: Request[];
  onAccept: (id: string) => void;
  onReject: (id: string) => void;
}

export default function RequestsView({ requests, onAccept, onReject }: Props) {
  if (requests.length === 0) {
    return <div className="text-center text-gray-400">No pending requests.</div>;
  }
  return (
    <div className="space-y-4">
      {requests.map((req) => (
        <div key={req.id} className="flex items-center justify-between bg-white/5 p-4 rounded-xl">
          <div className="flex items-center gap-4">
            <Avatar className="size-12">
              {req.avatar ? (
                <AvatarImage src={req.avatar} alt={req.username} />
              ) : (
                <AvatarFallback>{req.username[0]}</AvatarFallback>
              )}
            </Avatar>
            <div className="font-semibold text-white text-lg">@{req.username}</div>
          </div>
          <div className="flex gap-2">
            <Button size="sm" onClick={() => onAccept(req.id)} className="bg-green-600 hover:bg-green-500 text-white">
              Accept
            </Button>
            <Button size="sm" onClick={() => onReject(req.id)} variant="destructive">
              Reject
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
} 