import React from 'react';

interface WatchPartyBoxProps {
  children: React.ReactNode;
}

export default function WatchPartyBox({ children }: WatchPartyBoxProps) {
  return (
    <div className="mt-20 mx-auto w-full max-w-screen-xl bg-black/70 border-2 border-yellow-400 rounded-2xl shadow-2xl p-4 md:p-8 backdrop-blur-md">
      <h2 className="text-2xl md:text-3xl font-extrabold text-yellow-400 mb-6 text-center drop-shadow-lg">
        Watch Party
      </h2>
      {children}
    </div>
  );
} 