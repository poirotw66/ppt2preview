/** Zustand store for app settings (voice selection, preferences) */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SettingsState {
  // Voice settings
  selectedVoice: string;
  
  // Actions
  setVoice: (voice: string) => void;
  reset: () => void;
}

const initialState = {
  selectedVoice: 'Aoede', // Default female voice
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      ...initialState,

      setVoice: (voice) => set({ selectedVoice: voice }),

      reset: () => set(initialState),
    }),
    {
      name: 'ppt2preview-settings', // localStorage key
    }
  )
);
