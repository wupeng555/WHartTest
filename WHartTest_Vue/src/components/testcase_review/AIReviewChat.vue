<template>
  <div class="ai-review-chat">
    <!-- 聊天消息区域 -->
    <div class="chat-messages" ref="messagesContainer">
      <div
        v-for="message in messages"
        :key="message.id"
        :class="['message', `message-${message.role}`]"
      >
        <div class="message-avatar">
          <icon-user v-if="message.role === 'user'" />
          <icon-robot v-else />
        </div>
        <div class="message-content">
          <div class="message-text" v-html="formatMessage(message.content)"></div>
          <div class="message-time">{{ formatTime(message.created_at) }}</div>
        </div>
      </div>
      
      <!-- 打字指示器 -->
      <div v-if="isTyping" class="message message-ai">
        <div class="message-avatar">
          <icon-robot />
        </div>
        <div class="message-content">
          <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 快速评审按钮 -->
    <div class="quick-review-section" v-if="hasFileContent">
      <div class="section-title">⚡ 快速评审</div>
      <div class="quick-review-buttons">
        <a-button
          v-for="type in reviewTypes"
          :key="type.id"
          :class="['review-btn', type.color]"
          @click="quickReview(type)"
          :loading="isReviewing"
        >
          {{ type.icon }} {{ type.name }}
        </a-button>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input-container">
      <div class="input-wrapper">
        <a-textarea
          v-model="inputMessage"
          placeholder="输入您的问题或评审要求..."
          :rows="2"
          :auto-size="{ minRows: 2, maxRows: 6 }"
          @keydown="handleKeyDown"
        />
        <a-button
          type="primary"
          :loading="isSending"
          :disabled="!inputMessage.trim()"
          @click="sendMessage"
          class="send-button"
        >
          <template #icon><icon-send /></template>
        </a-button>
      </div>
    </div>

    <!-- AI模型选择 -->
    <div class="model-selector">
      <a-select
        v-model="selectedModel"
        size="small"
        style="width: 120px"
        @change="handleModelChange"
      >
        <a-option value="deepseek">DeepSeek</a-option>
        <a-option value="qianwen">千问</a-option>
        <a-option value="gpt-4">GPT-4</a-option>
        <a-option value="claude">Claude</a-option>
      </a-select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick, onMounted, watch, computed } from 'vue';
import { Message } from '@arco-design/web-vue';
import { testcaseReviewService } from '@/services/testcaseReviewService';
import { IconUser, IconRobot, IconSend } from '@arco-design/web-vue/es/icon';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

interface ReviewType {
  id: string;
  name: string;
  icon: string;
  color: string;
  prompt: string;
}

const props = defineProps<{
  reviewId: string;
  sessionId?: string;
  fileContent?: string;
}>();

const emit = defineEmits<{
  sessionCreated: [sessionId: string];
  messageAdded: [message: ChatMessage];
}>();

// 响应式数据
const messages = ref<ChatMessage[]>([]);
const inputMessage = ref('');
const isTyping = ref(false);
const isSending = ref(false);
const isReviewing = ref(false);
const selectedModel = ref('deepseek');
const messagesContainer = ref<HTMLElement>();

// 默认评审类型
const reviewTypes = ref<ReviewType[]>([
  {
    id: 'boundary',
    name: '边界值评审',
    icon: '📊',
    color: 'boundary',
    prompt: `你是一位资深的测试工程师，专注于边界值测试分析。请对以下测试用例进行全面的边界值评审：

请重点关注以下方面：
1. **边界值识别**：是否识别了所有关键的边界值点
2. **边界测试覆盖**：是否包含了最小值、最大值、临界值测试
3. **异常边界**：是否考虑了超出边界的异常情况
4. **数据类型边界**：针对不同数据类型的边界值测试
5. **业务边界**：业务规则相关的边界值测试

测试用例内容：
{content}`
  },
  {
    id: 'ambiguity',
    name: '二义性检查',
    icon: '❓',
    color: 'ambiguity',
    prompt: `你是一位专业的测试分析师，专门识别测试用例中的二义性问题。请对以下测试用例进行二义性检查：

请重点检查以下方面：
1. **描述清晰度**：步骤描述是否清晰明确
2. **预期结果**：预期结果是否具体、可验证
3. **术语一致性**：专业术语使用是否一致
4. **操作明确性**：操作步骤是否容易理解和执行
5. **条件明确性**：前置条件和测试环境是否明确

测试用例内容：
{content}`
  },
  {
    id: 'completeness',
    name: '完整性评审',
    icon: '📋',
    color: 'completeness',
    prompt: `你是一位测试专家，请对以下测试用例进行完整性评审：

请检查以下方面：
1. **用例结构**：是否包含完整的用例要素
2. **场景覆盖**：是否覆盖了主要的测试场景
3. **数据完整性**：测试数据是否完整和有效
4. **步骤完整性**：测试步骤是否完整、逻辑清晰
5. **验证完整性**：验证点是否充分

测试用例内容：
{content}`
  },
  {
    id: 'format',
    name: '格式规范检查',
    icon: '📝',
    color: 'format',
    prompt: `你是一位测试规范专家，请对以下测试用例进行格式规范性检查：

请检查以下方面：
1. **格式标准**：是否符合测试用例编写规范
2. **命名规范**：用例名称是否规范
3. **结构统一**：用例结构是否统一
4. **语言规范**：语言表达是否规范
5. **排版格式**：排版是否整齐、易读

测试用例内容：
{content}`
  }
]);

// 计算属性
const hasFileContent = computed(() => !!props.fileContent);

// 方法
const sendMessage = async () => {
  if (!inputMessage.value.trim() || isSending.value) return;

  const userMessage = inputMessage.value.trim();
  inputMessage.value = '';
  isSending.value = true;

  try {
    // 添加用户消息
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString()
    };
    messages.value.push(userMsg);
    emit('messageAdded', userMsg);

    // 滚动到底部
    await nextTick();
    scrollToBottom();

    // 显示打字指示器
    isTyping.value = true;

    // 发送到AI
    const response = await testcaseReviewService.sendChatMessage(
      props.reviewId,
      props.sessionId || '',
      userMessage,
      selectedModel.value
    );

    // 添加AI回复
    const aiMsg: ChatMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: response.content,
      created_at: new Date().toISOString()
    };
    messages.value.push(aiMsg);
    emit('messageAdded', aiMsg);

    // 如果是新会话，触发会话创建事件
    if (response.session_id && !props.sessionId) {
      emit('sessionCreated', response.session_id);
    }

  } catch (error) {
    console.error('发送消息失败:', error);
    Message.error('发送消息失败，请重试');
  } finally {
    isTyping.value = false;
    isSending.value = false;
    await nextTick();
    scrollToBottom();
  }
};

const quickReview = async (type: ReviewType) => {
  if (!props.fileContent || isReviewing.value) return;

  isReviewing.value = true;

  try {
    // 构建评审消息
    const reviewPrompt = type.prompt.replace('{content}', props.fileContent);
    
    // 添加用户消息
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: `请进行${type.name}：`,
      created_at: new Date().toISOString()
    };
    messages.value.push(userMsg);

    // 滚动到底部并显示打字指示器
    await nextTick();
    scrollToBottom();
    isTyping.value = true;

    // 发送评审请求
    const response = await testcaseReviewService.sendChatMessage(
      props.reviewId,
      props.sessionId || '',
      reviewPrompt,
      selectedModel.value
    );

    // 添加AI回复
    const aiMsg: ChatMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: response.content,
      created_at: new Date().toISOString()
    };
    messages.value.push(aiMsg);
    emit('messageAdded', aiMsg);

    // 如果是新会话，触发会话创建事件
    if (response.session_id && !props.sessionId) {
      emit('sessionCreated', response.session_id);
    }

  } catch (error) {
    console.error('快速评审失败:', error);
    Message.error('评审失败，请重试');
  } finally {
    isTyping.value = false;
    isReviewing.value = false;
    await nextTick();
    scrollToBottom();
  }
};

const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
};

const handleModelChange = (model: string) => {
  selectedModel.value = model;
  // 可以在这里保存用户偏好
  localStorage.setItem('preferred_ai_model', model);
};

const formatMessage = (content: string) => {
  // 简单的Markdown渲染
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>');
};

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString();
};

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

// 加载历史消息
const loadMessages = async () => {
  if (!props.sessionId) return;

  try {
    const response = await testcaseReviewService.getChatMessages(props.sessionId);
    messages.value = response.results;
    await nextTick();
    scrollToBottom();
  } catch (error) {
    console.error('加载消息失败:', error);
  }
};

// 生命周期
onMounted(() => {
  // 加载用户偏好的AI模型
  const savedModel = localStorage.getItem('preferred_ai_model');
  if (savedModel) {
    selectedModel.value = savedModel;
  }

  // 加载历史消息
  loadMessages();

  // 添加欢迎消息
  if (messages.value.length === 0) {
    messages.value.push({
      id: 'welcome',
      role: 'assistant',
      content: `👋 您好！我是AI测试用例评审助手。

**快速开始：**
1. 如果您已上传测试用例文件，可以使用下方的快速评审按钮
2. 或者直接在输入框中描述您的评审需求
3. 我支持多轮对话，可以针对评审结果进行深入讨论

有什么我可以帮助您的吗？`,
      created_at: new Date().toISOString()
    });
  }
});

// 监听sessionId变化
watch(() => props.sessionId, () => {
  if (props.sessionId) {
    loadMessages();
  }
});
</script>

<style scoped>
.ai-review-chat {
  display: flex;
  flex-direction: column;
  height: 600px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-bg-1);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.message-user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-ai {
  align-self: flex-start;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-light-1);
  color: var(--color-primary);
  flex-shrink: 0;
}

.message-user .message-avatar {
  background: var(--color-success-light-1);
  color: var(--color-success);
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-text {
  background: var(--color-bg-2);
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.5;
  word-wrap: break-word;
}

.message-user .message-text {
  background: var(--color-primary);
  color: white;
}

.message-time {
  font-size: 12px;
  color: var(--color-text-3);
  margin-top: 4px;
  text-align: right;
}

.message-user .message-time {
  text-align: left;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: var(--color-bg-2);
  border-radius: 12px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-text-3);
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.quick-review-section {
  padding: 16px;
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-2);
}

.section-title {
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--color-text-1);
}

.quick-review-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.review-btn {
  border-radius: 20px;
  font-size: 12px;
  height: 32px;
  padding: 0 16px;
}

.review-btn.boundary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
}

.review-btn.ambiguity {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border: none;
  color: white;
}

.review-btn.completeness {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  border: none;
  color: white;
}

.review-btn.format {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  border: none;
  color: white;
}

.chat-input-container {
  padding: 16px;
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-1);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-wrapper .arco-textarea-wrapper {
  flex: 1;
}

.send-button {
  height: 40px;
  border-radius: 20px;
  padding: 0 20px;
}

.model-selector {
  position: absolute;
  top: 16px;
  right: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .message {
    max-width: 95%;
  }
  
  .quick-review-buttons {
    flex-direction: column;
  }
  
  .review-btn {
    width: 100%;
  }
}
</style>