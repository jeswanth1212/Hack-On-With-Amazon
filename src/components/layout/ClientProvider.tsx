'use client';

import { ReactNode } from "react";
import { AuthProvider } from "@/lib/hooks";

interface ClientProviderProps {
  children: ReactNode;
}

export default function ClientProvider({ children }: ClientProviderProps) {
  return <AuthProvider>{children}</AuthProvider>;
} 