import { create } from 'zustand';

export interface UserProfile {
  id: string;
  full_name: string;
  email: string;
  avatar_url?: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;

  // UI Backwards Compatibility fields
  name: string;
  avatar: string;
  targetRole?: string;
  targetCompany?: string;
  subscriptionTier: 'free' | 'pro' | 'enterprise';
}

interface UserState {
  profile: UserProfile | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setProfile: (profile: Partial<UserProfile>) => void;
  login: (profile: any, token: string, refreshToken: string) => void;
  logout: () => void;
  setLoading: (isLoading: boolean) => void;
  initialize: () => Promise<void>;
}

const API_BASE_URL = 'http://localhost:8000/api/v1';

const mapProfile = (raw: any): UserProfile => {
  return {
    ...raw,
    name: raw.full_name || 'Candidate',
    avatar:
      raw.avatar_url ||
      'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&h=100&q=80',
    subscriptionTier: raw.subscriptionTier || 'pro',
    targetRole: raw.targetRole || 'Senior Engineer',
    targetCompany: raw.targetCompany || 'Stripe',
  };
};

export const useUserStore = create<UserState>((set, get) => ({
  profile: localStorage.getItem('profile')
    ? JSON.parse(localStorage.getItem('profile')!)
    : null,
  token: localStorage.getItem('token'),
  refreshToken: localStorage.getItem('refreshToken'),
  isAuthenticated: !!localStorage.getItem('token'),
  isLoading: false,
  setProfile: (updates) =>
    set((state) => {
      const newProfile = state.profile
        ? { ...state.profile, ...updates }
        : null;
      if (newProfile) {
        localStorage.setItem('profile', JSON.stringify(newProfile));
      }
      return { profile: newProfile };
    }),
  login: (profile, token, refreshToken) => {
    const mapped = mapProfile(profile);
    localStorage.setItem('profile', JSON.stringify(mapped));
    localStorage.setItem('token', token);
    localStorage.setItem('refreshToken', refreshToken);
    set({ profile: mapped, token, refreshToken, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem('profile');
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    set({
      profile: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
    });
  },
  setLoading: (isLoading) => set({ isLoading }),
  initialize: async () => {
    const { token } = get();
    if (!token) {
      set({ isAuthenticated: false, profile: null });
      return;
    }
    set({ isLoading: true });
    try {
      const res = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (res.ok) {
        const rawProfile = await res.json();
        const profile = mapProfile(rawProfile);
        localStorage.setItem('profile', JSON.stringify(profile));
        set({ profile, isAuthenticated: true });
      } else {
        // Token might have expired, try refresh
        const { refreshToken } = get();
        if (refreshToken) {
          const refreshRes = await fetch(`${API_BASE_URL}/auth/refresh`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });
          if (refreshRes.ok) {
            const data = await refreshRes.json();
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('refreshToken', data.refresh_token);
            set({ token: data.access_token, refreshToken: data.refresh_token });
            // Retry fetch profile
            const retryRes = await fetch(`${API_BASE_URL}/auth/me`, {
              headers: {
                Authorization: `Bearer ${data.access_token}`,
              },
            });
            if (retryRes.ok) {
              const retryRaw = await retryRes.json();
              const retryProfile = mapProfile(retryRaw);
              localStorage.setItem('profile', JSON.stringify(retryProfile));
              set({ profile: retryProfile, isAuthenticated: true });
              return;
            }
          }
        }
        // If refresh fails
        localStorage.removeItem('profile');
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        set({
          profile: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      }
    } catch (err) {
      console.error('Failed to initialize user session:', err);
    } finally {
      set({ isLoading: false });
    }
  },
}));
export type { UserState };
