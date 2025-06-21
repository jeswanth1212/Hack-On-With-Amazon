'use client';

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { ArrowUpRight } from "lucide-react";
import { useState } from "react";
import { useRouter } from 'next/navigation';

interface ContentCardProps {
  id: string | number;
  title: string;
  imageUrl: string;
  year?: string;
  rating?: string;
  source?: string;
  onClick?: () => void;
  className?: string;
  showHoverArrow?: boolean;
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
  showHoverArrow = true,
}: ContentCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const router = useRouter();

  const handleClick = () => {
    if (onClick) return onClick();
    router.push(`/movie/${id}`);
  };

  return (
    <div className="h-full w-full">
      <div 
        className={
          `group relative h-full w-full aspect-[2/3] overflow-visible rounded-lg cursor-pointer transition-all duration-300 ${
            isHovered ? "scale-[1.03] z-10 ring-2 ring-blue-500" : ""
          } ${className}`
        }
        onClick={handleClick}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Image container */}
        <div className="absolute inset-0 bg-black rounded-lg overflow-hidden">
          <img 
            src={imageUrl} 
            alt={title} 
            className="h-full w-full object-cover"
          />
        </div>
        {/* Hover overlay */}
        {showHoverArrow && (
          <div className="absolute inset-0 grid place-content-center">
            <div className="grid h-10 w-10 scale-0 place-content-center rounded-full bg-primary text-primary-foreground transition-transform ease-in-out group-hover:scale-100">
              <ArrowUpRight size={24} />
            </div>
          </div>
        )}
        {/* Fade overlay for text visibility on hover */}
        <div className="absolute left-0 right-0 bottom-0 h-16 pointer-events-none rounded-b-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300"
             style={{background: 'linear-gradient(to top, rgba(0,0,0,0.6) 80%, rgba(0,0,0,0) 100%)'}} />
        {/* Content info */}
        <div className="absolute bottom-0 left-0 right-0 p-3 opacity-0 transition-opacity group-hover:opacity-100">
          <h3 className="text-sm font-bold text-white line-clamp-1">{title}</h3>
          <div className="flex items-center justify-between mt-1">
            <div className="flex items-center gap-2">
              {year && <span className="text-xs text-white/80">{year}</span>}
              {rating && (
                <div className="flex items-center">
                  <span className="text-xs text-white/80">★ {rating}</span>
                </div>
              )}
            </div>
            {source && (
              <div className="text-xs text-white/80 uppercase">{source}</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 