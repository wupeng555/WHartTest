<template>
  <a-modal
    v-model:visible="visible"
    :title="isEdit ? '编辑脚本' : '新建脚本'"
    width="800px"
    @ok="handleSubmit"
    @cancel="handleCancel"
    :confirm-loading="submitting"
  >
    <a-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      layout="vertical"
      @submit="handleSubmit"
    >
      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="脚本名称" field="name">
            <a-input
              v-model="formData.name"
              placeholder="请输入脚本名称"
              :max-length="200"
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

      <a-form-item label="脚本描述" field="description">
        <a-textarea
          v-model="formData.description"
          placeholder="请输入脚本描述（可选）"
          :rows="3"
          :max-length="500"
        />
      </a-form-item>

      <a-row :gutter="16">
        <a-col :span="8">
          <a-form-item label="脚本类型" field="script_type">
            <a-select
              v-model="formData.script_type"
              placeholder="选择脚本类型"
              @change="handleScriptTypeChange"
            >
              <a-option value="web">🌐 Web自动化</a-option>
              <a-option value="android">📱 Android自动化</a-option>
              <a-option value="ios">📱 iOS自动化</a-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="AI模型" field="ai_model">
            <a-select
              v-model="formData.ai_model"
              placeholder="选择AI模型"
            >
              <a-option value="qwen-turbo">通义千问-Turbo</a-option>
              <a-option value="qwen-plus">通义千问-Plus</a-option>
              <a-option value="qwen-max">通义千问-Max</a-option>
              <a-option value="deepseek-chat">DeepSeek-Chat</a-option>
              <a-option value="gpt-4">GPT-4</a-option>
              <a-option value="gpt-3.5-turbo">GPT-3.5-Turbo</a-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item 
            v-if="formData.script_type === 'web'" 
            label="目标URL" 
            field="target_url"
          >
            <a-input
              v-model="formData.target_url"
              placeholder="https://example.com"
            />
          </a-form-item>
        </a-col>
      </a-row>

      <!-- Web配置 -->
      <div v-if="formData.script_type === 'web'" class="config-section">
        <h4>Web配置</h4>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="视口宽度" field="viewport_width">
              <a-input-number
                v-model="formData.viewport_width"
                :min="800"
                :max="2560"
                placeholder="1280"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="视口高度" field="viewport_height">
              <a-input-number
                v-model="formData.viewport_height"
                :min="600"
                :max="1440"
                placeholder="960"
              />
            </a-form-item>
          </a-col>
        </a-row>
      </div>

      <!-- AI配置 -->
      <div class="config-section">
        <h4>AI配置</h4>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="API密钥" field="api_key">
              <a-input-password
                v-model="formData.api_key"
                placeholder="请输入API密钥"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="API端点" field="api_endpoint">
              <a-input
                v-model="formData.api_endpoint"
                placeholder="https://dashscope.aliyuncs.com"
              />
            </a-form-item>
          </a-col>
        </a-row>
      </div>

      <!-- 执行配置 -->
      <div class="config-section">
        <h4>执行配置</h4>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="执行超时(秒)" field="execution_timeout">
              <a-input-number
                v-model="formData.execution_timeout"
                :min="60"
                :max="3600"
                placeholder="300"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="重试次数" field="retry_count">
              <a-input-number
                v-model="formData.retry_count"
                :min="1"
                :max="5"
                placeholder="1"
              />
            </a-form-item>
          </a-col>
        </a-row>
      </div>

      <!-- 测试用例内容 -->
      <a-form-item label="测试用例内容" field="test_cases_content">
        <div class="test-cases-section">
          <div class="section-header">
            <span>测试用例</span>
            <div class="header-actions">
              <a-button
                size="small"
                @click="showTemplateSelector = true"
              >
                📋 选择模板
              </a-button>
              <a-button
                size="small"
                @click="showExampleModal = true"
              >
                💡 查看示例
              </a-button>
            </div>
          </div>
          <a-textarea
            v-model="formData.test_cases_content"
            placeholder="请输入测试用例内容，支持自然语言描述..."
            :rows="10"
            :max-length="10000"
          />
          <div class="input-tip">
            💡 提示：可以使用自然语言描述测试步骤，AI会自动转换为Midscene.js YAML脚本
          </div>
        </div>
      </a-form-item>
    </a-form>

    <!-- 模板选择器 -->
    <a-modal
      v-model:visible="showTemplateSelector"
      title="选择脚本模板"
      width="600px"
      :footer="false"
    >
      <div class="template-list">
        <div
          v-for="template in templates"
          :key="template.id"
          class="template-item"
          @click="selectTemplate(template)"
        >
          <div class="template-header">
            <h4>{{ template.name }}</h4>
            <a-tag>{{ template.template_type_display }}</a-tag>
          </div>
          <p class="template-description">{{ template.description }}</p>
        </div>
      </div>
    </a-modal>

    <!-- 示例模态框 -->
    <a-modal
      v-model:visible="showExampleModal"
      title="测试用例示例"
      width="700px"
      :footer="false"
    >
      <div class="example-content">
        <a-tabs>
          <a-tab-pane key="web" title="Web示例">
            <pre class="example-code">{{ webExample }}</pre>
          </a-tab-pane>
          <a-tab-pane key="android" title="Android示例">
            <pre class="example-code">{{ androidExample }}</pre>
          </a-tab-pane>
          <a-tab-pane key="ios" title="iOS示例">
            <pre class="example-code">{{ iosExample }}</pre>
          </a-tab-pane>
        </a-tabs>
      </div>
    </a-modal>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue';
import { Message } from '@arco-design/web-vue';
import { automationScriptService, type AutomationScript, type CreateScriptData } from '@/services/automationScriptService';

interface Props {
  visible: boolean;
  script?: AutomationScript | null;
  projects: any[];
  templates: any[];
}

const props = defineProps<Props>();
const emit = defineEmits<{
  'update:visible': [value: boolean];
  success: [];
}>();

// 响应式数据
const formRef = ref();
const submitting = ref(false);
const showTemplateSelector = ref(false);
const showExampleModal = ref(false);

const formData = reactive<CreateScriptData>({
  name: '',
  description: '',
  script_type: 'web',
  test_cases_content: '',
  target_url: '',
  viewport_width: 1280,
  viewport_height: 960,
  ai_model: 'qwen-turbo',
  api_key: '',
  api_endpoint: 'https://dashscope.aliyuncs.com',
  execution_timeout: 300,
  retry_count: 1,
  project: ''
});

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入脚本名称' },
    { minLength: 2, message: '脚本名称至少2个字符' }
  ],
  project: [
    { required: true, message: '请选择项目' }
  ],
  script_type: [
    { required: true, message: '请选择脚本类型' }
  ],
  test_cases_content: [
    { required: true, message: '请输入测试用例内容' },
    { minLength: 10, message: '测试用例内容至少10个字符' }
  ],
  target_url: [
    { 
      validator: (value: string, callback: Function) => {
        if (formData.script_type === 'web' && !value) {
          callback('Web脚本需要输入目标URL');
        } else if (value && !/^https?:\/\/.+/.test(value)) {
          callback('请输入有效的URL');
        } else {
          callback();
        }
      }
    }
  ],
  api_key: [
    { required: true, message: '请输入API密钥' }
  ],
  api_endpoint: [
    { required: true, message: '请输入API端点' }
  ]
};

// 计算属性
const isEdit = computed(() => !!props.script?.id);

// 示例内容
const webExample = `测试用例：用户登录流程

测试步骤：
1. 打开登录页面
2. 在用户名输入框输入 "test@example.com"
3. 在密码输入框输入 "password123"
4. 点击登录按钮
5. 验证页面跳转到首页
6. 验证页面显示用户名

预期结果：
- 登录成功后跳转到首页
- 页面显示正确的用户信息`;

const androidExample = `测试用例：Android应用登录

测试步骤：
1. 启动应用
2. 点击登录按钮
3. 输入用户名 "testuser"
4. 输入密码 "123456"
5. 点击确认登录
6. 验证进入主界面

预期结果：
- 登录成功进入主界面
- 显示用户头像和昵称`;

const iosExample = `测试用例：iOS应用注册流程

测试步骤：
1. 打开注册页面
2. 输入手机号 "13800138000"
3. 点击获取验证码
4. 输入验证码 "123456"
5. 设置密码 "password123"
6. 点击注册按钮
7. 验证注册成功

预期结果：
- 注册成功并自动登录
- 跳转到完善资料页面`;

// 方法
const handleSubmit = async () => {
  try {
    const valid = await formRef.value?.validate();
    if (!valid) return;

    submitting.value = true;

    if (isEdit.value) {
      await automationScriptService.updateScript(props.script!.id, formData);
      Message.success('脚本更新成功');
    } else {
      await automationScriptService.createScript(formData);
      Message.success('脚本创建成功');
    }

    emit('success');
  } catch (error: any) {
    console.error('保存脚本失败:', error);
    Message.error(error.response?.data?.error || '保存脚本失败');
  } finally {
    submitting.value = false;
  }
};

const handleCancel = () => {
  emit('update:visible', false);
  resetForm();
};

const handleScriptTypeChange = (type: string) => {
  // 根据脚本类型设置默认配置
  if (type === 'web') {
    formData.target_url = '';
    formData.viewport_width = 1280;
    formData.viewport_height = 960;
  }
};

const selectTemplate = (template: any) => {
  formData.test_cases_content = template.test_case_template || '';
  formData.script_type = template.template_type.includes('web') ? 'web' : 
                         template.template_type.includes('android') ? 'android' : 'ios';
  showTemplateSelector.value = false;
  Message.success('模板应用成功');
};

const resetForm = () => {
  Object.assign(formData, {
    name: '',
    description: '',
    script_type: 'web',
    test_cases_content: '',
    target_url: '',
    viewport_width: 1280,
    viewport_height: 960,
    ai_model: 'qwen-turbo',
    api_key: '',
    api_endpoint: 'https://dashscope.aliyuncs.com',
    execution_timeout: 300,
    retry_count: 1,
    project: ''
  });
  formRef.value?.clearValidate();
};

// 监听器
watch(() => props.visible, (visible) => {
  if (visible && props.script) {
    // 编辑模式，填充表单数据
    Object.assign(formData, {
      name: props.script.name,
      description: props.script.description || '',
      script_type: props.script.script_type,
      test_cases_content: props.script.test_cases_content,
      target_url: props.script.target_url || '',
      viewport_width: props.script.viewport_width,
      viewport_height: props.script.viewport_height,
      ai_model: props.script.ai_model,
      api_key: props.script.api_key || '',
      api_endpoint: props.script.api_endpoint || 'https://dashscope.aliyuncs.com',
      execution_timeout: props.script.execution_timeout,
      retry_count: props.script.retry_count,
      project: props.script.project
    });
  } else if (visible) {
    resetForm();
  }
});

watch(() => props.visible, (visible) => {
  if (!visible) {
    showTemplateSelector.value = false;
    showExampleModal.value = false;
  }
});
</script>

<style scoped>
.config-section {
  margin: 24px 0;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.config-section h4 {
  margin: 0 0 16px 0;
  color: #1d2129;
  font-weight: 600;
}

.test-cases-section {
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f7f8fa;
  border-bottom: 1px solid #e5e6eb;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.test-cases-section .arco-textarea-wrapper {
  border: none;
  border-radius: 0;
}

.input-tip {
  padding: 8px 16px;
  background: #f0f9ff;
  color: #0969da;
  font-size: 12px;
  border-top: 1px solid #e5e6eb;
}

.template-list {
  max-height: 400px;
  overflow-y: auto;
}

.template-item {
  padding: 16px;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.template-item:hover {
  border-color: #165dff;
  background: #f0f5ff;
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.template-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.template-description {
  margin: 0;
  color: #86909c;
  font-size: 12px;
}

.example-content {
  max-height: 500px;
  overflow-y: auto;
}

.example-code {
  background: #f7f8fa;
  padding: 16px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>