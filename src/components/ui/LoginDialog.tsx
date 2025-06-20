'use client';

import { useState } from 'react';
import { Button } from './button';
import { Input } from './input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from './dialog';
import { useAuth } from '@/lib/hooks';

interface LoginDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function LoginDialog({ isOpen, onClose }: LoginDialogProps) {
  const { login, error, loading } = useAuth();
  const [userId, setUserId] = useState('');
  const [showRegistration, setShowRegistration] = useState(false);
  const [registrationData, setRegistrationData] = useState({
    user_id: '',
    age: '',
    location: ''
  });

  const handleLogin = async () => {
    if (!userId.trim()) return;
    
    const success = await login(userId);
    if (success) {
      onClose();
    }
  };

  const handleRegister = () => {
    setShowRegistration(true);
  };

  const handleRegistrationSubmit = async () => {
    // In a real implementation, you would send this data to the backend
    // For now, we'll just simulate a successful login
    const success = await login(registrationData.user_id);
    if (success) {
      onClose();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setRegistrationData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <Dialog open={isOpen} onOpenChange={open => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{showRegistration ? 'Register New User' : 'Login'}</DialogTitle>
          <DialogDescription>
            {showRegistration 
              ? 'Enter your details to create a new account.'
              : 'Enter your user ID to login and get personalized recommendations.'}
          </DialogDescription>
        </DialogHeader>
        
        {showRegistration ? (
          // Registration form
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <label htmlFor="user_id">User ID</label>
              <Input 
                id="user_id" 
                name="user_id"
                placeholder="Enter a unique user ID" 
                value={registrationData.user_id}
                onChange={handleInputChange}
              />
            </div>
            <div className="grid gap-2">
              <label htmlFor="age">Age</label>
              <Input 
                id="age" 
                name="age"
                type="number" 
                placeholder="Enter your age" 
                value={registrationData.age}
                onChange={handleInputChange}
              />
            </div>
            <div className="grid gap-2">
              <label htmlFor="location">Location</label>
              <Input 
                id="location" 
                name="location"
                placeholder="Enter your location" 
                value={registrationData.location}
                onChange={handleInputChange}
              />
            </div>
          </div>
        ) : (
          // Login form
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <label htmlFor="userId">User ID</label>
              <Input 
                id="userId" 
                placeholder="Enter your user ID" 
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
              />
            </div>
            {error && (
              <p className="text-red-500 text-sm">{error}</p>
            )}
          </div>
        )}
        
        <DialogFooter className="sm:justify-between">
          {showRegistration ? (
            <>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowRegistration(false)}
              >
                Back to Login
              </Button>
              <Button 
                type="submit"
                disabled={loading || !registrationData.user_id}
                onClick={handleRegistrationSubmit}
              >
                {loading ? 'Registering...' : 'Register'}
              </Button>
            </>
          ) : (
            <>
              <Button
                type="button"
                variant="outline"
                onClick={handleRegister}
              >
                New User?
              </Button>
              <Button 
                type="submit"
                disabled={loading || !userId.trim()}
                onClick={handleLogin}
              >
                {loading ? 'Logging in...' : 'Login'}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
} 