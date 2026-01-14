<template>
  <div class="execution-report-viewer">
    <!-- 报告头部 -->
    <div class="report-header">
      <div class="header-info">
        <h2>{{ execution?.script_name }} - 执行报告</h2>
        <div class="execution-meta">
          <a-tag :color="getStatusColor(execution?.status)">
            {{ execution?.status_display }}
          </a-tag>
          <span class="execution-id">执行ID: {{ execution?.execution_id }}</span>
          <span class="execution-time">
            执行时间: {{ formatDate(execution?.created_at) }}
          </span>
        </div>
      </div>
      <div class="header-actions">
        <a-button @click="refreshReport">
          <template #icon><icon-refresh /></template>
          刷新
        </a-button>
        <a-button @click="openInNewWindow" v-if="execution?.report_url">
          <template #icon><icon-export /></template>
          新窗口打开
        </a-button>
      </div>
    </div>

    <!-- 执行统计 -->
    <div v-if="execution && execution.total_tests > 0" class="execution-stats">
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon total">📊</div>
          <div class="stat-content">
            <div class="stat-value">{{ execution.total_tests }}</div>
            <div class="stat-label">总测试数</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon success">✅</div>
          <div class="stat-content">
            <div class="stat-value">{{ execution.passed_tests }}</div>
            <div class="stat-label">通过</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon error">❌</div>
          <div class="stat-content">
            <div class="stat-value">{{ execution.failed_tests }}</div>
            <div class="stat-label">失败</div>
          </div>
        </div>
        <div class="stat-card" v-if="execution.execution_time">
          <div class="stat-icon time">⏱️</div>
          <div class="stat-content">
            <div class="stat-value">{{ execution.execution_time.toFixed(2) }}s</div>
            <div class="stat-label">执行时间</div>
          </div>
        </div>
      </div>
      
      <!-- 成功率进度条 -->
      <div class="success-rate">
        <div class="rate-header">
          <span>成功率</span>
          <span class="rate-value">{{ getSuccessRate() }}%</span>
        </div>
        <a-progress
          :percent="getSuccessRate()"
          :status="getSuccessRate() === 100 ? 'success' : getSuccessRate() > 80 ? 'normal' : 'exception'"
          :show-text="false"
        />
      </div>
    </div>

    <!-- 报告内容 -->
    <div class="report-content">
      <a-tabs v-model:active-key="activeTab" type="card">
        <!-- HTML报告 -->
        <a-tab-pane key="report" title="测试报告">
          <div class="report-iframe-container">
            <div v-if="loading" class="loading-container">
              <a-spin size="large" />
              <p>正在加载报告...</p>
            </div>
            <iframe
              v-else-if="reportUrl"
              ref="reportIframe"
              :src="reportUrl"
              class="report-iframe"
              @load="handleIframeLoad"
              @error="handleIframeError"
            />
            <div v-else class="no-report">
              <icon-file-text class="no-report-icon" />
              <p>暂无测试报告</p>
              <p class="no-report-hint">
                {{ execution?.status === 'running' ? '测试正在执行中，请稍后刷新' : '测试执行失败或未生成报告' }}
              </p>
            </div>
          </div>
        </a-tab-pane>

        <!-- 执行日志 -->
        <a-tab-pane key="logs" title="执行日志">
          <ExecutionLogs :execution="execution" />
        </a-tab-pane>

        <!-- 输出信息 -->
        <a-tab-pane key="output" title="输出信息">
          <div class="output-content">
            <div v-if="execution?.stdout" class="output-section">
              <h4>标准输出</h4>
              <pre class="output-text stdout">{{ execution.stdout }}</pre>
            </div>
            <div v-if="execution?.stderr" class="output-section">
              <h4>错误输出</h4>
              <pre class="output-text stderr">{{ execution.stderr }}</pre>
            </div>
            <div v-if="!execution?.stdout && !execution?.stderr" class="no-output">
              <icon-info-circle class="no-output-icon" />
              <p>暂无输出信息</p>
            </div>
          </div>
        </a-tab-pane>

        <!-- 截图预览 -->
        <a-tab-pane key="screenshots" title="截图预览">
          <ScreenshotGallery :execution="execution" />
        </a-tab-pane>
      </a-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { Message } from '@arco-design/web-vue';
import {
  IconRefresh,
  IconExport,
  IconFileText,
  IconInfoCircle
} from '@arco-design/web-vue/es/icon';
import { automationScriptService, type ScriptExecution } from '@/services/automationScriptService';
import ExecutionLogs from './ExecutionLogs.vue';
import ScreenshotGallery from './ScreenshotGallery.vue';

interface Props {
  execution?: ScriptExecution | null;
}

const props = defineProps<Props>();

// 响应式数据
const activeTab = ref('report');
const loading = ref(false);
const reportIframe = ref<HTMLIFrameElement>();
const refreshTimer = ref<NodeJS.Timeout>();

// 计算属性
const reportUrl = computed(() => {
  if (!props.execution?.report_url) return null;
  return automationScriptService.getExecutionReportUrl(props.execution.id);
});

// 方法
const refreshReport = () => {
  if (reportIframe.value) {
    loading.value = true;
    reportIframe.value.src = reportIframe.value.src;
  }
};

const openInNewWindow = () => {
  if (reportUrl.value) {
    window.open(reportUrl.value, '_blank', 'width=1200,height=800');
  }
};

const handleIframeLoad = () => {
  loading.value = false;
  
  // 尝试调整iframe样式
  try {
    const iframe = reportIframe.value;
    if (iframe?.contentDocument) {
      const doc = iframe.contentDocument;
      
      // 添加响应式样式
      const style = doc.createElement('style');
      style.textContent = `
        body {
          margin: 0;
          padding: 16px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        .container {
          max-width: 100%;
          overflow-x: auto;
        }
        table {
          width: 100%;
          border-collapse: collapse;
        }
        img {
          max-width: 100%;
          height: auto;
        }
      `;
      doc.head.appendChild(style);
    }
  } catch (error) {
    console.warn('无法访问iframe内容:', error);
  }
};

const handleIframeError = () => {
  loading.value = false;
  Message.error('报告加载失败');
};

const getSuccessRate = () => {
  if (!props.execution || props.execution.total_tests === 0) return 0;
  return Math.round((props.execution.passed_tests / props.execution.total_tests) * 100);
};

const getStatusColor = (status?: string) => {
  const colors = {
    pending: 'gray',
    running: 'orange',
    completed: 'green',
    failed: 'red',
    cancelled: 'gray'
  };
  return colors[status || ''] || 'gray';
};

const formatDate = (dateString?: string) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleString();
};

// 自动刷新正在执行的任务
const startAutoRefresh = () => {
  if (props.execution?.status === 'running') {
    refreshTimer.value = setInterval(() => {
      refreshReport();
    }, 5000); // 每5秒刷新一次
  }
};

const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value);
    refreshTimer.value = undefined;
  }
};

// 监听器
watch(() => props.execution, (newExecution) => {
  stopAutoRefresh();
  if (newExecution?.status === 'running') {
    startAutoRefresh();
  }
}, { immediate: true });

watch(reportUrl, (newUrl) => {
  if (newUrl) {
    loading.value = true;
  }
});

// 生命周期
onMounted(() => {
  if (props.execution?.status === 'running') {
    startAutoRefresh();
  }
});

onUnmounted(() => {
  stopAutoRefresh();
});
</script>

<style scoped>
.execution-report-viewer {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-1);
}

.header-info h2 {
  margin: 0 0 8px 0;
  color: var(--color-text-1);
  font-size: 18px;
  font-weight: 600;
}

.execution-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 14px;
  color: var(--color-text-2);
}

.execution-id {
  font-family: monospace;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.execution-stats {
  padding: 24px;
  background: var(--color-bg-1);
  border-bottom: 1px solid var(--color-border);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.stat-icon.total {
  background: #e6f7ff;
}

.stat-icon.success {
  background: #f6ffed;
}

.stat-icon.error {
  background: #fff2f0;
}

.stat-icon.time {
  background: #f9f0ff;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-1);
  line-height: 1;
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-3);
  margin-top: 4px;
}

.success-rate {
  max-width: 400px;
}

.rate-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}

.rate-value {
  font-weight: 600;
  color: var(--color-text-1);
}

.report-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.report-iframe-container {
  position: relative;
  flex: 1;
  overflow: hidden;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  gap: 16px;
}

.report-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: white;
}

.no-report {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  text-align: center;
}

.no-report-icon {
  font-size: 48px;
  color: var(--color-text-4);
  margin-bottom: 16px;
}

.no-report-hint {
  color: var(--color-text-3);
  font-size: 12px;
  margin-top: 8px;
}

.output-content {
  padding: 24px;
  max-height: 500px;
  overflow-y: auto;
}

.output-section {
  margin-bottom: 24px;
}

.output-section h4 {
  margin: 0 0 12px 0;
  color: var(--color-text-1);
  font-size: 14px;
  font-weight: 600;
}

.output-text {
  background: #f8f9fa;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 16px;
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 300px;
  overflow-y: auto;
}

.output-text.stderr {
  background: #fff2f0;
  border-color: #ffccc7;
  color: #a8071a;
}

.no-output {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  text-align: center;
}

.no-output-icon {
  font-size: 48px;
  color: var(--color-text-4);
  margin-bottom: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .report-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .execution-meta {
    flex-direction: column;
    gap: 8px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: center;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-card {
    justify-content: center;
    text-align: center;
  }
}
</style>