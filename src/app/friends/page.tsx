import dynamic from 'next/dynamic';

const FriendsPage = dynamic(() => import('@/components/friends/FriendsPage'), {
  ssr: true,
});

export default function Friends() {
  return <FriendsPage />;
} 