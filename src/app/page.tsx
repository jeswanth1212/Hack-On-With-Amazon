import dynamic from 'next/dynamic';

const HomePage = dynamic(() => import('@/components/home/HomePage'), {
  ssr: true,
});

export default function Home() {
  return <HomePage />;
}
