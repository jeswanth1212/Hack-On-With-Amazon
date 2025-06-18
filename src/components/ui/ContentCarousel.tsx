'use client';

import { ReactNode } from 'react';
import { Carousel, CarouselContent, CarouselItem, CarouselNext, CarouselPrevious } from "@/components/ui/carousel";

interface ContentCarouselProps {
  title: string;
  children: ReactNode;
  slidesToShow?: number;
  autoplay?: boolean;
  className?: string;
  compact?: boolean;
}

export default function ContentCarousel({
  title,
  children,
  slidesToShow = 5,
  autoplay = false,
  className,
  compact = false,
}: ContentCarouselProps) {
  return (
    <div className={`mb-8 ${className}`}>
      <h2 className="text-2xl font-bold mb-4 px-4 text-white">{title}</h2>
      <Carousel
        opts={{
          align: "start",
          loop: true,
        }}
        className="w-full"
      >
        <CarouselContent className="-ml-2 md:-ml-4">
          {Array.isArray(children) ? 
            children.map((child, index) => (
              <CarouselItem 
                key={index} 
                className="pl-2 md:pl-4" 
                style={{
                  flex: `0 0 ${100/slidesToShow}%`,
                  maxWidth: `${100/slidesToShow}%`,
                  ...(compact ? { height: '140px' } : {})
                }}
              >
                {child}
              </CarouselItem>
            )) : 
            <CarouselItem className="pl-2 md:pl-4">{children}</CarouselItem>
          }
        </CarouselContent>
        <div className="hidden md:block">
          <CarouselPrevious className="left-2 bg-background/80 hover:bg-background" />
          <CarouselNext className="right-2 bg-background/80 hover:bg-background" />
        </div>
      </Carousel>
    </div>
  );
} 