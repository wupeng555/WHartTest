<template>
  <a-modal
    v-model:visible="visible"
    :title="script?.name || '脚本详情'"
    width="1200px"
    :footer="false"
    :body-style="{ padding: 0 }"
  >
    <div v-if="script" class="script-detail">
      <!-- 头部信息 -->
      <div class="detail-header">
        <div class="header-info">
          <div class="status-badge">
            <a-tag :color="getStatusColor(script.status)" size="large">
              {{ script.status_display }}
            </a-tag>
            <a-tag :color="getScriptTypeColor(script.script_type)">
              {{ script.script_type_display }}
            </a-tag>
          </div>
          <div class="script-meta">
            <div class="meta-item">
              <span class="meta-label">项目:</span>
              <span class="meta-value">{{ script.project_name }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">创建者:</span>
              <span class="meta-value">{{ script.creator_name }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">创建时间:</span>
              <span class="meta-value">{{ formatDate(script.created_at) }}</span>
            </div>
            <div v-if="script.generated_at" class="meta-item">
              <span class="meta-label">生成时间:</span>
              <span class="meta-value">{{ formatDate(script.generated_at) }}</span>
            </div>
          </div>
        </div>
        <div class="header-actions">
          <a-button
            v-if="script.status === 'draft'"
            type="primary"
            @click="generateYaml"
            :loading="generating"
          >
            生成脚本
          </a-button>
          <a-button
            v-if="['generated', 'ready', 'completed'].includes(script.status)"
            type="primary"
            @click="executeScript"
            :loading="executing"
          >
            执行脚本
          </a-button>
          <a-button
            v-if="script.yaml_content"
            @click="downloadYaml"
          >
            <template #icon><icon-download /></template>
            下载YAML
          </a-button>
          <a-button @click="refreshDetail">
            <template #icon><icon-refresh /></template>
            刷新
          </a-button>
        </div>
      </div>

      <!-- 标签页内容 -->
      <div class="detail-content">
        <a-tabs v-model:active-key="activeTab" type="card">
          <!-- 基本信息 -->
          <a-tab-pane key="info" title="基本信息">
            <div class="info-panel">
              <div class="info-section">
                <h3>脚本信息</h3>
                <div class="info-grid">
                  <div class="info-item">
                    <label>脚本名称:</label>
                    <span>{{ script.name }}</span>
                  </div>
                  <div class="info-item">
                    <label>脚本描述:</label>
                    <span>{{ script.description || '无' }}</span>
                  </div>
                  <div class="info-item">
                    <label>目标URL:</label>
                    <span>{{ script.target_url || '无' }}</span>
                  </div>
                  <div class="info-item">
                    <label>视口尺寸:</label>
                    <span>{{ script.viewport_width }} × {{ script.viewport_height }}</span>
                  </div>
                </div>
              </div>

              <div class="info-section">
                <h3>AI配置</h3>
                <div class="info-grid">
                  <div class="info-item">
                    <label>AI模型:</label>
                    <span>{{ script.ai_model }}</span>
                  </div>
                  <div class="info-item">
                    <label>API端点:</label>
                    <span>{{ script.api_endpoint || '未配置' }}</span>
                  </div>
                </div>
              </div>

              <div class="info-section">
                <h3>执行配置</h3>
                <div class="info-grid">
                  <div class="info-item">
                    <label>执行超时:</label>
                    <span>{{ script.execution_timeout }}秒</span>
                  </div>
                  <div class="info-item">
                    <label>重试次数:</label>
                    <span>{{ script.retry_count }}次</span>
                  </div>
                </div>
              </div>
            </div>
          </a-tab-pane>

          <!-- 测试用例 -->
          <a-tab-pane key="testcases" title="测试用例">
            <div class="content-panel">
              <div class="content-header">
                <h3>测试用例内容</h3>
                <a-button size="small" @click="copyTestCases">
                  <template #icon><icon-copy /></template>
                  复制
                </a-button>
              </div>
              <div class="content-text">
                <pre>{{ script.test_cases_content }}</pre>
              </div>
            </div>
          </a-tab-pane>

          <!-- YAML脚本 -->
          <a-tab-pane key="yaml" title="YAML脚本">
            <div class="content-panel">
              <div v-if="script.yaml_content" class="yaml-content">
                <div class="content-header">
                  <h3>生成的YAML脚本</h3>
                  <div class="header-actions">
                    <a-button size="small" @click="copyYaml">
                      <template #icon><icon-copy /></template>
                      复制
                    </a-button>
                    <a-button size="small" @click="downloadYaml">
                      <template #icon><icon-download /></template>
                      下载
                    </a-button>
                  </div>
                </div>
                <div class="yaml-editor">
                  <pre><code class="language-yaml">{{ script.yaml_content }}</code></pre>
                </div>
              </div>

              <div v-else class="empty-content">
                <icon-file-text class="empty-icon" />
                <p>YAML脚本未生成</p>
                <a-button
                  v-if="script.status === 'draft'"
                  type="primary"
                  @click="generateYaml"
                  :loading="generating"
                >
                  立即生成
                </a-button>
              </div>
            </div>
          </a-tab-pane>

          <!-- 执行记录 -->
          <a-tab-pane key="executions" title="执行记录">
            <div class="executions-panel">
              <div class="executions-header">
                <h3>执行历史</h3>
                <a-button
                  type="primary"
                  size="small"
                  @click="loadExecutions"
                  :loading="loadingExecutions"
                >
                  <template #icon><icon-refresh /></template>
                  刷新
                </a-button>
              </div>

              <div v-if="executions.length > 0" class="executions-list">
                <div
                  v-for="execution in executions"
                  :key="execution.id"
                  class="execution-item"
                  @click="viewExecution(execution)"
                >
                  <div class="execution-header">
                    <div class="execution-info">
                      <span class="execution-id">{{ execution.execution_id }}</span>
                      <a-tag :color="getExecutionStatusColor(execution.status)">
                        {{ execution.status_display }}
                      </a-tag>
                    </div>
                    <div class="execution-time">
                      {{ formatDate(execution.created_at) }}
                    </div>
                  </div>
                  
                  <div v-if="execution.total_tests > 0" class="execution-stats">
                    <div class="stat-item">
                      <span class="stat-label">总数:</span>
                      <span class="stat-value">{{ execution.total_tests }}</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">通过:</span>
                      <span class="stat-value success">{{ execution.passed_tests }}</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">失败:</span>
                      <span class="stat-value error">{{ execution.failed_tests }}</span>
                    </div>
                    <div v-if="execution.execution_time" class="stat-item">
                      <span class="stat-label">耗时:</span>
                      <span class="stat-value">{{ execution.execution_time.toFixed(2) }}s</span>
                    </div>
                  </div>

                  <div class="execution-actions">
                    <a-button
                      v-if="execution.report_url"
                      size="small"
                      @click.stop="viewReport(execution)"
                    >
                      查看报告
                    </a-button>
                    <a-button
                      size="small"
                      @click.stop="viewLogs(execution)"
                    >
                      查看日志
                    </a-button>
                    <a-button
                      v-if="execution.status === 'running'"
                      size="small"
                      status="danger"
                      @click.stop="cancelExecution(execution)"
                    >
                      取消执行
                    </a-button>
                  </div>
                </div>
              </div>

              <div v-else class="empty-executions">
                <icon-history class="empty-icon" />
                <p>暂无执行记录</p>
              </div>
            </div>
          </a-tab-pane>
        </a-tabs>
      </div>
    </div>

    <!-- 执行详情模态框 -->
    <ExecutionDetailModal
      v-model:visible="showExecutionDetail"
      :execution="selectedExecution"
    />

    <!-- 日志查看模态框 -->
    <ExecutionLogsModal
      v-model:visible="showLogsModal"
      :execution="selectedExecution"
    />
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue';
import { Message } from '@arco-design/web-vue';
import {
  IconDownload,
  IconRefresh,
  IconCopy,
  IconFileText,
  IconHistory
} from '@arco-design/web-vue/es/icon';
import { automationScriptService, type AutomationScript, type ScriptExecution } from '@/services/automationScriptService';
import ExecutionDetailModal from './ExecutionDetailModal.vue';
import ExecutionLogsModal from './ExecutionLogsModal.vue';

interface Props {
  visible: boolean;
  script?: AutomationScript | null;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  'update:visible': [value: boolean];
  refresh: [];
}>();

// 响应式数据
const activeTab = ref('info');
const generating = ref(false);
const executing = ref(false);
const loadingExecutions = ref(false);
const executions = ref<ScriptExecution[]>([]);
const selectedExecution = ref<ScriptExecution | null>(null);
const showExecutionDetail = ref(false);
const showLogsModal = ref(false);

// 方法
const generateYaml = async () => {
  if (!props.script) return;

  generating.value = true;
  try {
    await automationScriptService.generateYaml(props.script.id);
    Message.success('YAML脚本生成成功');
    emit('refresh');
  } catch (error: any) {
    console.error('生成YAML脚本失败:', error);
    Message.error(error.response?.data?.error || '生成YAML脚本失败');
  } finally {
    generating.value = false;
  }
};

const executeScript = async () => {
  if (!props.script) return;

  executing.value = true;
  try {
    await automationScriptService.executeScript(props.script.id);
    Message.success('脚本执行已开始');
    emit('refresh');
    loadExecutions();
  } catch (error: any) {
    console.error('执行脚本失败:', error);
    Message.error(error.response?.data?.error || '执行脚本失败');
  } finally {
    executing.value = false;
  }
};

const downloadYaml = async () => {
  if (!props.script?.yaml_content) return;

  try {
    const response = await automationScriptService.downloadYaml(props.script.id);
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.download = `${props.script.name}.yaml`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    Message.success('YAML脚本下载成功');
  } catch (error: any) {
    console.error('下载YAML脚本失败:', error);
    Message.error('下载YAML脚本失败');
  }
};

const copyTestCases = async () => {
  if (!props.script?.test_cases_content) return;

  try {
    await navigator.clipboard.writeText(props.script.test_cases_content);
    Message.success('测试用例内容已复制到剪贴板');
  } catch (error) {
    console.error('复制失败:', error);
    Message.error('复制失败');
  }
};

const copyYaml = async () => {
  if (!props.script?.yaml_content) return;

  try {
    await navigator.clipboard.writeText(props.script.yaml_content);
    Message.success('YAML脚本已复制到剪贴板');
  } catch (error) {
    console.error('复制失败:', error);
    Message.error('复制失败');
  }
};

const loadExecutions = async () => {
  if (!props.script) return;

  loadingExecutions.value = true;
  try {
    const response = await automationScriptService.getScriptExecutions(props.script.id);
    executions.value = response.data.results || response.data;
  } catch (error: any) {
    console.error('加载执行记录失败:', error);
    Message.error('加载执行记录失败');
  } finally {
    loadingExecutions.value = false;
  }
};

const viewExecution = (execution: ScriptExecution) => {
  selectedExecution.value = execution;
  showExecutionDetail.value = true;
};

const viewReport = (execution: ScriptExecution) => {
  if (!execution.report_url) return;
  
  // 在新窗口打开报告
  const reportUrl = automationScriptService.getExecutionReportUrl(execution.id);
  window.open(reportUrl, '_blank');
};

const viewLogs = (execution: ScriptExecution) => {
  selectedExecution.value = execution;
  showLogsModal.value = true;
};

const cancelExecution = async (execution: ScriptExecution) => {
  try {
    await automationScriptService.cancelExecution(execution.id);
    Message.success('执行已取消');
    loadExecutions();
  } catch (error: any) {
    console.error('取消执行失败:', error);
    Message.error('取消执行失败');
  }
};

const refreshDetail = () => {
  emit('refresh');
  if (activeTab.value === 'executions') {
    loadExecutions();
  }
};

// 辅助方法
const getStatusColor = (status: string) => {
  const colors = {
    draft: 'gray',
    generated: 'blue',
    ready: 'cyan',
    running: 'orange',
    completed: 'green',
    failed: 'red'
  };
  return colors[status] || 'gray';
};

const getScriptTypeColor = (type: string) => {
  const colors = {
    web: 'blue',
    android: 'green',
    ios: 'orange'
  };
  return colors[type] || 'gray';
};

const getExecutionStatusColor = (status: string) => {
  const colors = {
    pending: 'gray',
    running: 'orange',
    completed: 'green',
    failed: 'red',
    cancelled: 'gray'
  };
  return colors[status] || 'gray';
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString();
};

// 监听器
watch(() => props.visible, (visible) => {
  if (visible) {
    activeTab.value = 'info';
    loadExecutions();
  }
});

watch(activeTab, (tab) => {
  if (tab === 'executions' && props.visible) {
    loadExecutions();
  }
});
</script>

<style scoped>
.script-detail {
  min-height: 600px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-1);
}

.header-info {
  flex: 1;
}

.status-badge {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.script-meta {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  gap: 8px;
  font-size: 14px;
}

.meta-label {
  color: var(--color-text-3);
}

.meta-value {
  color: var(--color-text-1);
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.detail-content {
  padding: 0;
}

.info-panel {
  padding: 24px;
}

.info-section {
  margin-bottom: 32px;
}

.info-section h3 {
  margin: 0 0 16px 0;
  color: var(--color-text-1);
  font-size: 16px;
  font-weight: 600;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  gap: 12px;
}

.info-item label {
  min-width: 80px;
  color: var(--color-text-3);
  font-weight: 500;
}

.info-item span {
  color: var(--color-text-1);
}

.content-panel {
  padding: 24px;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.content-header h3 {
  margin: 0;
  color: var(--color-text-1);
  font-size: 16px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.content-text {
  background: var(--color-bg-2);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.content-text pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.yaml-editor {
  background: #f8f9fa;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 16px;
  max-height: 500px;
  overflow: auto;
}

.yaml-editor pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  color: var(--color-text-4);
  margin-bottom: 16px;
}

.executions-panel {
  padding: 24px;
}

.executions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.executions-header h3 {
  margin: 0;
  color: var(--color-text-1);
  font-size: 16px;
  font-weight: 600;
}

.executions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.execution-item {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.execution-item:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-light-1);
}

.execution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.execution-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.execution-id {
  font-family: monospace;
  font-weight: 600;
  color: var(--color-text-1);
}

.execution-time {
  font-size: 12px;
  color: var(--color-text-3);
}

.execution-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.stat-item {
  display: flex;
  gap: 4px;
  font-size: 12px;
}

.stat-label {
  color: var(--color-text-3);
}

.stat-value {
  font-weight: 600;
  color: var(--color-text-1);
}

.stat-value.success {
  color: var(--color-success);
}

.stat-value.error {
  color: var(--color-danger);
}

.execution-actions {
  display: flex;
  gap: 8px;
}

.empty-executions {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .detail-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .script-meta {
    justify-content: center;
  }
  
  .header-actions {
    width: 100%;
    justify-content: center;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .execution-header {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
  
  .execution-stats {
    flex-wrap: wrap;
  }
}
</style>