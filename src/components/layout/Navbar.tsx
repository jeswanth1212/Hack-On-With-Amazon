'use client';

import { useState, useEffect } from 'react';
import { cn } from "@/lib/utils";
import LiveTime from '@/components/ui/LiveTime';
import {
  User,
  Tv2,
  Users,
  Heart,
  Search,
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
      onClick={onClick}
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
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const isScrolled = window.scrollY > 50;
      if (isScrolled !== scrolled) {
        setScrolled(isScrolled);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, [scrolled]);

  return (
    <div className={cn(
      "fixed top-0 left-0 right-0 z-50 transition-all duration-300 px-8 py-4",
      scrolled 
        ? "bg-background/80 backdrop-blur-md" 
        : "bg-gradient-to-b from-black/90 via-black/70 to-transparent"
    )}>
      <div className="flex items-center justify-between w-full">
        {/* Left Section - Profile only */}
        <div>
          <NavItem icon={<User size={24} className="text-white" />} label="Profile" />
        </div>

        {/* Middle Section - Search, Live TV, Friends, My List */}
        <div className="flex gap-6">
          <NavItem icon={<Search size={24} className="text-white" />} label="Search" />
          <NavItem icon={<Tv2 size={24} className="text-white" />} label="Live TV" />
          <NavItem icon={<Users size={24} className="text-white" />} label="Friends" />
          <NavItem icon={<Heart size={24} className="text-white" />} label="My List" />
        </div>

        {/* Right Section - Time (positioned at the very right) */}
        <div>
          <LiveTime />
        </div>
      </div>
    </div>
  );
} 