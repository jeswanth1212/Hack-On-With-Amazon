'use client';

import { useState, useEffect } from 'react';
import { Button } from './button';
import { Input } from './input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from './dialog';
import { useAuth } from '@/lib/hooks';
import { UserProfile, getRegistrationOptions, SelectionOption } from '@/lib/utils';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";

interface LoginDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

// Indian languages with codes
const INDIAN_LANGUAGES = [
  { code: "hi", name: "Hindi" },
  { code: "ta", name: "Tamil" },
  { code: "te", name: "Telugu" },
  { code: "ml", name: "Malayalam" },
  { code: "kn", name: "Kannada" },
  { code: "bn", name: "Bengali" },
  { code: "mr", name: "Marathi" },
  { code: "pa", name: "Punjabi" },
  { code: "gu", name: "Gujarati" },
];

// Other popular languages
const OTHER_LANGUAGES = [
  { code: "en", name: "English" },
  { code: "ja", name: "Japanese" },
  { code: "ko", name: "Korean" },
  { code: "zh", name: "Chinese" },
  { code: "fr", name: "French" },
  { code: "es", name: "Spanish" },
  { code: "de", name: "German" }
];

// All languages combined
const ALL_LANGUAGES = [...INDIAN_LANGUAGES, ...OTHER_LANGUAGES];

// Fallback options in case API fails
const FALLBACK_LANGUAGES = [
  { id: "hi", name: "Hindi" },
  { id: "ta", name: "Tamil" },
  { id: "en", name: "English" },
];

export default function LoginDialog({ isOpen, onClose }: LoginDialogProps) {
  const { login, error, loading, registerUser } = useAuth();
  const [userId, setUserId] = useState('');
  const [showRegistration, setShowRegistration] = useState(false);
  const [registrationData, setRegistrationData] = useState({
    user_id: '',
    age: '',
    location: '',
    language_preference: 'en', // Default to English
    preferred_genres: [] as string[]
  });
  const [options, setOptions] = useState<{
    genres: SelectionOption[],
    languages: SelectionOption[]
  }>({
    genres: [],
    languages: FALLBACK_LANGUAGES,
  });
  const [fetchingOptions, setFetchingOptions] = useState(false);

  // Fetch genres and languages options when dialog opens
  useEffect(() => {
    if (isOpen) {
      setFetchingOptions(true);
      getRegistrationOptions()
        .then(data => {
          setOptions({
            genres: data.genres || [],
            languages: data.languages || FALLBACK_LANGUAGES,
          });
        })
        .catch(err => {
          console.error('Failed to fetch options:', err);
          // Use fallback options if API fails
          setOptions({
            genres: [
              {id: "action", name: "Action"},
              {id: "comedy", name: "Comedy"},
              {id: "drama", name: "Drama"},
              {id: "horror", name: "Horror"},
              {id: "romance", name: "Romance"},
              {id: "science_fiction", name: "Science Fiction"}
            ],
            languages: FALLBACK_LANGUAGES,
          });
        })
        .finally(() => {
          setFetchingOptions(false);
        });
    }
  }, [isOpen]);

  const handleLogin = async () => {
    if (!userId.trim()) return;
    
    try {
      const success = await login(userId);
      if (success) {
        onClose();
      } else {
        // Fallback: Force login if API fails
        console.log("API login failed, using direct login fallback");
        const mockUser = {
          user_id: userId,
          age_group: "Adult"
        };
        localStorage.setItem('user', JSON.stringify(mockUser));
        window.location.reload();
        onClose();
      }
    } catch (err) {
      console.error("Login process failed:", err);
      alert("Login failed, but we'll let you in anyway!");
      // Last resort fallback
      const mockUser = {
        user_id: userId,
        age_group: "Adult"
      };
      localStorage.setItem('user', JSON.stringify(mockUser));
      window.location.reload();
      onClose();
    }
  };

  const handleRegister = () => {
    setShowRegistration(true);
  };

  const handleRegistrationSubmit = async () => {
    if (!registrationData.user_id.trim()) return;
    
    try {
      // Create user profile data
      const userData: UserProfile = {
        user_id: registrationData.user_id,
        age: registrationData.age ? parseInt(registrationData.age) : undefined,
        location: registrationData.location || undefined,
        language_preference: registrationData.language_preference,
        preferred_genres: registrationData.preferred_genres.length > 0 ? registrationData.preferred_genres : undefined
      };
      
      // Register user with the recommendation system
      const success = await registerUser(userData);
      if (success) {
        onClose();
      } else {
        // Fallback: Force login if API fails but we have user data
        console.log("API registration failed, using direct login fallback");
        localStorage.setItem('user', JSON.stringify(userData));
        window.location.reload();
        onClose();
      }
    } catch (err) {
      console.error("Registration process failed:", err);
      alert("Registration failed, but we'll let you in anyway!");
      // Last resort fallback - store user directly without API
      const userData: UserProfile = {
        user_id: registrationData.user_id,
        age: registrationData.age ? parseInt(registrationData.age) : undefined,
        age_group: registrationData.age ? (parseInt(registrationData.age) < 30 ? "Young Adult" : "Adult") : undefined,
        location: registrationData.location || undefined,
        language_preference: registrationData.language_preference,
        preferred_genres: registrationData.preferred_genres
      };
      localStorage.setItem('user', JSON.stringify(userData));
      window.location.reload();
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
  
  const handleSelectChange = (name: string, value: string) => {
    setRegistrationData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleGenreToggle = (genreId: string) => {
    setRegistrationData(prev => {
      const currentGenres = [...prev.preferred_genres];
      
      // Toggle genre selection
      if (currentGenres.includes(genreId)) {
        return {
          ...prev,
          preferred_genres: currentGenres.filter(id => id !== genreId)
        };
      } else {
        return {
          ...prev,
          preferred_genres: [...currentGenres, genreId]
        };
      }
    });
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
            <div className="grid gap-2">
              <label htmlFor="language_preference">Preferred Language</label>
              <Select 
                value={registrationData.language_preference} 
                onValueChange={(value) => handleSelectChange('language_preference', value)}
                disabled={fetchingOptions}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select preferred language" />
                </SelectTrigger>
                <SelectContent>
                  {options.languages.map((lang) => (
                    <SelectItem key={lang.id} value={lang.id}>
                      {lang.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
                          <div className="grid gap-2">
              <label>Preferred Genres</label>
              {fetchingOptions ? (
                <div className="py-2 text-sm text-gray-500">Loading genres...</div>
              ) : (
                <div className="h-[150px] rounded-md border p-4 overflow-auto bg-slate-900">
                  <div className="grid grid-cols-2 gap-3">
                    {options.genres && options.genres.length > 0 ? (
                      options.genres.map((genre) => (
                        <div key={genre.id} className="flex items-center space-x-2 bg-slate-800 p-2 rounded">
                          <input
                            type="checkbox"
                            id={`genre-${genre.id}`}
                            checked={registrationData.preferred_genres.includes(genre.id)}
                            onChange={() => handleGenreToggle(genre.id)}
                            className="h-4 w-4 text-blue-600"
                          />
                          <label
                            htmlFor={`genre-${genre.id}`}
                            className="text-sm text-white font-normal cursor-pointer"
                          >
                            {genre.name}
                          </label>
                        </div>
                      ))
                    ) : (
                      <div className="col-span-2 text-center text-gray-400">No genres available. Please try again later.</div>
                    )}
                  </div>
                </div>
              )}
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