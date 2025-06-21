'use client';

import { Button } from "@/components/ui/button";
import { Carousel, CarouselContent, CarouselItem } from "@/components/ui/carousel";
import { Play, Info } from "lucide-react";
import { useEffect, useState } from "react";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import { useRouter } from 'next/navigation';

interface FeaturedContent {
  id: string | number;
  title: string;
  description: string;
  imageUrl: string;
  provider?: string;
  rating?: number;
  releaseDate?: string;
  genres?: string | string[];
}

interface HeroBannerProps {
  featuredContent: FeaturedContent[];
}

export default function HeroBanner({ featuredContent }: HeroBannerProps) {
  const [api, setApi] = useState<any>();
  const [current, setCurrent] = useState(0);
  const router = useRouter();
  
  // Set up auto-rotation
  useEffect(() => {
    if (!api) return;
    
    const interval = setInterval(() => {
      // Check if we're at the last slide, if so, go to the first slide
      // otherwise go to the next slide
      const isLastSlide = current === featuredContent.length - 1;
      if (isLastSlide) {
        api.scrollTo(0);
      } else {
        api.scrollNext();
      }
    }, 5000);
    
    // Update current slide index when it changes
    const onSelect = () => {
      setCurrent(api.selectedScrollSnap());
    };
    
    api.on("select", onSelect);
    
    return () => {
      clearInterval(interval);
      api.off("select", onSelect);
    };
  }, [api, current, featuredContent.length]);

  return (
    <Carousel setApi={setApi} className="w-full" opts={{ loop: true }}>
      <CarouselContent>
        {featuredContent.map((item) => (
          <CarouselItem key={item.id} className="relative">
            <AspectRatio ratio={16/7} className="w-full">
              <div className="w-full h-full relative overflow-hidden">
                <img 
                  src={item.imageUrl} 
                  alt={item.title} 
                  className="w-full h-full object-cover"
                />
                <div className="hero-overlay flex flex-col justify-end p-6 lg:p-12 pb-[8%] h-full">
                  {item.provider && (
                    <span className="text-sm text-muted-foreground mb-1">
                      {item.provider}
                    </span>
                  )}
                  <h2 className="text-4xl md:text-5xl font-extrabold text-white mb-2 drop-shadow-lg">
                    {item.title}
                  </h2>
                  <div className="flex flex-wrap items-center gap-4 mb-6">
                    {typeof item.rating === 'number' && (
                      <span className="text-yellow-400 font-semibold text-lg flex items-center">
                        ★ {item.rating.toFixed(1)}
                      </span>
                    )}
                    {item.releaseDate && (
                      <span className="text-white/90 text-base">
                        {item.releaseDate.slice(0, 4)}
                      </span>
                    )}
                    {item.genres && (
                      <span className="text-white/80 text-base">
                        {Array.isArray(item.genres)
                          ? item.genres.join(', ')
                          : item.genres}
                      </span>
                    )}
                  </div>
                  <div className="flex gap-4">
                    <Button className="bg-white text-background hover:bg-white/90" size="lg" onClick={() => router.push(`/movie/${item.id}`)}>
                      <Play className="mr-2 h-5 w-5" /> Watch Now
                    </Button>
                    <Button variant="outline" className="border-white text-white hover:bg-white/10" size="lg" onClick={() => router.push(`/movie/${item.id}`)}>
                      <Info className="mr-2 h-5 w-5" /> Learn More
                    </Button>
                  </div>
                </div>
              </div>
            </AspectRatio>
          </CarouselItem>
        ))}
      </CarouselContent>
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-1">
        {featuredContent.map((_, index) => (
          <button
            key={index}
            className={`w-2 h-2 rounded-full transition-all ${
              current === index
                ? "bg-white w-4"
                : "bg-white/50"
            }`}
            onClick={() => api?.scrollTo(index)}
            aria-label={`Go to slide ${index + 1}`}
          />
        ))}
      </div>
    </Carousel>
  );
} 