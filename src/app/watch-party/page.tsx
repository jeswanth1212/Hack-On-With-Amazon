'use client';

import MainLayout from '@/components/layout/MainLayout';
import Link from 'next/link';
import { Music2, Clapperboard } from 'lucide-react';
import { useState } from 'react';
import SearchOverlay from '@/components/ui/SearchOverlay';

export default function WatchPartyPage() {
  const [searchOpen, setSearchOpen] = useState(false);
  return (
    <MainLayout>
      <div className={searchOpen ? 'hidden' : 'min-h-screen flex flex-col md:flex-row items-center justify-center gap-28 md:gap-32 py-24'}>
        {/* Jam with Friends Card */}
        <Link href="#" className="group">
          <div className="card w-[260px] h-[260px] md:w-[340px] md:h-[340px]">
            <div className="circle" />
            <div className="circle" />
            <div className="card-inner flex flex-col items-center justify-center text-center p-6 gap-4">
              <Music2 size={64} className="text-yellow-400 group-hover:scale-110 transition-transform duration-300" />
              <span className="text-xl md:text-2xl font-semibold text-white group-hover:scale-105 transition-transform duration-300">
                Jam with Friends
              </span>
            </div>
          </div>
        </Link>

        {/* Watch Movie with Friends Card */}
        <button onClick={() => setSearchOpen(true)} className="group focus:outline-none">
          <div className="card w-[260px] h-[260px] md:w-[340px] md:h-[340px]">
            <div className="circle" />
            <div className="circle" />
            <div className="card-inner flex flex-col items-center justify-center text-center p-6 gap-4">
              <Clapperboard size={64} className="text-yellow-400 group-hover:scale-110 transition-transform duration-300" />
              <span className="text-xl md:text-2xl font-semibold text-white group-hover:scale-105 transition-transform duration-300">
                Watch Movie with Friends
              </span>
            </div>
          </div>
        </button>

      </div>

      {/* Search Overlay */}
      <SearchOverlay isOpen={searchOpen} onClose={() => setSearchOpen(false)} partyMode />

      {/* Inject custom styles for the cards */}
      <style jsx global>{`
        /* Card styles from Uiverse.io (adapted) */
        .card {
          transition: all 0.2s;
          position: relative;
          cursor: pointer;
        }
        .card-inner {
          width: inherit;
          height: inherit;
          background: rgba(255, 255, 255, 0.05);
          box-shadow: 0 0 10px rgba(0, 0, 0, 0.25);
          backdrop-filter: blur(10px);
          border-radius: 8px;
        }
        .card:hover {
          transform: scale(1.04) rotate(1deg);
        }
        .circle {
          position: absolute;
          width: 100px;
          height: 100px;
          background: repeating-linear-gradient(48deg, #facc15 0%, #f59e0b 100%);
          border-radius: 35% 30% 75% 30% / 49% 30% 70% 51%;
          animation: move-up6 2s ease-in infinite alternate-reverse;
        }
        .circle:nth-child(1) {
          top: -25px;
          left: -25px;
        }
        .circle:nth-child(2) {
          bottom: -25px;
          right: -25px;
          animation-name: move-down1;
        }
        @keyframes move-up6 {
          to { transform: translateY(-10px); }
        }
        @keyframes move-down1 {
          to { transform: translateY(10px); }
        }
      `}</style>
    </MainLayout>
  );
} 