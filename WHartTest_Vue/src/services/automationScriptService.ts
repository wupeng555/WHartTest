import { request } from '@/utils/request';

export interface AutomationScript {
  id: string;
  name: string;
  description?: string;
  script_type: string;
  script_type_display: string;
  status: string;
  status_display: string;
  test_cases_content: string;
  yaml_content?: string;
  target_url?: string;
  viewport_width: number;
  viewport_height: number;
  ai_model: string;
  api_key?: string;
  api_endpoint?: string;
  execution_timeout: number;
  retry_count: number;
  creator: string;
  creator_name: string;
  project: string;
  project_name: string;
  created_at: string;
  updated_at: string;
  generated_at?: string;
}

export interface ScriptExecution {
  id: string;
  script: string;
  script_name: string;
  executor: string;
  executor_name: string;
  status: string;
  status_display: string;
  execution_id: string;
  exit_code?: number;
  stdout?: string;
  stderr?: string;
  report_path?: string;
  report_url?: string;
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  execution_time?: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface ExecutionLog {
  id: string;
  execution: string;
  level: string;
  level_display: string;
  message: string;
  timestamp: string;
  step_name?: string;
  screenshot_path?: string;
}

export interface ScriptTemplate {
  id: string;
  name: string;
  description?: string;
  template_type: string;
  template_type_display: string;
  yaml_template: string;
  test_case_template?: string;
  is_public: boolean;
  is_default: boolean;
  creator: string;
  creator_name: string;
  created_at: string;
  updated_at: string;
}

export interface CreateScriptData {
  name: string;
  description?: string;
  script_type: string;
  test_cases_content: string;
  target_url?: string;
  viewport_width?: number;
  viewport_height?: number;
  ai_model?: string;
  api_key?: string;
  api_endpoint?: string;
  execution_timeout?: number;
  retry_count?: number;
  project: string;
}

class AutomationScriptService {
  private baseURL = '/api/automation-scripts';

  // 脚本管理
  async getScripts(params?: { 
    page?: number; 
    page_size?: number; 
    script_type?: string;
    status?: string;
    project?: string;
    search?: string;
  }) {
    return request.get(`${this.baseURL}/scripts/`, { params });
  }

  async getScript(id: string) {
    return request.get(`${this.baseURL}/scripts/${id}/`);
  }

  async createScript(data: CreateScriptData) {
    return request.post(`${this.baseURL}/scripts/`, data);
  }

  async updateScript(id: string, data: Partial<CreateScriptData>) {
    return request.patch(`${this.baseURL}/scripts/${id}/`, data);
  }

  async deleteScript(id: string) {
    return request.delete(`${this.baseURL}/scripts/${id}/`);
  }

  // 脚本生成
  async generateYaml(id: string) {
    return request.post(`${this.baseURL}/scripts/${id}/generate_yaml/`);
  }

  async downloadYaml(id: string) {
    return request.get(`${this.baseURL}/scripts/${id}/download_yaml/`, {
      responseType: 'blob',
    });
  }

  // 脚本执行
  async executeScript(id: string, data?: {
    execution_mode?: string;
    timeout?: number;
    retry_count?: number;
  }) {
    return request.post(`${this.baseURL}/scripts/${id}/execute/`, data || {});
  }

  async getScriptExecutions(scriptId: string, params?: { page?: number; page_size?: number }) {
    return request.get(`${this.baseURL}/scripts/${scriptId}/executions/`, { params });
  }

  // 执行记录管理
  async getExecutions(params?: { 
    page?: number; 
    page_size?: number; 
    script?: string;
    status?: string;
    executor?: string;
  }) {
    return request.get(`${this.baseURL}/executions/`, { params });
  }

  async getExecution(id: string) {
    return request.get(`${this.baseURL}/executions/${id}/`);
  }

  async cancelExecution(id: string) {
    return request.post(`${this.baseURL}/executions/${id}/cancel/`);
  }

  // 执行日志
  async getExecutionLogs(executionId: string, params?: { page?: number; page_size?: number }) {
    return request.get(`${this.baseURL}/executions/${executionId}/logs/`, { params });
  }

  // 测试报告
  async getExecutionReport(executionId: string, filePath?: string) {
    const params = filePath ? { path: filePath } : {};
    return request.get(`${this.baseURL}/executions/${executionId}/report/`, { 
      params,
      responseType: 'blob'
    });
  }

  async getExecutionReportUrl(executionId: string, filePath: string = 'index.html') {
    return `${this.baseURL}/executions/${executionId}/report/?path=${filePath}`;
  }

  // 模板管理
  async getTemplates(params?: { 
    page?: number; 
    page_size?: number; 
    template_type?: string;
    is_public?: boolean;
    search?: string;
  }) {
    return request.get(`${this.baseURL}/templates/`, { params });
  }

  async getTemplate(id: string) {
    return request.get(`${this.baseURL}/templates/${id}/`);
  }

  async createTemplate(data: {
    name: string;
    description?: string;
    template_type: string;
    yaml_template: string;
    test_case_template?: string;
    is_public?: boolean;
  }) {
    return request.post(`${this.baseURL}/templates/`, data);
  }

  async updateTemplate(id: string, data: Partial<{
    name: string;
    description?: string;
    template_type: string;
    yaml_template: string;
    test_case_template?: string;
    is_public?: boolean;
  }>) {
    return request.patch(`${this.baseURL}/templates/${id}/`, data);
  }

  async deleteTemplate(id: string) {
    return request.delete(`${this.baseURL}/templates/${id}/`);
  }

  async getDefaultTemplates() {
    return request.get(`${this.baseURL}/templates/default_templates/`);
  }

  // 实时状态轮询
  async pollExecutionStatus(executionId: string, onUpdate: (execution: ScriptExecution) => void, interval: number = 3000) {
    const poll = async () => {
      try {
        const response = await this.getExecution(executionId);
        const execution = response.data;
        onUpdate(execution);
        
        // 如果执行完成，停止轮询
        if (['completed', 'failed', 'cancelled'].includes(execution.status)) {
          return;
        }
        
        // 继续轮询
        setTimeout(poll, interval);
      } catch (error) {
        console.error('轮询执行状态失败:', error);
        // 发生错误时也停止轮询
      }
    };
    
    poll();
  }

  // 停止执行
  async stopExecution(executionId: string) {
    return request.post(`${this.baseURL}/executions/${executionId}/stop/`);
  }

  // 获取执行截图
  async getExecutionScreenshots(executionId: string) {
    return request.get(`${this.baseURL}/executions/${executionId}/screenshots/`);
  }

  // 下载执行报告
  async downloadExecutionReport(executionId: string) {
    return request.get(`${this.baseURL}/executions/${executionId}/report/`, {
      responseType: 'blob'
    });
  }

  // 获取执行统计
  async getExecutionStats(params?: { project_id?: string; date_range?: string[] }) {
    return request.get(`${this.baseURL}/executions/stats/`, { params });
  }

  // 获取执行报告列表
  async getExecutionReports(params?: { 
    page?: number; 
    page_size?: number;
    script_name?: string;
    status?: string;
    project_id?: string;
    date_start?: string;
    date_end?: string;
  }) {
    return request.get(`${this.baseURL}/executions/`, { params });
  }

  // 导出执行报告
  async exportExecutionReports(params?: any) {
    return request.get(`${this.baseURL}/executions/export/`, {
      params,
      responseType: 'blob'
    });
  }

  // 重新执行脚本
  async rerunScript(executionId: string) {
    return request.post(`${this.baseURL}/executions/${executionId}/rerun/`);
  }

  // 分享报告
  async shareReport(executionId: string) {
    return request.post(`${this.baseURL}/executions/${executionId}/share/`);
  }

  // 对比报告
  async compareReports(data: { base_report_id: string; compare_report_id: string }) {
    return request.post(`${this.baseURL}/executions/compare/`, data);
  }

  // 获取项目列表
  async getProjects() {
    return request.get('/api/projects/');
  }
}

export const automationScriptService = new AutomationScriptService();