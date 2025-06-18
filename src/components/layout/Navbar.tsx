'use client';

import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import LiveTime from '@/components/ui/LiveTime';
import {
  User,
  Tv2,
  Users,
  Heart,
} from "lucide-react";

interface NavItemProps {
  icon: React.ReactNode;
  label: string;
  onClick?: () => void;
}

const NavItem = ({ icon, label, onClick }: NavItemProps) => {
  const [showLabel, setShowLabel] = useState(false);

  return (
    <div
      className="nav-item"
      onMouseEnter={() => setShowLabel(true)}
      onMouseLeave={() => setShowLabel(false)}
    >
      <div className={cn(
        "flex items-center px-3 py-2 rounded-lg transition-all duration-300",
        showLabel ? "bg-white/10" : "bg-transparent"
      )}>
        <div className={cn(
          "transition-transform duration-300",
          showLabel ? "transform -translate-x-1" : ""
        )}>
          {icon}
        </div>
        
        <div className={cn(
          "ml-2 text-xs text-white whitespace-nowrap overflow-hidden transition-all duration-300",
          showLabel ? "max-w-24 opacity-100" : "max-w-0 opacity-0"
        )}>
          {label}
        </div>
      </div>
    </div>
  );
};

export default function Navbar() {
  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-b from-black/90 via-black/70 to-transparent">
      <header className="container flex items-center justify-center py-4 mb-8">
        <div className="flex items-center justify-between w-full max-w-6xl">
          {/* Left Section */}
          <div className="flex gap-4">
            <NavItem icon={<User size={24} className="text-white" />} label="Profile" />
          </div>

          {/* Middle Section */}
          <div className="flex gap-6">
            <NavItem icon={<Tv2 size={24} className="text-white" />} label="Live TV" />
            <NavItem icon={<Users size={24} className="text-white" />} label="Friends" />
            <NavItem icon={<Heart size={24} className="text-white" />} label="My List" />
          </div>

          {/* Right Section */}
          <div className="flex gap-4 items-center">
            <LiveTime />
          </div>
        </div>
      </header>
    </div>
  );
} 