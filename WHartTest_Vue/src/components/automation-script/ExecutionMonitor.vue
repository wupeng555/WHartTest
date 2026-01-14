<template>
  <div class="execution-monitor">
    <!-- 执行状态头部 -->
    <div class="execution-header">
      <div class="execution-info">
        <h3>{{ execution?.script_name || '脚本执行' }}</h3>
        <a-tag :color="getStatusColor(execution?.status)">
          {{ getStatusText(execution?.status) }}
        </a-tag>
      </div>
      <div class="execution-actions">
        <a-button 
          v-if="execution?.status === 'running'" 
          type="primary" 
          status="danger"
          @click="stopExecution"
        >
          <template #icon><icon-stop /></template>
          停止执行
        </a-button>
        <a-button 
          v-if="execution?.status === 'completed' || execution?.status === 'failed'" 
          @click="downloadReport"
        >
          <template #icon><icon-download /></template>
          下载报告
        </a-button>
      </div>
    </div>

    <!-- 执行进度 -->
    <div v-if="execution?.status === 'running'" class="execution-progress">
      <a-progress 
        :percent="execution.progress || 0" 
        :status="execution.progress === 100 ? 'success' : 'normal'"
      />
      <div class="progress-info">
        <span>已执行: {{ execution.completed_steps || 0 }} / {{ execution.total_steps || 0 }} 步骤</span>
        <span>耗时: {{ formatDuration(execution.elapsed_time) }}</span>
      </div>
    </div>

    <!-- 实时日志 -->
    <div class="execution-logs">
      <div class="logs-header">
        <h4>执行日志</h4>
        <div class="logs-actions">
          <a-switch v-model="autoScroll" size="small">
            <template #checked>自动滚动</template>
            <template #unchecked>手动滚动</template>
          </a-switch>
          <a-button size="small" @click="clearLogs">清空日志</a-button>
        </div>
      </div>
      <div 
        ref="logsContainer" 
        class="logs-container"
        :class="{ 'auto-scroll': autoScroll }"
      >
        <div 
          v-for="(log, index) in logs" 
          :key="index"
          :class="['log-item', `log-${log.level}`]"
        >
          <span class="log-time">{{ formatTime(log.timestamp) }}</span>
          <span class="log-level">{{ log.level.toUpperCase() }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
        <div v-if="logs.length === 0" class="no-logs">
          暂无日志信息
        </div>
      </div>
    </div>

    <!-- 执行结果摘要 -->
    <div v-if="execution?.status !== 'running'" class="execution-summary">
      <h4>执行摘要</h4>
      <a-row :gutter="16">
        <a-col :span="6">
          <a-statistic title="总步骤数" :value="execution?.total_steps || 0" />
        </a-col>
        <a-col :span="6">
          <a-statistic 
            title="成功步骤" 
            :value="execution?.success_steps || 0" 
            :value-style="{ color: '#52c41a' }"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic 
            title="失败步骤" 
            :value="execution?.failed_steps || 0" 
            :value-style="{ color: '#ff4d4f' }"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic 
            title="总耗时" 
            :value="formatDuration(execution?.total_time)" 
            suffix="秒"
          />
        </a-col>
      </a-row>
    </div>

    <!-- 截图展示 -->
    <div v-if="screenshots.length > 0" class="execution-screenshots">
      <h4>执行截图</h4>
      <div class="screenshots-grid">
        <div 
          v-for="(screenshot, index) in screenshots" 
          :key="index"
          class="screenshot-item"
          @click="previewScreenshot(screenshot)"
        >
          <img :src="screenshot.url" :alt="screenshot.description" />
          <div class="screenshot-info">
            <div class="screenshot-step">步骤 {{ screenshot.step }}</div>
            <div class="screenshot-desc">{{ screenshot.description }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 截图预览模态框 -->
    <a-modal 
      v-model:visible="screenshotPreviewVisible" 
      title="截图预览"
      :footer="false"
      width="80%"
    >
      <div v-if="currentScreenshot" class="screenshot-preview">
        <img :src="currentScreenshot.url" :alt="currentScreenshot.description" />
        <div class="screenshot-details">
          <p><strong>步骤:</strong> {{ currentScreenshot.step }}</p>
          <p><strong>描述:</strong> {{ currentScreenshot.description }}</p>
          <p><strong>时间:</strong> {{ formatTime(currentScreenshot.timestamp) }}</p>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { Message } from '@arco-design/web-vue';
import {
  IconStop,
  IconDownload,
  IconEye
} from '@arco-design/web-vue/es/icon';
import { automationScriptService } from '@/services/automationScriptService';

interface ExecutionLog {
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
}

interface Screenshot {
  step: number;
  url: string;
  description: string;
  timestamp: string;
}

interface ExecutionData {
  id: string;
  script_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'stopped';
  progress: number;
  completed_steps: number;
  total_steps: number;
  success_steps: number;
  failed_steps: number;
  elapsed_time: number;
  total_time: number;
}

const props = defineProps<{
  executionId: string;
}>();

const emit = defineEmits<{
  executionCompleted: [result: any];
  executionFailed: [error: any];
}>();

// 响应式数据
const execution = ref<ExecutionData | null>(null);
const logs = ref<ExecutionLog[]>([]);
const screenshots = ref<Screenshot[]>([]);
const autoScroll = ref(true);
const screenshotPreviewVisible = ref(false);
const currentScreenshot = ref<Screenshot | null>(null);

// DOM引用
const logsContainer = ref<HTMLElement>();

// WebSocket连接
let websocket: WebSocket | null = null;
let statusPollingTimer: number | null = null;

// 初始化监控
onMounted(() => {
  initializeMonitoring();
});

// 清理资源
onUnmounted(() => {
  cleanup();
});

// 监听自动滚动变化
watch(() => logs.value.length, () => {
  if (autoScroll.value) {
    nextTick(() => {
      scrollToBottom();
    });
  }
});

const initializeMonitoring = async () => {
  try {
    // 获取执行信息
    await loadExecutionInfo();
    
    // 建立WebSocket连接
    connectWebSocket();
    
    // 开始状态轮询（作为WebSocket的备用方案）
    startStatusPolling();
    
  } catch (error) {
    console.error('初始化监控失败:', error);
    Message.error('初始化监控失败');
  }
};

const loadExecutionInfo = async () => {
  try {
    const response = await automationScriptService.getExecution(props.executionId);
    execution.value = response.data;
    
    // 加载历史日志
    await loadLogs();
    
    // 加载截图
    await loadScreenshots();
    
  } catch (error) {
    console.error('加载执行信息失败:', error);
  }
};

const loadLogs = async () => {
  try {
    const response = await automationScriptService.getExecutionLogs(props.executionId);
    logs.value = response.data || [];
  } catch (error) {
    console.error('加载日志失败:', error);
  }
};

const loadScreenshots = async () => {
  try {
    const response = await automationScriptService.getExecutionScreenshots(props.executionId);
    screenshots.value = response.data || [];
  } catch (error) {
    console.error('加载截图失败:', error);
  }
};

const connectWebSocket = () => {
  try {
    const wsUrl = `ws://localhost:8000/ws/execution/${props.executionId}/`;
    websocket = new WebSocket(wsUrl);
    
    websocket.onopen = () => {
      console.log('WebSocket连接已建立');
    };
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };
    
    websocket.onclose = () => {
      console.log('WebSocket连接已关闭');
      // 尝试重连
      setTimeout(() => {
        if (execution.value?.status === 'running') {
          connectWebSocket();
        }
      }, 3000);
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket错误:', error);
    };
    
  } catch (error) {
    console.error('WebSocket连接失败:', error);
  }
};

const handleWebSocketMessage = (data: any) => {
  switch (data.type) {
    case 'execution_update':
      if (execution.value) {
        Object.assign(execution.value, data.data);
      }
      break;
      
    case 'log_message':
      logs.value.push(data.data);
      break;
      
    case 'screenshot':
      screenshots.value.push(data.data);
      break;
      
    case 'execution_completed':
      if (execution.value) {
        execution.value.status = 'completed';
      }
      emit('executionCompleted', data.data);
      cleanup();
      break;
      
    case 'execution_failed':
      if (execution.value) {
        execution.value.status = 'failed';
      }
      emit('executionFailed', data.data);
      cleanup();
      break;
  }
};

const startStatusPolling = () => {
  statusPollingTimer = window.setInterval(async () => {
    if (execution.value?.status === 'running') {
      await loadExecutionInfo();
    } else {
      cleanup();
    }
  }, 2000);
};

const stopExecution = async () => {
  try {
    await automationScriptService.stopExecution(props.executionId);
    Message.success('停止执行请求已发送');
  } catch (error) {
    console.error('停止执行失败:', error);
    Message.error('停止执行失败');
  }
};

const downloadReport = async () => {
  try {
    const response = await automationScriptService.downloadExecutionReport(props.executionId);
    
    // 创建下载链接
    const blob = new Blob([response.data], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `execution_report_${props.executionId}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    Message.success('报告下载成功');
  } catch (error) {
    console.error('下载报告失败:', error);
    Message.error('下载报告失败');
  }
};

const clearLogs = () => {
  logs.value = [];
};

const scrollToBottom = () => {
  if (logsContainer.value) {
    logsContainer.value.scrollTop = logsContainer.value.scrollHeight;
  }
};

const previewScreenshot = (screenshot: Screenshot) => {
  currentScreenshot.value = screenshot;
  screenshotPreviewVisible.value = true;
};

const cleanup = () => {
  if (websocket) {
    websocket.close();
    websocket = null;
  }
  
  if (statusPollingTimer) {
    clearInterval(statusPollingTimer);
    statusPollingTimer = null;
  }
};

// 工具函数
const getStatusColor = (status?: string) => {
  switch (status) {
    case 'running': return 'blue';
    case 'completed': return 'green';
    case 'failed': return 'red';
    case 'stopped': return 'orange';
    default: return 'gray';
  }
};

const getStatusText = (status?: string) => {
  switch (status) {
    case 'pending': return '等待中';
    case 'running': return '执行中';
    case 'completed': return '已完成';
    case 'failed': return '执行失败';
    case 'stopped': return '已停止';
    default: return '未知';
  }
};

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString();
};

const formatDuration = (seconds?: number) => {
  if (!seconds) return '0';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return mins > 0 ? `${mins}分${secs}秒` : `${secs}秒`;
};
</script>

<style scoped>
.execution-monitor {
  padding: 16px;
  background: #fff;
  border-radius: 8px;
}

.execution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.execution-info h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
}

.execution-progress {
  margin-bottom: 24px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #666;
}

.execution-logs {
  margin-bottom: 24px;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.logs-header h4 {
  margin: 0;
}

.logs-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.logs-container {
  height: 300px;
  overflow-y: auto;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  padding: 8px;
  background: #fafafa;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
}

.log-item {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
  line-height: 1.4;
}

.log-time {
  color: #999;
  min-width: 80px;
}

.log-level {
  min-width: 50px;
  font-weight: bold;
}

.log-info .log-level { color: #1890ff; }
.log-warn .log-level { color: #faad14; }
.log-error .log-level { color: #ff4d4f; }
.log-debug .log-level { color: #52c41a; }

.log-message {
  flex: 1;
  word-break: break-all;
}

.no-logs {
  text-align: center;
  color: #999;
  padding: 40px;
}

.execution-summary {
  margin-bottom: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.execution-summary h4 {
  margin: 0 0 16px 0;
}

.execution-screenshots h4 {
  margin: 0 0 16px 0;
}

.screenshots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.screenshot-item {
  cursor: pointer;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  overflow: hidden;
  transition: all 0.3s;
}

.screenshot-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.screenshot-item img {
  width: 100%;
  height: 120px;
  object-fit: cover;
}

.screenshot-info {
  padding: 8px;
}

.screenshot-step {
  font-size: 12px;
  color: #1890ff;
  font-weight: bold;
}

.screenshot-desc {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.screenshot-preview img {
  width: 100%;
  max-height: 60vh;
  object-fit: contain;
}

.screenshot-details {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.screenshot-details p {
  margin: 8px 0;
}
</style>