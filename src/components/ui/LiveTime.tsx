'use client';

import { useState, useEffect } from 'react';

export default function LiveTime() {
  const [time, setTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      // Format: HH:MM AM/PM
      setTime(now.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      }));
    };

    // Update time immediately
    updateTime();
    
    // Then update every second
    const interval = setInterval(updateTime, 1000);
    
    // Cleanup on unmount
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="text-base font-medium text-white px-3 py-1.5 rounded-lg bg-black/50">
      {time}
    </div>
  );
} 