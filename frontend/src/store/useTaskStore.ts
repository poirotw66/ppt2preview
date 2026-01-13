/** Zustand store for task management */

import { create } from 'zustand';
import type {
  TaskStatus,
  TaskStatusResponse,
  ScriptResponse,
  LengthMode,
  VideoParams,
} from '@/types';

interface TaskState {
  // Current task
  taskId: string | null;
  status: TaskStatus | null;
  progress: number;
  currentStep: string | null;
  message: string | null;
  error: string | null;

  // Script data
  scriptContent: string | null;
  transcriptionData: Array<[string, string]> | null;

  // Video parameters used for generation
  videoParams: VideoParams | null;

  // Actions
  setTaskId: (taskId: string | null) => void;
  updateStatus: (status: TaskStatusResponse) => void;
  setScript: (script: ScriptResponse) => void;
  updateScriptContent: (content: string) => void;
  setVideoParams: (params: VideoParams) => void;
  reset: () => void;
}

const initialState = {
  taskId: null,
  status: null,
  progress: 0,
  currentStep: null,
  message: null,
  error: null,
  scriptContent: null,
  transcriptionData: null,
  videoParams: null,
};

export const useTaskStore = create<TaskState>((set) => ({
  ...initialState,

  setTaskId: (taskId) => set({ taskId }),

  updateStatus: (statusData) =>
    set({
      status: statusData.status,
      progress: statusData.progress,
      currentStep: statusData.current_step || null,
      message: statusData.message || null,
      error: statusData.error || null,
    }),

  setScript: (script) =>
    set({
      scriptContent: script.script_content,
      transcriptionData: script.transcription_data,
    }),

  updateScriptContent: (content) => set({ scriptContent: content }),

  setVideoParams: (params) => set({ videoParams: params }),

  reset: () => set(initialState),
}));

