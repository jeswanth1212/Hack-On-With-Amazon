'use client';

import { useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AvatarWithStatus } from '@/components/ui/avatar-with-status';
import { X } from 'lucide-react';

interface QrCodeOverlayProps {
  onClose: () => void;
}

export default function QrCodeOverlay({ onClose }: QrCodeOverlayProps) {
  // Mock user data - in a real app, this would come from auth context
  const currentUser = {
    username: 'Your Username',
    avatar: '/assets/avatars/user.jpg'
  };

  // Close overlay when ESC key is pressed
  useEffect(() => {
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };
    
    window.addEventListener('keydown', handleEscKey);
    return () => window.removeEventListener('keydown', handleEscKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <Card className="p-8 w-[400px] max-w-[90%] bg-secondary border-gray-700">
        <div className="absolute top-4 right-4">
          <Button
            variant="ghost"
            size="icon"
            className="text-gray-400 hover:text-white hover:bg-white/10"
            onClick={onClose}
          >
            <X size={20} />
          </Button>
        </div>
        
        <div className="flex flex-col items-center space-y-6">
          <h2 className="text-2xl font-bold text-white">Scan to add me as a friend</h2>
          
          {/* QR Code Placeholder */}
          <div className="w-64 h-64 bg-white p-4 rounded-lg flex items-center justify-center">
            <div className="text-black text-xs text-center">
              {/* In a real implementation, we'd use a QR code library */}
              <div className="border-2 border-black w-full h-full flex items-center justify-center">
                QR Code
                <br />
                (Placeholder)
              </div>
            </div>
          </div>
          
          <div className="flex flex-col items-center space-y-2">
            <AvatarWithStatus
              src={currentUser.avatar}
              username={currentUser.username}
              size="lg"
              status="online"
            />
            <span className="text-lg font-medium text-white">{currentUser.username}</span>
          </div>
          
          <Button
            className="bg-primary text-background hover:bg-primary/90 w-full"
            onClick={onClose}
          >
            Close
          </Button>
        </div>
      </Card>
    </div>
  );
} 