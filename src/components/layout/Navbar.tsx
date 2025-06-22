'use client';

import { useState, useEffect } from 'react';
import { cn } from "@/lib/utils";
import LiveTime from '@/components/ui/LiveTime';
import SearchOverlay from '@/components/ui/SearchOverlay';
import LoginDialog from '@/components/ui/LoginDialog';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth, useNotifications } from '@/lib/hooks';
import {
  User,
  Tv2,
  Users,
  Heart,
  Search,
  Tv,
  UserCircle2,
  UserPlus,
  LogOut,
  Home,
  Network,
} from "lucide-react";
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";

interface NavItemProps {
  icon: React.ReactNode;
  label: string;
  href?: string;
  onClick?: () => void;
  isActive?: boolean;
  badge?: number;
}

interface NavbarProps {
  onSearchOpen?: () => void;
  onSearchClose?: () => void;
}

const NavItem = ({ icon, label, href, onClick, isActive, badge }: NavItemProps) => {
  const [showLabel, setShowLabel] = useState(false);

  const content = (
    <div
      className={cn(
        "nav-item relative",
        isActive && "bg-white/10 rounded-lg"
      )}
      onMouseEnter={() => setShowLabel(true)}
      onMouseLeave={() => setShowLabel(false)}
      onClick={onClick}
    >
      {badge !== undefined && badge > 0 && (
        <Badge 
          className="absolute -top-2 -right-1 bg-primary text-primary-foreground text-xs min-w-5 h-5 flex items-center justify-center rounded-full z-10"
        >
          {badge > 99 ? '99+' : badge}
        </Badge>
      )}
      <div className={cn(
        "flex items-center px-3 py-2 rounded-lg transition-all duration-300",
        (showLabel || isActive) ? "bg-white/10" : "bg-transparent"
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

  if (href) {
    return (
      <Link href={href}>
        {content}
      </Link>
    );
  }

  return content;
};

export default function Navbar({ onSearchOpen, onSearchClose }: NavbarProps = {}) {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [loginOpen, setLoginOpen] = useState(false);
  const { user, logout } = useAuth();
  const { totalCount, markActivityAsRead } = useNotifications();

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

  useEffect(() => {
    // Mark notifications as read when visiting the friends page
    if (pathname === '/friends') {
      markActivityAsRead();
    }
  }, [pathname]);

  const handleSearchClick = () => {
    setSearchOpen(true);
    if (onSearchOpen) onSearchOpen();
  };

  const handleCloseSearch = () => {
    setSearchOpen(false);
    if (onSearchClose) onSearchClose();
  };

  const handleProfileClick = () => {
    if (!user) {
      setLoginOpen(true);
    }
  };

  return (
    <>
      <div className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300 px-8 py-4",
        scrolled 
          ? "bg-background/80 backdrop-blur-md" 
          : "bg-gradient-to-b from-black/90 via-black/70 to-transparent"
      )}>
        <div className="flex items-center justify-between w-full">
          {/* Left Section - Profile */}
          <div>
            {user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <div className="cursor-pointer">
                    <NavItem 
                      icon={<User size={24} className="text-white" />} 
                      label={`User ${user.user_id}`} 
                    />
                  </div>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-56">
                  <DropdownMenuLabel>My Account</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem disabled>Profile</DropdownMenuItem>
                  <DropdownMenuItem disabled>Settings</DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={logout} className="text-red-500">
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>Log out</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <div onClick={handleProfileClick}>
                <NavItem icon={<User size={24} className="text-white" />} label="Login" />
              </div>
            )}
          </div>

          {/* Middle Section - Search, Live TV, Friends, My List */}
          <div className="flex gap-6">
            <NavItem 
              icon={<Home size={24} className="text-white" />} 
              label="Home"
              href="/"
              isActive={pathname === '/'}
            />
            <NavItem 
              icon={<Search size={24} className="text-white" />} 
              label="Search"
              onClick={handleSearchClick}
            />
            <NavItem 
              icon={<Tv size={24} className="text-white" />} 
              label="Watch Party" 
              href="/watch-party"
              isActive={pathname === '/watch-party'}
            />
            <NavItem 
              icon={<Network size={24} className="text-white" />} 
              label="Ur Network" 
              href="/friends"
              isActive={pathname === '/friends'}
              badge={user ? totalCount : undefined}
            />
            <NavItem icon={<Heart size={24} className="text-white" />} label="My List" />
          </div>

          {/* Right Section - Time (positioned at the very right) */}
          <div>
            <LiveTime />
          </div>
        </div>
      </div>

      <SearchOverlay isOpen={searchOpen} onClose={handleCloseSearch} />
      <LoginDialog isOpen={loginOpen} onClose={() => setLoginOpen(false)} />
    </>
  );
} 