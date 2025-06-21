'use client';

import { ReactNode } from 'react';
import { Carousel, CarouselContent, CarouselItem, CarouselNext, CarouselPrevious } from "@/components/ui/carousel";
import React from 'react';

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
  slidesToShow = 5.5,
  autoplay = false,
  className,
  compact = false,
}: ContentCarouselProps) {
  return (
    <div className={`mb-10 ${className}`}>
      {title && <h2 className="text-2xl font-bold mb-4 pl-8 text-white">{title}</h2>}
      <div className="relative w-full">
        <Carousel
          opts={{
            align: "start",
            loop: false,
          }}
          className="w-full relative"
        >
          <CarouselContent className="ml-0">
            {Array.isArray(children)
              ? children.map((child, index) => (
                  <CarouselItem
                    key={index}
                    className={`${compact ? 'app-carousel-item' : 'movie-carousel-item'} pr-1`}
                    style={{
                      flex: `0 0 ${100 / slidesToShow}%`,
                      maxWidth: `${100 / slidesToShow}%`,
                    }}
                  >
                    <div className={`h-full flex items-center justify-center ${compact ? '' : 'py-2'}`}>
                      {child}
                    </div>
                  </CarouselItem>
                ))
              : <CarouselItem className="pl-2 md:pl-4">{children}</CarouselItem>
            }
          </CarouselContent>
          {/* Overlay navigation arrows */}
          <div className="hidden md:block pointer-events-none">
            <CarouselPrevious className="left-2 bg-background/80 hover:bg-background absolute pointer-events-auto z-20" />
            <CarouselNext className="right-2 bg-background/80 hover:bg-background absolute pointer-events-auto z-20" />
          </div>
        </Carousel>
      </div>
    </div>
  );
} 