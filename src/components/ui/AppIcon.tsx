'use client';

import { Card } from "@/components/ui/card";
import { AspectRatio } from "@/components/ui/aspect-ratio";
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
    <Card 
      className="content-card border-0 overflow-hidden cursor-pointer mx-1 h-full bg-transparent"
      onClick={onClick}
    >
      <AspectRatio ratio={16/9}>
        <div className="w-full h-full flex items-center justify-center">
          <img 
            src={`/apps/${iconFile}`} 
            alt={name} 
            className="w-full h-full object-contain"
          />
        </div>
      </AspectRatio>
    </Card>
  );
} 