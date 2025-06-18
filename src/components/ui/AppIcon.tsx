'use client';

import { cn } from "@/lib/utils";

interface AppIconProps {
  id: string | number;
  name: string;
  iconFile: string;
  backgroundColor?: string;
  onClick?: () => void;
}

export default function AppIcon({
  id,
  name,
  iconFile,
  onClick,
}: AppIconProps) {
  return (
    <div className="h-full w-full rounded-2xl overflow-hidden bg-black/10 hover:scale-110 transition-transform duration-200 border border-gray-800">
      <div 
        className="h-full w-full flex items-center justify-center cursor-pointer"
        onClick={onClick}
      >
        <img 
          src={`/apps/${iconFile}`} 
          alt={name} 
          className="h-full w-full object-cover"
        />
      </div>
    </div>
  );
} 