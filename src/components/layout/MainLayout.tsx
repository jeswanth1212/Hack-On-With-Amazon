'use client';

import { ReactNode } from 'react';
import Navbar from './Navbar';
import Chatbot from '@/components/ui/Chatbot';
import { useState } from 'react';

interface MainLayoutProps {
  children: ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
  const [searchOpen, setSearchOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar
        onSearchOpen={() => setSearchOpen(true)}
        onSearchClose={() => setSearchOpen(false)}
      />
      <Chatbot zIndex={searchOpen ? 10 : 1000} />
      <main>
        {children}
      </main>
    </div>
  );
} 