import { request } from '@/utils/request';

export interface TestCaseReview {
  id: string;
  title: string;
  description?: string;
  original_file?: File | string;
  file_type?: string;
  file_content?: string;
  review_type: string;
  custom_prompt?: string;
  ai_model: string;
  api_base_url?: string;
  api_key?: string;
  status: string;
  review_result?: string;
  error_message?: string;
  total_test_cases: number;
  review_score?: number;
  processing_time?: number;
  creator?: string;
  creator_name?: string;
  project: string;
  project_name?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  comments?: ReviewComment[];
  sessions?: ReviewSession[];
  file_size?: number;
  comment_count?: number;
}

export interface ReviewComment {
  id: string;
  comment_type: string;
  severity: string;
  title: string;
  content: string;
  line_number?: number;
  test_case_id?: string;
  is_resolved: boolean;
  resolution?: string;
  created_at: string;
  resolved_at?: string;
}

export interface ReviewTemplate {
  id: string;
  name: string;
  description?: string;
  template_type: string;
  prompt_template: string;
  is_default: boolean;
  is_active: boolean;
  creator?: string;
  created_at: string;
  updated_at: string;
}

export interface ReviewSession {
  id: string;
  session_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  messages?: ReviewMessage[];
  message_count?: number;
}

export interface ReviewMessage {
  id: string;
  message_type: string;
  content: string;
  model_used?: string;
  tokens_used?: number;
  response_time?: number;
  created_at: string;
}

export interface CreateReviewData {
  title: string;
  description?: string;
  original_file?: File;
  file_type?: string;
  file_content?: string;
  review_type: string;
  custom_prompt?: string;
  ai_model: string;
  api_base_url?: string;
  api_key?: string;
  project: string;
}

export interface ReviewListParams {
  page?: number;
  page_size?: number;
  project?: string;
  status?: string;
  review_type?: string;
  search?: string;
  ordering?: string;
}

export interface ChatMessage {
  session_id: string;
  message: string;
}

class TestCaseReviewService {
  private baseURL = '/api/testcase-review';

  // 获取评审列表
  async getReviews(params?: ReviewListParams) {
    return request.get(`${this.baseURL}/reviews/`, { params });
  }

  // 获取评审详情
  async getReview(id: string) {
    return request.get(`${this.baseURL}/reviews/${id}/`);
  }

  // 创建评审
  async createReview(data: CreateReviewData) {
    const formData = new FormData();
    
    // 添加基本字段
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (key === 'original_file' && value instanceof File) {
          formData.append(key, value);
        } else if (typeof value === 'string' || typeof value === 'number') {
          formData.append(key, value.toString());
        }
      }
    });

    return request.post(`${this.baseURL}/reviews/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  // 更新评审
  async updateReview(id: string, data: Partial<CreateReviewData>) {
    const formData = new FormData();
    
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (key === 'original_file' && value instanceof File) {
          formData.append(key, value);
        } else if (typeof value === 'string' || typeof value === 'number') {
          formData.append(key, value.toString());
        }
      }
    });

    return request.patch(`${this.baseURL}/reviews/${id}/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  // 删除评审
  async deleteReview(id: string) {
    return request.delete(`${this.baseURL}/reviews/${id}/`);
  }

  // 开始评审
  async startReview(id: string) {
    return request.post(`${this.baseURL}/reviews/${id}/start_review/`);
  }

  // 下载原始文件
  async downloadFile(id: string) {
    return request.get(`${this.baseURL}/reviews/${id}/download_file/`, {
      responseType: 'blob',
    });
  }

  // 创建对话会话
  async createSession(reviewId: string, sessionName?: string) {
    return request.post(`${this.baseURL}/reviews/${reviewId}/create_session/`, {
      session_name: sessionName,
    });
  }

  // AI对话
  async chat(reviewId: string, data: ChatMessage) {
    return request.post(`${this.baseURL}/reviews/${reviewId}/chat/`, data);
  }

  // 发送聊天消息
  async sendChatMessage(reviewId: string, sessionId: string, message: string, aiModel: string = 'deepseek') {
    return request.post(`${this.baseURL}/reviews/${reviewId}/send_message/`, {
      session_id: sessionId,
      message: message,
      ai_model: aiModel,
    });
  }

  // 获取聊天消息列表
  async getChatMessages(sessionId: string, params?: { page?: number; page_size?: number }) {
    return request.get(`${this.baseURL}/sessions/${sessionId}/messages/`, { params });
  }

  // 获取会话列表
  async getSessions(params?: { review?: string; page?: number; page_size?: number }) {
    return request.get(`${this.baseURL}/sessions/`, { params });
  }

  // 获取评审意见列表
  async getComments(params?: { review?: string; page?: number; page_size?: number }) {
    return request.get(`${this.baseURL}/comments/`, { params });
  }

  // 创建评审意见
  async createComment(data: Partial<ReviewComment>) {
    return request.post(`${this.baseURL}/comments/`, data);
  }

  // 解决评审意见
  async resolveComment(id: string, resolution: string) {
    return request.post(`${this.baseURL}/comments/${id}/resolve/`, {
      resolution,
    });
  }

  // 获取评审模板列表
  async getTemplates(params?: { template_type?: string; is_active?: boolean }) {
    return request.get(`${this.baseURL}/templates/`, { params });
  }

  // 获取默认模板
  async getDefaultTemplates() {
    return request.get(`${this.baseURL}/templates/default_templates/`);
  }

  // 创建评审模板
  async createTemplate(data: Partial<ReviewTemplate>) {
    return request.post(`${this.baseURL}/templates/`, data);
  }

  // 获取会话列表
  async getSessions(params?: { review?: string; is_active?: boolean }) {
    return request.get(`${this.baseURL}/sessions/`, { params });
  }

  // 获取会话消息
  async getMessages(params?: { session?: string }) {
    return request.get(`${this.baseURL}/messages/`, { params });
  }
}

export const testcaseReviewService = new TestCaseReviewService();