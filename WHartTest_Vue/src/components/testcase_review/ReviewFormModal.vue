<template>
  <a-modal
    v-model:visible="visible"
    :title="isEdit ? '编辑评审' : '新建评审'"
    width="800px"
    @ok="handleSubmit"
    @cancel="handleCancel"
    :confirm-loading="loading"
  >
    <a-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      layout="vertical"
    >
      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="评审标题" field="title">
            <a-input
              v-model="formData.title"
              placeholder="请输入评审标题"
            />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="所属项目" field="project">
            <a-select
              v-model="formData.project"
              placeholder="选择项目"
              :disabled="isEdit"
            >
              <a-option
                v-for="project in projects"
                :key="project.id"
                :value="project.id"
              >
                {{ project.name }}
              </a-option>
            </a-select>
          </a-form-item>
        </a-col>
      </a-row>

      <a-form-item label="评审描述" field="description">
        <a-textarea
          v-model="formData.description"
          placeholder="请输入评审描述（可选）"
          :rows="3"
        />
      </a-form-item>

      <!-- 文件上传或文本输入 -->
      <a-form-item label="测试用例来源">
        <a-radio-group v-model="inputMode" @change="handleInputModeChange">
          <a-radio value="file">文件上传</a-radio>
          <a-radio value="text">文本输入</a-radio>
        </a-radio-group>
      </a-form-item>

      <a-form-item
        v-if="inputMode === 'file'"
        label="上传文件"
        field="original_file"
      >
        <a-upload
          ref="uploadRef"
          :file-list="fileList"
          :show-file-list="true"
          :auto-upload="false"
          :limit="1"
          accept=".txt,.xlsx,.xls,.xmind,.docx,.pdf"
          @change="handleFileChange"
        >
          <template #upload-button>
            <div class="upload-area">
              <icon-cloud-upload class="upload-icon" />
              <div class="upload-text">
                <div>点击上传文件</div>
                <div class="upload-tip">
                  支持 .txt, .xlsx, .xls, .xmind, .docx, .pdf 格式
                </div>
              </div>
            </div>
          </template>
        </a-upload>
      </a-form-item>

      <a-form-item
        v-if="inputMode === 'text'"
        label="测试用例内容"
        field="file_content"
      >
        <a-textarea
          v-model="formData.file_content"
          placeholder="请粘贴或输入测试用例内容"
          :rows="8"
        />
      </a-form-item>

      <!-- 评审配置 -->
      <a-divider>评审配置</a-divider>

      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="评审类型" field="review_type">
            <a-select
              v-model="formData.review_type"
              placeholder="选择评审类型"
              @change="handleReviewTypeChange"
            >
              <a-option value="completeness">完整性评审</a-option>
              <a-option value="boundary">边界值评审</a-option>
              <a-option value="ambiguity">二义性检查</a-option>
              <a-option value="logic">逻辑性评审</a-option>
              <a-option value="coverage">覆盖率评审</a-option>
              <a-option value="custom">自定义评审</a-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="AI模型" field="ai_model">
            <a-select
              v-model="formData.ai_model"
              placeholder="选择AI模型"
            >
              <a-option value="deepseek-chat">DeepSeek Chat</a-option>
              <a-option value="qwen-turbo">通义千问 Turbo</a-option>
              <a-option value="qwen-plus">通义千问 Plus</a-option>
              <a-option value="qwen-max">通义千问 Max</a-option>
              <a-option value="gpt-3.5-turbo">GPT-3.5 Turbo</a-option>
              <a-option value="gpt-4">GPT-4</a-option>
            </a-select>
          </a-form-item>
        </a-col>
      </a-row>

      <a-form-item
        v-if="formData.review_type === 'custom'"
        label="自定义提示词"
        field="custom_prompt"
      >
        <a-textarea
          v-model="formData.custom_prompt"
          placeholder="请输入自定义评审提示词，使用 {content} 作为测试用例内容的占位符"
          :rows="6"
        />
      </a-form-item>

      <!-- AI API配置 -->
      <a-divider>AI API配置</a-divider>

      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="API基础URL" field="api_base_url">
            <a-input
              v-model="formData.api_base_url"
              placeholder="例如: https://api.deepseek.com/v1"
            />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="API密钥" field="api_key">
            <a-input-password
              v-model="formData.api_key"
              placeholder="请输入API密钥"
            />
          </a-form-item>
        </a-col>
      </a-row>

      <!-- 预设配置快捷按钮 -->
      <a-form-item label="快捷配置">
        <a-space>
          <a-button size="small" @click="setDeepSeekConfig">
            DeepSeek配置
          </a-button>
          <a-button size="small" @click="setQianwenConfig">
            通义千问配置
          </a-button>
        </a-space>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import { Message } from '@arco-design/web-vue';
import { IconCloudUpload } from '@arco-design/web-vue/es/icon';
import { testcaseReviewService, type TestCaseReview, type CreateReviewData } from '@/services/testcaseReviewService';

interface Props {
  visible: boolean;
  review?: TestCaseReview | null;
  projects: any[];
}

interface Emits {
  (e: 'update:visible', visible: boolean): void;
  (e: 'success'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// 响应式数据
const loading = ref(false);
const formRef = ref();
const uploadRef = ref();
const inputMode = ref<'file' | 'text'>('file');
const fileList = ref<any[]>([]);

// 表单数据
const formData = reactive<CreateReviewData>({
  title: '',
  description: '',
  project: '',
  review_type: 'completeness',
  ai_model: 'deepseek-chat',
  api_base_url: '',
  api_key: '',
  file_content: '',
  custom_prompt: '',
});

// 表单验证规则
const rules = {
  title: [
    { required: true, message: '请输入评审标题' },
    { minLength: 2, message: '标题至少2个字符' },
  ],
  project: [
    { required: true, message: '请选择项目' },
  ],
  review_type: [
    { required: true, message: '请选择评审类型' },
  ],
  ai_model: [
    { required: true, message: '请选择AI模型' },
  ],
  api_base_url: [
    { required: true, message: '请输入API基础URL' },
  ],
  api_key: [
    { required: true, message: '请输入API密钥' },
  ],
  original_file: [
    {
      validator: (value: any, callback: any) => {
        if (inputMode.value === 'file' && fileList.value.length === 0 && !props.review?.original_file) {
          callback('请上传文件');
        } else {
          callback();
        }
      },
    },
  ],
  file_content: [
    {
      validator: (value: any, callback: any) => {
        if (inputMode.value === 'text' && !formData.file_content?.trim()) {
          callback('请输入测试用例内容');
        } else {
          callback();
        }
      },
    },
  ],
  custom_prompt: [
    {
      validator: (value: any, callback: any) => {
        if (formData.review_type === 'custom' && !formData.custom_prompt?.trim()) {
          callback('请输入自定义提示词');
        } else {
          callback();
        }
      },
    },
  ],
};

// 计算属性
const isEdit = computed(() => !!props.review?.id);

// 监听器
watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      resetForm();
      if (props.review) {
        loadReviewData();
      }
    }
  }
);

// 方法
const resetForm = () => {
  Object.assign(formData, {
    title: '',
    description: '',
    project: '',
    review_type: 'completeness',
    ai_model: 'deepseek-chat',
    api_base_url: '',
    api_key: '',
    file_content: '',
    custom_prompt: '',
  });
  fileList.value = [];
  inputMode.value = 'file';
  formRef.value?.clearValidate();
};

const loadReviewData = () => {
  if (!props.review) return;

  Object.assign(formData, {
    title: props.review.title,
    description: props.review.description || '',
    project: props.review.project,
    review_type: props.review.review_type,
    ai_model: props.review.ai_model,
    api_base_url: props.review.api_base_url || '',
    api_key: '', // 不回填密钥
    file_content: props.review.file_content || '',
    custom_prompt: props.review.custom_prompt || '',
  });

  // 设置输入模式
  if (props.review.file_content && !props.review.original_file) {
    inputMode.value = 'text';
  } else {
    inputMode.value = 'file';
  }

  // 如果有文件，显示文件信息
  if (props.review.original_file) {
    fileList.value = [{
      uid: '1',
      name: getFileName(props.review.original_file),
      status: 'done',
    }];
  }
};

const handleInputModeChange = () => {
  // 清除另一种模式的数据
  if (inputMode.value === 'file') {
    formData.file_content = '';
  } else {
    fileList.value = [];
    formData.original_file = undefined;
  }
  formRef.value?.clearValidate();
};

const handleFileChange = (fileList: any[], file: any) => {
  if (file.status === 'init') {
    formData.original_file = file.file;
    // 自动检测文件类型
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (extension) {
      formData.file_type = extension;
    }
  }
};

const handleReviewTypeChange = () => {
  if (formData.review_type !== 'custom') {
    formData.custom_prompt = '';
  }
};

const setDeepSeekConfig = () => {
  formData.api_base_url = 'https://api.deepseek.com/v1';
  formData.ai_model = 'deepseek-chat';
};

const setQianwenConfig = () => {
  formData.api_base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1';
  formData.ai_model = 'qwen-turbo';
};

const handleSubmit = async () => {
  try {
    const valid = await formRef.value?.validate();
    if (!valid) return;

    loading.value = true;

    const submitData = { ...formData };

    // 如果是文本模式，清除文件相关字段
    if (inputMode.value === 'text') {
      delete submitData.original_file;
      delete submitData.file_type;
    } else {
      // 文件模式，清除文本内容
      delete submitData.file_content;
    }

    if (isEdit.value && props.review) {
      await testcaseReviewService.updateReview(props.review.id, submitData);
      Message.success('评审更新成功');
    } else {
      await testcaseReviewService.createReview(submitData);
      Message.success('评审创建成功');
    }

    emit('success');
  } catch (error: any) {
    console.error('提交失败:', error);
    Message.error(error.response?.data?.message || '操作失败');
  } finally {
    loading.value = false;
  }
};

const handleCancel = () => {
  emit('update:visible', false);
};

// 工具函数
const getFileName = (filePath: string) => {
  if (!filePath) return '';
  return filePath.split('/').pop() || filePath;
};
</script>

<style scoped>
.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  border: 2px dashed #d9d9d9;
  border-radius: 6px;
  background-color: #fafafa;
  cursor: pointer;
  transition: border-color 0.3s;
}

.upload-area:hover {
  border-color: #165dff;
}

.upload-icon {
  font-size: 48px;
  color: #d9d9d9;
  margin-bottom: 16px;
}

.upload-text {
  text-align: center;
}

.upload-tip {
  font-size: 12px;
  color: #86909c;
  margin-top: 4px;
}
</style>