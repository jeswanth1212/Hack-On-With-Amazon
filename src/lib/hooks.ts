import { useEffect } from 'react';

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