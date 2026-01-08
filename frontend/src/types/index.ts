/** Type definitions for PPT2Preview Frontend */

export enum LengthMode {
  SHORT = "SHORT",
  MEDIUM = "MEDIUM",
  LONG = "LONG",
}

export enum TaskStatus {
  PENDING = "pending",
  UPLOADING = "uploading",
  GENERATING_SCRIPT = "generating_script",
  SCRIPT_READY = "script_ready",
  GENERATING_VIDEO = "generating_video",
  COMPLETED = "completed",
  FAILED = "failed",
}

export interface UploadResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface GenerateScriptRequest {
  task_id: string;
  length_mode: LengthMode;
}

export interface ScriptResponse {
  task_id: string;
  script_content: string;
  transcription_data: Array<[string, string]>;
}

export interface UpdateScriptRequest {
  script_content: string;
}

export interface VideoParams {
  fps?: number;
  resolution_width?: number;
  resolution_height?: number;
  bitrate?: string;
  preset?: string;
}

export interface GenerateVideoRequest {
  task_id: string;
  video_params?: VideoParams;
  voice_name?: string;
}

export interface TaskStatusResponse {
  task_id: string;
  status: TaskStatus;
  progress: number;
  current_step?: string;
  message?: string;
  error?: string;
}

export interface ProgressUpdate {
  task_id: string;
  status: TaskStatus;
  progress: number;
  current_step?: string;
  message?: string;
  error?: string;
}

export interface HistoryProject {
  task_id: string;
  created_time: string | null;
  modified_time: string | null;
  has_script: boolean;
  has_video: boolean;
  status: string;
}

export interface HistoryResponse {
  projects: HistoryProject[];
}

