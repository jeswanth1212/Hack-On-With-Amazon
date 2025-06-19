'use client';

import { useEffect, useRef, useState } from 'react';
import { Search } from 'lucide-react';
import Image from 'next/image';
import { useKeyboardNavigation } from '@/lib/hooks';

interface SearchOverlayProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SearchOverlay({ isOpen, onClose }: SearchOverlayProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const [inputValue, setInputValue] = useState('');

  // Focus input when overlay opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (overlayRef.current === e.target) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  // TV remote-style keyboard navigation
  useKeyboardNavigation({
    disabled: !isOpen,
    onEscape: onClose,
    onEnter: () => {
      if (inputValue.trim()) {
        // Handle search submission
        console.log(`Search submitted: ${inputValue}`);
        // You can add a search function here
      }
    },
  });

  if (!isOpen) return null;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex justify-center items-start"
      aria-modal="true"
      role="dialog"
    >
      <div className="w-[90%] max-w-2xl mt-24 animate-in fade-in slide-in-from-top duration-300">
        <div className="h-12 flex items-center px-4 gap-3 bg-black/30 backdrop-blur-xl rounded-xl border border-white/20 shadow-[0_0_15px_rgba(255,255,255,0.15)] hover:shadow-[0_0_20px_rgba(255,255,255,0.2)] transition-all duration-300">
          <Search className="text-white/90" size={24} />
          
          <input
            ref={inputRef}
            type="text"
            placeholder="Search..."
            className="flex-grow bg-transparent outline-none text-white placeholder:text-white/60 text-base caret-white focus:ring-0"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            autoFocus
          />
          
          <Image 
            src="/assets/alexa.png" 
            alt="Alexa" 
            width={24} 
            height={24} 
            className="opacity-80 hover:opacity-100 transition-opacity duration-300"
          />
        </div>
      </div>
    </div>
  );
} 