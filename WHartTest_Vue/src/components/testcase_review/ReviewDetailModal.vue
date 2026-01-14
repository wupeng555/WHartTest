<template>
  <a-modal
    v-model:visible="visible"
    :title="review?.title || '评审详情'"
    width="1200px"
    :footer="false"
    :body-style="{ padding: 0 }"
  >
    <div v-if="review" class="review-detail">
      <!-- 头部信息 -->
      <div class="detail-header">
        <div class="header-info">
          <div class="status-badge">
            <a-tag :color="getStatusColor(review.status)" size="large">
              {{ getStatusText(review.status) }}
            </a-tag>
          </div>
          <div class="review-meta">
            <div class="meta-item">
              <span class="meta-label">项目:</span>
              <span class="meta-value">{{ review.project_name }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">类型:</span>
              <span class="meta-value">{{ getReviewTypeText(review.review_type) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">创建时间:</span>
              <span class="meta-value">{{ formatDate(review.created_at) }}</span>
            </div>
            <div v-if="review.completed_at" class="meta-item">
              <span class="meta-label">完成时间:</span>
              <span class="meta-value">{{ formatDate(review.completed_at) }}</span>
            </div>
          </div>
        </div>
        <div class="header-actions">
          <a-button
            v-if="review.status === 'pending'"
            type="primary"
            @click="startReview"
            :loading="starting"
          >
            开始评审
          </a-button>
          <a-button @click="createChatSession">
            <template #icon><icon-message /></template>
            AI对话
          </a-button>
          <a-button @click="refreshDetail">
            <template #icon><icon-refresh /></template>
            刷新
          </a-button>
        </div>
      </div>

      <!-- 内容区域 -->
      <div class="detail-content">
        <a-tabs v-model:active-key="activeTab" type="line">
          <!-- 评审结果 -->
          <a-tab-pane key="result" title="评审结果">
            <div class="result-panel">
              <div v-if="review.status === 'completed' && review.review_result" class="result-content">
                <!-- 评分显示 -->
                <div v-if="review.review_score !== null" class="score-section">
                  <div class="score-display">
                    <div class="score-number">{{ review.review_score }}/10</div>
                    <a-rate
                      :model-value="review.review_score / 2"
                      :count="5"
                      :allow-half="true"
                      disabled
                    />
                  </div>
                  <div class="score-label">综合评分</div>
                </div>

                <!-- 评审报告 -->
                <div class="report-section">
                  <h3>评审报告</h3>
                  <div class="markdown-content" v-html="formatMarkdown(review.review_result)"></div>
                </div>
              </div>

              <div v-else-if="review.status === 'reviewing'" class="status-message">
                <a-spin size="large" />
                <p>AI正在评审中，请稍候...</p>
              </div>

              <div v-else-if="review.status === 'failed'" class="error-message">
                <icon-exclamation-circle-fill class="error-icon" />
                <div>
                  <h4>评审失败</h4>
                  <p>{{ review.error_message || '未知错误' }}</p>
                </div>
              </div>

              <div v-else class="empty-message">
                <icon-file-text class="empty-icon" />
                <p>暂无评审结果</p>
              </div>
            </div>
          </a-tab-pane>

          <!-- 文件内容 -->
          <a-tab-pane key="content" title="测试用例">
            <div class="content-panel">
              <div v-if="review.original_file" class="file-info">
                <div class="file-header">
                  <div class="file-details">
                    <icon-file class="file-icon" />
                    <div>
                      <div class="file-name">{{ getFileName(review.original_file) }}</div>
                      <div class="file-meta">
                        {{ review.file_type?.toUpperCase() }} • {{ formatFileSize(review.file_size) }}
                      </div>
                    </div>
                  </div>
                  <a-button size="small" @click="downloadFile">
                    <template #icon><icon-download /></template>
                    下载
                  </a-button>
                </div>
              </div>

              <div v-if="review.file_content" class="file-content">
                <h4>文件内容</h4>
                <pre class="content-text">{{ review.file_content }}</pre>
              </div>

              <div v-else class="empty-content">
                <icon-file-text class="empty-icon" />
                <p>无文件内容</p>
              </div>
            </div>
          </a-tab-pane>

          <!-- AI对话 -->
          <a-tab-pane key="chat" title="AI对话">
            <div class="chat-panel">
              <AIReviewChat
                v-if="review"
                :review-id="review.id"
                :session-id="selectedSessionId"
                :file-content="review.file_content"
                @session-created="handleSessionCreated"
                @message-added="handleMessageAdded"
              />
            </div>
          </a-tab-pane>
                        </div>
                        <div class="message-text" v-html="formatMessageContent(message.content)"></div>
                      </div>
                    </div>
                  </div>

                  <!-- 输入框 -->
                  <div class="chat-input">
                    <a-textarea
                      v-model="chatMessage"
                      placeholder="输入您的问题..."
                      :rows="3"
                      @keydown.ctrl.enter="sendMessage"
                    />
                    <div class="input-actions">
                      <span class="input-tip">Ctrl + Enter 发送</span>
                      <a-button
                        type="primary"
                        @click="sendMessage"
                        :loading="sending"
                        :disabled="!chatMessage.trim()"
                      >
                        发送
                      </a-button>
                    </div>
                  </div>
                </div>
              </div>

              <div v-else class="empty-chat">
                <icon-message class="empty-icon" />
                <p>暂无对话会话</p>
                <a-button type="primary" @click="createChatSession">
                  创建第一个会话
                </a-button>
              </div>
            </div>
          </a-tab-pane>

          <!-- 评审配置 -->
          <a-tab-pane key="config" title="配置信息">
            <div class="config-panel">
              <a-descriptions :column="2" bordered>
                <a-descriptions-item label="评审类型">
                  {{ getReviewTypeText(review.review_type) }}
                </a-descriptions-item>
                <a-descriptions-item label="AI模型">
                  {{ review.ai_model }}
                </a-descriptions-item>
                <a-descriptions-item label="API基础URL">
                  {{ review.api_base_url || '-' }}
                </a-descriptions-item>
                <a-descriptions-item label="处理耗时">
                  {{ review.processing_time ? `${review.processing_time.toFixed(2)}秒` : '-' }}
                </a-descriptions-item>
                <a-descriptions-item label="测试用例数量">
                  {{ review.total_test_cases }}
                </a-descriptions-item>
                <a-descriptions-item label="创建人">
                  {{ review.creator_name || '-' }}
                </a-descriptions-item>
              </a-descriptions>

              <div v-if="review.custom_prompt" class="custom-prompt">
                <h4>自定义提示词</h4>
                <pre class="prompt-text">{{ review.custom_prompt }}</pre>
              </div>
            </div>
          </a-tab-pane>
        </a-tabs>
      </div>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch, nextTick } from 'vue';
import { Message } from '@arco-design/web-vue';
import {
  IconMessage,
  IconRefresh,
  IconExclamationCircleFill,
  IconFileText,
  IconFile,
  IconDownload,
  IconUser,
  IconRobot
} from '@arco-design/web-vue/es/icon';
import { testcaseReviewService, type TestCaseReview } from '@/services/testcaseReviewService';
import AIReviewChat from './AIReviewChat.vue';
  IconFile,
  IconDownload,
  IconUser,
  IconRobot,
} from '@arco-design/web-vue/es/icon';
import {
  testcaseReviewService,
  type TestCaseReview,
  type ReviewSession,
  type ReviewMessage,
} from '@/services/testcaseReviewService';

interface Props {
  visible: boolean;
  review?: TestCaseReview | null;
}

interface Emits {
  (e: 'update:visible', visible: boolean): void;
  (e: 'refresh'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// 响应式数据
const starting = ref(false);
const activeTab = ref('result');
const sessions = ref<ReviewSession[]>([]);
const messages = ref<ReviewMessage[]>([]);
const selectedSessionId = ref<string>('');
const chatMessage = ref('');
const sending = ref(false);
const messagesRef = ref();

// 监听器
watch(
  () => props.visible,
  (visible) => {
    if (visible && props.review) {
      loadSessions();
    }
  }
);

watch(
  () => props.review,
  (review) => {
    if (review && props.visible) {
      loadSessions();
    }
  }
);

// 方法
const refreshDetail = () => {
  emit('refresh');
};

const startReview = async () => {
  if (!props.review) return;

  starting.value = true;
  try {
    await testcaseReviewService.startReview(props.review.id);
    Message.success('评审已开始');
    emit('refresh');
  } catch (error: any) {
    console.error('开始评审失败:', error);
    Message.error(error.response?.data?.error || '开始评审失败');
  } finally {
    starting.value = false;
  }
};

const downloadFile = async () => {
  if (!props.review?.original_file) return;

  try {
    const response = await testcaseReviewService.downloadFile(props.review.id);
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.download = getFileName(props.review.original_file);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('文件下载失败:', error);
    Message.error('文件下载失败');
  }
};

const loadSessions = async () => {
  if (!props.review) return;

  try {
    const response = await testcaseReviewService.getSessions({
      review: props.review.id,
    });
    sessions.value = response.data.results || response.data;
    
    // 自动选择第一个会话
    if (sessions.value.length > 0) {
      selectedSessionId.value = sessions.value[0].id;
      loadMessages();
    }
  } catch (error) {
    console.error('加载会话失败:', error);
  }
};

// AI对话相关方法
const handleSessionCreated = (sessionId: string) => {
  selectedSessionId.value = sessionId;
  loadSessions(); // 重新加载会话列表
};

const handleMessageAdded = (message: any) => {
  // 可以在这里处理消息添加后的逻辑
  console.log('新消息:', message);
};
    }
  } catch (error) {
    console.error('加载会话失败:', error);
  }
};

const loadMessages = async () => {
  if (!selectedSessionId.value) return;

  try {
    const response = await testcaseReviewService.getMessages({
      session: selectedSessionId.value,
    });
    messages.value = response.data.results || response.data;
    
    // 滚动到底部
    nextTick(() => {
      scrollToBottom();
    });
  } catch (error) {
    console.error('加载消息失败:', error);
  }
};

const createChatSession = async () => {
  if (!props.review) return;

  try {
    const sessionName = `会话 ${new Date().toLocaleString()}`;
    const response = await testcaseReviewService.createSession(props.review.id, sessionName);
    
    sessions.value.unshift(response.data);
    selectedSessionId.value = response.data.id;
    messages.value = [];
    activeTab.value = 'chat';
    
    Message.success('会话创建成功');
  } catch (error) {
    console.error('创建会话失败:', error);
    Message.error('创建会话失败');
  }
};

const sendMessage = async () => {
  if (!props.review || !selectedSessionId.value || !chatMessage.value.trim()) return;

  const message = chatMessage.value.trim();
  chatMessage.value = '';
  sending.value = true;

  try {
    const response = await testcaseReviewService.chat(props.review.id, {
      session_id: selectedSessionId.value,
      message,
    });

    // 重新加载消息
    await loadMessages();
    
    Message.success('消息发送成功');
  } catch (error: any) {
    console.error('发送消息失败:', error);
    Message.error(error.response?.data?.error || '发送消息失败');
    // 恢复消息内容
    chatMessage.value = message;
  } finally {
    sending.value = false;
  }
};

const scrollToBottom = () => {
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight;
  }
};

// 工具函数
const getStatusColor = (status: string) => {
  const colors = {
    pending: 'orange',
    reviewing: 'blue',
    completed: 'green',
    failed: 'red',
  };
  return colors[status] || 'gray';
};

const getStatusText = (status: string) => {
  const texts = {
    pending: '待评审',
    reviewing: '评审中',
    completed: '已完成',
    failed: '评审失败',
  };
  return texts[status] || status;
};

const getReviewTypeText = (type: string) => {
  const texts = {
    completeness: '完整性评审',
    boundary: '边界值评审',
    ambiguity: '二义性检查',
    logic: '逻辑性评审',
    coverage: '覆盖率评审',
    custom: '自定义评审',
  };
  return texts[type] || type;
};

const getFileName = (filePath: string) => {
  if (!filePath) return '';
  return filePath.split('/').pop() || filePath;
};

const formatFileSize = (size?: number) => {
  if (!size) return '';
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString();
};

const formatTime = (dateString: string) => {
  return new Date(dateString).toLocaleTimeString();
};

const formatMarkdown = (content: string) => {
  // 简单的Markdown渲染
  return content
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^- (.*$)/gim, '<li>$1</li>')
    .replace(/\n/g, '<br>');
};

const formatMessageContent = (content: string) => {
  return formatMarkdown(content);
};
</script>

<style scoped>
.review-detail {
  height: 80vh;
  display: flex;
  flex-direction: column;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e6eb;
  background: #f7f8fa;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.status-badge {
  display: flex;
  align-items: center;
}

.review-meta {
  display: flex;
  gap: 20px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-label {
  color: #86909c;
  font-size: 14px;
}

.meta-value {
  color: #1d2129;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.detail-content {
  flex: 1;
  overflow: hidden;
}

.result-panel,
.content-panel,
.chat-panel,
.config-panel {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.score-section {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
  padding: 20px;
  background: #f7f8fa;
  border-radius: 8px;
}

.score-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.score-number {
  font-size: 32px;
  font-weight: bold;
  color: #165dff;
}

.score-label {
  color: #86909c;
  font-size: 14px;
}

.report-section h3 {
  margin-bottom: 16px;
  color: #1d2129;
}

.markdown-content {
  line-height: 1.6;
  color: #4e5969;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3 {
  color: #1d2129;
  margin: 16px 0 8px 0;
}

.markdown-content li {
  margin: 4px 0;
}

.status-message,
.error-message,
.empty-message,
.empty-content,
.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #86909c;
}

.error-icon,
.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.error-icon {
  color: #f53f3f;
}

.file-info {
  margin-bottom: 24px;
}

.file-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f7f8fa;
  border-radius: 8px;
}

.file-details {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-icon {
  font-size: 24px;
  color: #165dff;
}

.file-name {
  font-weight: 500;
  color: #1d2129;
}

.file-meta {
  font-size: 12px;
  color: #86909c;
}

.file-content h4 {
  margin-bottom: 12px;
  color: #1d2129;
}

.content-text {
  background: #f7f8fa;
  padding: 16px;
  border-radius: 8px;
  white-space: pre-wrap;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
  max-height: 400px;
  overflow-y: auto;
}

.chat-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.session-selector {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.messages-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.messages-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
  max-height: 400px;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.message-user .message-avatar {
  background: #165dff;
  color: white;
}

.message-ai .message-avatar {
  background: #00b42a;
  color: white;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.message-sender {
  font-weight: 500;
  color: #1d2129;
}

.message-time {
  font-size: 12px;
  color: #86909c;
}

.message-text {
  color: #4e5969;
  line-height: 1.5;
  word-wrap: break-word;
}

.chat-input {
  border-top: 1px solid #e5e6eb;
  padding-top: 16px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.input-tip {
  font-size: 12px;
  color: #86909c;
}

.custom-prompt {
  margin-top: 24px;
}

.custom-prompt h4 {
  margin-bottom: 12px;
  color: #1d2129;
}

.prompt-text {
  background: #f7f8fa;
  padding: 16px;
  border-radius: 8px;
  white-space: pre-wrap;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
}
</style>