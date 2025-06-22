'use client';

import { useState, useEffect, useRef } from 'react';

export default function LiveTime() {
  const [time, setTime] = useState<string>('');
  const prevTimeRef = useRef<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const newTime = now.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      });

      // Only update if the time string has actually changed
      if (newTime !== prevTimeRef.current) {
        prevTimeRef.current = newTime;
        setTime(newTime);
      }
    };

    // Initial update
    updateTime();

    // Then update every 30 seconds (minute accuracy is enough and reduces render frequency)
    const interval = setInterval(updateTime, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="text-base font-medium text-white px-3 py-1.5 rounded-lg bg-black/50">
      {time}
    </div>
  );
} 