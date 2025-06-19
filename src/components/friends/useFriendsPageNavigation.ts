'use client';

import { useState, useEffect, useCallback } from 'react';

export function useFriendsPageNavigation() {
  const [activeTabIndex, setActiveTabIndex] = useState(0);
  const [activeItemIndex, setActiveItemIndex] = useState(0);
  
  // Handle tab switching via keyboard
  const handleTabNavigation = useCallback((direction: 'next' | 'prev') => {
    if (direction === 'next') {
      setActiveTabIndex((prev) => (prev < 2 ? prev + 1 : prev));
    } else {
      setActiveTabIndex((prev) => (prev > 0 ? prev - 1 : prev));
    }
    // Reset item index when changing tabs
    setActiveItemIndex(0);
  }, []);

  // Handle item selection within a tab
  const handleItemNavigation = useCallback((direction: 'next' | 'prev', itemCount: number) => {
    if (direction === 'next') {
      setActiveItemIndex((prev) => (prev < itemCount - 1 ? prev + 1 : prev));
    } else {
      setActiveItemIndex((prev) => (prev > 0 ? prev - 1 : prev));
    }
  }, []);
  
  // Connect to keyboard events
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowLeft':
          e.preventDefault();
          handleTabNavigation('prev');
          break;
        case 'ArrowRight':
          e.preventDefault();
          handleTabNavigation('next');
          break;
        case 'ArrowUp':
          e.preventDefault();
          handleItemNavigation('prev', 10); // Assume max 10 items for now
          break;
        case 'ArrowDown':
          e.preventDefault();
          handleItemNavigation('next', 10); // Assume max 10 items for now
          break;
        default:
          break;
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleTabNavigation, handleItemNavigation]);
  
  return {
    activeTabIndex,
    activeItemIndex,
    setActiveTabIndex,
    setActiveItemIndex
  };
}