import { create } from 'zustand';
import type { Toast, ToastType } from '@/components/Toast';

interface ToastStore {
  toasts: Toast[];
  showToast: (message: string, type?: ToastType, duration?: number) => void;
  removeToast: (id: string) => void;
  success: (message: string, duration?: number) => void;
  error: (message: string, duration?: number) => void;
  info: (message: string, duration?: number) => void;
  warning: (message: string, duration?: number) => void;
}

let toastIdCounter = 0;

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  
  showToast: (message: string, type: ToastType = 'info', duration?: number) => {
    const id = `toast-${Date.now()}-${toastIdCounter++}`;
    const newToast: Toast = { id, message, type, duration };
    set((state) => ({ toasts: [...state.toasts, newToast] }));
  },
  
  removeToast: (id: string) => {
    set((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) }));
  },
  
  success: (message: string, duration?: number) => {
    useToastStore.getState().showToast(message, 'success', duration);
  },
  
  error: (message: string, duration?: number) => {
    useToastStore.getState().showToast(message, 'error', duration);
  },
  
  info: (message: string, duration?: number) => {
    useToastStore.getState().showToast(message, 'info', duration);
  },
  
  warning: (message: string, duration?: number) => {
    useToastStore.getState().showToast(message, 'warning', duration);
  },
}));
