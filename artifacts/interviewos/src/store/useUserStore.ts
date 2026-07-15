import { create } from 'zustand';

export interface UserProfile {
  name: string;
  email: string;
  avatar?: string;
  targetRole?: string;
  targetCompany?: string;
  subscriptionTier: 'free' | 'pro' | 'enterprise';
}

interface UserState {
  profile: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setProfile: (profile: Partial<UserProfile>) => void;
  login: (profile: UserProfile) => void;
  logout: () => void;
  setLoading: (isLoading: boolean) => void;
}

export const useUserStore = create<UserState>((set) => ({
  profile: {
    name: 'Alex Developer',
    email: 'alex@example.com',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&h=100&q=80',
    targetRole: 'Senior Frontend Engineer',
    targetCompany: 'Stripe',
    subscriptionTier: 'pro',
  },
  isAuthenticated: true,
  isLoading: false,
  setProfile: (updates) =>
    set((state) => ({
      profile: state.profile ? { ...state.profile, ...updates } : null,
    })),
  login: (profile) => set({ profile, isAuthenticated: true }),
  logout: () => set({ profile: null, isAuthenticated: false }),
  setLoading: (isLoading) => set({ isLoading }),
}));
