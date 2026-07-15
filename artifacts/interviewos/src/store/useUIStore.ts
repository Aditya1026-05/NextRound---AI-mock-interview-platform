import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  workspaceLayout: {
    leftPanelWidth: number; // Percentage (e.g., 50)
    editorHeight: number; // Percentage (e.g., 70)
  };
  breadcrumbs: string[];
  
  // Actions
  toggleSidebar: () => void;
  setSidebar: (open: boolean) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  updateWorkspaceLayout: (layout: Partial<UIState['workspaceLayout']>) => void;
  setBreadcrumbs: (crumbs: string[]) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  theme: 'light',
  workspaceLayout: {
    leftPanelWidth: 45,
    editorHeight: 65,
  },
  breadcrumbs: ['Dashboard'],

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebar: (sidebarOpen) => set({ sidebarOpen }),
  setTheme: (theme) => set({ theme }),
  updateWorkspaceLayout: (layout) =>
    set((state) => ({
      workspaceLayout: { ...state.workspaceLayout, ...layout },
    })),
  setBreadcrumbs: (breadcrumbs) => set({ breadcrumbs }),
}));
