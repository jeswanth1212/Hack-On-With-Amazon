'use client';

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

interface AvatarWithStatusProps {
  src: string;
  username: string;
  size?: 'sm' | 'md' | 'lg';
  status?: 'online' | 'offline' | 'watching' | undefined;
}

export function AvatarWithStatus({
  src,
  username,
  size = 'md',
  status
}: AvatarWithStatusProps) {
  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-12 w-12'
  };

  const statusSizeClasses = {
    sm: 'h-2.5 w-2.5',
    md: 'h-3 w-3',
    lg: 'h-3.5 w-3.5'
  };

  const statusColorClasses = {
    online: 'bg-green-500',
    offline: 'bg-gray-400',
    watching: 'bg-primary'
  };

  const fallbackText = username
    .split(' ')
    .map(part => part[0])
    .join('')
    .slice(0, 2);

  return (
    <div className="relative inline-block">
      <Avatar className={cn(sizeClasses[size], "border-2 border-secondary")}>
        <AvatarImage src={src} alt={username} />
        <AvatarFallback className="bg-secondary text-white">
          {fallbackText}
        </AvatarFallback>
      </Avatar>
      {status && (
        <span 
          className={cn(
            "absolute bottom-0 right-0 rounded-full ring-2 ring-background",
            statusColorClasses[status],
            statusSizeClasses[size]
          )}
        />
      )}
    </div>
  );
} 