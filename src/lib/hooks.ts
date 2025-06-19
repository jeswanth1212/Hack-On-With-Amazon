'use client';

import { useState, useEffect } from 'react';

/**
 * Hook to handle keyboard events for TV-style navigation
 */
export function useKeyboardNavigation(
  options: {
    onEscape?: () => void;
    onEnter?: () => void;
    onArrowUp?: () => void;
    onArrowDown?: () => void;
    onArrowLeft?: () => void;
    onArrowRight?: () => void;
    disabled?: boolean;
  }
) {
  useEffect(() => {
    if (options.disabled) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'Escape':
          options.onEscape?.();
          break;
        case 'Enter':
          options.onEnter?.();
          break;
        case 'ArrowUp':
          options.onArrowUp?.();
          break;
        case 'ArrowDown':
          options.onArrowDown?.();
          break;
        case 'ArrowLeft':
          options.onArrowLeft?.();
          break;
        case 'ArrowRight':
          options.onArrowRight?.();
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [options]);
}

// Hook for handling keyboard navigation for Fire TV remote
export function useRemoteNavigation() {
  const [focusIndex, setFocusIndex] = useState(0);
  const [focusableElements, setFocusableElements] = useState<HTMLElement[]>([]);
  
  // Find all focusable elements
  useEffect(() => {
    const focusable = Array.from(
      document.querySelectorAll(
        'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
      ) 
    ) as HTMLElement[];
    
    setFocusableElements(focusable);
  }, []);
  
  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (focusableElements.length === 0) return;
      
      let newIndex = focusIndex;
      
      switch (event.key) {
        case 'ArrowUp':
          event.preventDefault();
          newIndex = Math.max(0, focusIndex - 1);
          break;
        case 'ArrowDown':
          event.preventDefault();
          newIndex = Math.min(focusableElements.length - 1, focusIndex + 1);
          break;
        case 'ArrowLeft':
          // For horizontal navigation within groups
          break;
        case 'ArrowRight':
          // For horizontal navigation within groups
          break;
        default:
          return;
      }
      
      if (newIndex !== focusIndex) {
        setFocusIndex(newIndex);
        focusableElements[newIndex]?.focus();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [focusIndex, focusableElements]);
  
  return { focusIndex };
} 