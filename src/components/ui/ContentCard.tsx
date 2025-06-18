'use client';

import { Card } from "@/components/ui/card";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import { cn } from "@/lib/utils";
import { useState } from "react";

interface ContentCardProps {
  id: string | number;
  title: string;
  imageUrl: string;
  year?: string;
  rating?: string;
  source?: string;
  onClick?: () => void;
  className?: string;
}

export default function ContentCard({
  id,
  title,
  imageUrl,
  year,
  rating,
  source,
  onClick,
  className,
}: ContentCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <Card 
      className={cn(
        "content-card border-0 overflow-hidden cursor-pointer rounded-lg mx-auto h-full relative",
        className
      )}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <AspectRatio ratio={2/3}>
        <img 
          src={imageUrl} 
          alt={title} 
          className="w-full h-full object-cover"
        />
        <div className={cn(
          "content-card-overlay flex flex-col justify-end p-3",
          isHovered ? "opacity-100" : "opacity-0"
        )}>
          <div className="flex justify-between items-end">
            <div className="flex-1">
              <h3 className="text-sm font-bold text-white line-clamp-2">{title}</h3>
              <div className="flex items-center gap-2 mt-1">
                {year && <span className="text-xs text-white/80">{year}</span>}
                {rating && (
                  <div className="flex items-center">
                    <span className="text-xs text-white/80">★ {rating}</span>
                  </div>
                )}
              </div>
            </div>
            {source && (
              <div className="text-xs text-white/80 uppercase">{source}</div>
            )}
          </div>
        </div>
      </AspectRatio>
    </Card>
  );
} 