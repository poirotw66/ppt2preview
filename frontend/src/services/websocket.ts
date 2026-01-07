/** WebSocket client for real-time progress updates */

import type { ProgressUpdate } from '@/types';

export type WebSocketMessageHandler = (update: ProgressUpdate) => void;
export type WebSocketErrorHandler = (error: Event) => void;
export type WebSocketCloseHandler = () => void;

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';
const WS_PREFIX = `${WS_BASE_URL}/api/v1/ws`;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private taskId: string | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(
    private onMessage: WebSocketMessageHandler,
    private onError?: WebSocketErrorHandler,
    private onClose?: WebSocketCloseHandler
  ) {}

  /**
   * Connect to WebSocket for a specific task
   */
  connect(taskId: string): void {
    if (this.ws?.readyState === WebSocket.OPEN && this.taskId === taskId) {
      // Already connected to this task
      return;
    }

    this.disconnect();
    this.taskId = taskId;

    try {
      const wsUrl = `${WS_PREFIX}/${taskId}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log(`WebSocket connected for task ${taskId}`);
        this.reconnectAttempts = 0;
        // Send a ping message to keep connection alive
        this.send(JSON.stringify({ type: 'ping' }));
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // Handle pong responses
          if (data.type === 'pong') {
            return;
          }
          // Handle progress updates
          const update = data as ProgressUpdate;
          this.onMessage(update);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (this.onError) {
          this.onError(error);
        }
      };

      this.ws.onclose = () => {
        console.log(`WebSocket closed for task ${taskId}`);
        if (this.onClose) {
          this.onClose();
        }

        // Attempt to reconnect if not manually closed
        if (this.taskId && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          setTimeout(() => {
            if (this.taskId) {
              console.log(`Reconnecting WebSocket (attempt ${this.reconnectAttempts})...`);
              this.connect(this.taskId);
            }
          }, this.reconnectDelay * this.reconnectAttempts);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.taskId = null;
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Send a message through WebSocket
   */
  send(message: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(message);
    } else {
      console.warn('WebSocket is not connected');
    }
  }
}

