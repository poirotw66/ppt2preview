/** API client for PPT2Preview backend */

import axios from 'axios';
import type {
  UploadResponse,
  GenerateScriptRequest,
  ScriptResponse,
  UpdateScriptRequest,
  GenerateVideoRequest,
  TaskStatusResponse,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_PREFIX = `${API_BASE_URL}/api/v1`;

const api = axios.create({
  baseURL: API_PREFIX,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiClient = {
  /**
   * Upload abstract and PDF files
   */
  async uploadFiles(
    abstractFile: File,
    pdfFile?: File
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('abstract_file', abstractFile);
    if (pdfFile) {
      formData.append('pdf_file', pdfFile);
    }

    const response = await api.post<UploadResponse>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  /**
   * Generate script from uploaded files
   */
  async generateScript(
    request: GenerateScriptRequest
  ): Promise<ScriptResponse> {
    const response = await api.post<ScriptResponse>(
      '/generate-script',
      request
    );
    return response.data;
  },

  /**
   * Get script for a task
   */
  async getScript(taskId: string): Promise<ScriptResponse> {
    const response = await api.get<ScriptResponse>(`/script/${taskId}`);
    return response.data;
  },

  /**
   * Update script content
   */
  async updateScript(
    taskId: string,
    request: UpdateScriptRequest
  ): Promise<ScriptResponse> {
    const response = await api.put<ScriptResponse>(
      `/script/${taskId}`,
      request
    );
    return response.data;
  },

  /**
   * Optimize script using Gemini TRANSCRIPT_REWRITER_PROMPT
   */
  async optimizeScript(taskId: string): Promise<ScriptResponse> {
    const response = await api.post<ScriptResponse>(
      `/optimize-script/${taskId}`
    );
    return response.data;
  },

  /**
   * Generate video from script
   */
  async generateVideo(
    request: GenerateVideoRequest
  ): Promise<TaskStatusResponse> {
    const response = await api.post<TaskStatusResponse>(
      '/generate-video',
      request
    );
    return response.data;
  },

  /**
   * Get task status
   */
  async getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
    const response = await api.get<TaskStatusResponse>(`/status/${taskId}`);
    return response.data;
  },

  /**
   * Download video
   */
  async downloadVideo(taskId: string): Promise<Blob> {
    const response = await api.get(`/download/${taskId}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Get download URL for video
   */
  getDownloadUrl(taskId: string): string {
    return `${API_PREFIX}/download/${taskId}`;
  },

  /**
   * Get a file from task output directory
   */
  async getTaskFile(taskId: string, filename: string): Promise<string | Blob> {
    const response = await api.get(`/files/${taskId}/${filename}`, {
      responseType: filename.endsWith('.md') || filename.endsWith('.py') || filename.endsWith('.txt') 
        ? 'text' 
        : 'blob',
    });
    return response.data;
  },

  /**
   * List all files in task output directory
   */
  async listTaskFiles(taskId: string): Promise<{ task_id: string; files: string[]; count: number }> {
    const response = await api.get(`/files/${taskId}`);
    return response.data;
  },

  /**
   * Get file URL
   */
  getFileUrl(taskId: string, filename: string): string {
    return `${API_PREFIX}/files/${taskId}/${filename}`;
  },

  /**
   * Get history projects
   */
  async getHistory(): Promise<import('@/types').HistoryResponse> {
    const response = await api.get('/history');
    return response.data;
  },
};

export default apiClient;

