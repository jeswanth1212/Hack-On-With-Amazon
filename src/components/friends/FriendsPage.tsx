'use client';

import { useState, useEffect } from 'react';
import MainLayout from '../layout/MainLayout';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ChevronLeft, QrCode } from "lucide-react";
import ActivityView from './ActivityView';
import RequestsView from './RequestsView';
import FriendsListView from './FriendsListView';
import QrCodeOverlay from './QrCodeOverlay';
import { useFriendsPageNavigation } from './useFriendsPageNavigation';

const TAB_VALUES = ['activity', 'requests', 'friends'];

export default function FriendsPage() {
  const [showQrCode, setShowQrCode] = useState(false);
  const { activeTabIndex, setActiveTabIndex } = useFriendsPageNavigation();
  
  // Update tabs based on keyboard navigation
  useEffect(() => {
    const tabValue = TAB_VALUES[activeTabIndex];
    const tabElement = document.querySelector(`[data-state="inactive"][value="${tabValue}"]`);
    if (tabElement) {
      (tabElement as HTMLElement).click();
    }
  }, [activeTabIndex]);

  // Handle tab change from UI
  const handleTabChange = (value: string) => {
    const index = TAB_VALUES.indexOf(value);
    if (index !== -1) {
      setActiveTabIndex(index);
    }
  };
  
  return (
    <MainLayout>
      <div className="max-w-5xl mx-auto px-6 pt-24 pb-16">
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center">
            <Button 
              variant="ghost" 
              size="icon" 
              className="mr-4 text-white"
              aria-label="Back"
            >
              <ChevronLeft size={28} />
            </Button>
            <h1 className="text-4xl font-bold text-white">My Friends</h1>
          </div>
          <Button 
            variant="outline" 
            size="icon"
            className="text-white border-white"
            onClick={() => setShowQrCode(true)}
            aria-label="Show QR Code"
          >
            <QrCode size={20} />
          </Button>
        </div>
        
        <Tabs 
          defaultValue="activity" 
          className="w-full"
          onValueChange={handleTabChange}
        >
          <TabsList className="w-full max-w-md mb-6 bg-background border border-gray-800">
            <TabsTrigger 
              value="activity" 
              className="flex-1 py-3 data-[state=active]:bg-secondary"
            >
              Activity
            </TabsTrigger>
            <TabsTrigger 
              value="requests" 
              className="flex-1 py-3 data-[state=active]:bg-secondary"
            >
              Requests
            </TabsTrigger>
            <TabsTrigger 
              value="friends" 
              className="flex-1 py-3 data-[state=active]:bg-secondary"
            >
              Friends
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="activity" className="mt-0">
            <ActivityView />
          </TabsContent>
          
          <TabsContent value="requests" className="mt-0">
            <RequestsView />
          </TabsContent>
          
          <TabsContent value="friends" className="mt-0">
            <FriendsListView />
          </TabsContent>
        </Tabs>
      </div>
      
      {showQrCode && <QrCodeOverlay onClose={() => setShowQrCode(false)} />}
    </MainLayout>
  );
} 