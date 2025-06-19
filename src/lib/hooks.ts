'use client';

import { useState, useEffect, useCallback } from 'react';

/**
 * A hook for handling keyboard navigation events
 */
export function useKeyboardNavigation({
  disabled = false,
  onEnter,
  onEscape,
  onArrowUp,
  onArrowDown,
  onArrowLeft,
  onArrowRight,
}: {
  disabled?: boolean;
  onEnter?: () => void;
  onEscape?: () => void;
  onArrowUp?: () => void;
  onArrowDown?: () => void;
  onArrowLeft?: () => void;
  onArrowRight?: () => void;
}) {
  useEffect(() => {
    if (disabled) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'Enter':
          if (onEnter) {
            e.preventDefault();
            onEnter();
          }
          break;
        case 'Escape':
          if (onEscape) {
            e.preventDefault();
            onEscape();
          }
          break;
        case 'ArrowUp':
          if (onArrowUp) {
            e.preventDefault();
            onArrowUp();
          }
          break;
        case 'ArrowDown':
          if (onArrowDown) {
            e.preventDefault();
            onArrowDown();
          }
          break;
        case 'ArrowLeft':
          if (onArrowLeft) {
            e.preventDefault();
            onArrowLeft();
          }
          break;
        case 'ArrowRight':
          if (onArrowRight) {
            e.preventDefault();
            onArrowRight();
          }
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [disabled, onEnter, onEscape, onArrowUp, onArrowDown, onArrowLeft, onArrowRight]);
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