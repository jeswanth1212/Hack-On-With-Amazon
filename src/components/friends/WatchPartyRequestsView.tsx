import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/hooks';
import { getWatchPartyInvites, acceptWatchPartyInvite, WatchPartyInvite } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';

export default function WatchPartyRequestsView() {
  const { user } = useAuth();
  const router = useRouter();
  const [invites, setInvites] = useState<WatchPartyInvite[]>([]);
  const [loading, setLoading] = useState(false);

  const loadInvites = async () => {
    if (!user) return;
    setLoading(true);
    const data = await getWatchPartyInvites(user.user_id);
    setInvites(data);
    setLoading(false);
  };

  useEffect(() => {
    loadInvites();
  }, [user]);

  const handleAccept = async (partyId: number, tmdbId: number) => {
    if (!user) return;
    const ok = await acceptWatchPartyInvite(partyId, user.user_id);
    if (ok) {
      router.push(`/watch-party/session?party=${partyId}`);
    }
  };

  if (!user) return <p className="text-center text-gray-400 py-6">Please login to view invites.</p>;

  return (
    <div className="py-6">
      {loading ? (
        <p className="text-center text-gray-400">Loading...</p>
      ) : invites.length === 0 ? (
        <p className="text-center text-gray-400">No watch party invites.</p>
      ) : (
        <div className="space-y-4">
          {invites.map(invite => (
            <div key={invite.party_id} className="bg-white/5 rounded-lg p-4 flex items-center justify-between">
              <div>
                <p className="text-white">Host: {invite.host_id}</p>
                <p className="text-sm text-gray-400">Movie ID: {invite.tmdb_id}</p>
              </div>
              <Button onClick={() => handleAccept(invite.party_id, invite.tmdb_id)}>Accept</Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
} 