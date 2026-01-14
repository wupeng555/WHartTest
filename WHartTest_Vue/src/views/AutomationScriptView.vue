<template>
  <div class="automation-script-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <icon-robot class="title-icon" />
            自动化脚本管理
          </h1>
          <p class="page-description">基于AI的Midscene.js自动化测试脚本生成与执行</p>
        </div>
        <div class="header-actions">
          <a-button type="primary" @click="showCreateModal = true">
            <template #icon><icon-plus /></template>
            新建脚本
          </a-button>
          <a-button @click="showTemplateModal = true">
            <template #icon><icon-file-text /></template>
            脚本模板
          </a-button>
        </div>
      </div>
    </div>

    <!-- 筛选工具栏 -->
    <div class="filter-toolbar">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-select
            v-model="filters.project"
            placeholder="选择项目"
            allow-clear
            @change="handleFilterChange"
          >
            <a-option
              v-for="project in projects"
              :key="project.id"
              :value="project.id"
            >
              {{ project.name }}
            </a-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model="filters.script_type"
            placeholder="脚本类型"
            allow-clear
            @change="handleFilterChange"
          >
            <a-option value="web">Web自动化</a-option>
            <a-option value="android">Android自动化</a-option>
            <a-option value="ios">iOS自动化</a-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model="filters.status"
            placeholder="脚本状态"
            allow-clear
            @change="handleFilterChange"
          >
            <a-option value="draft">草稿</a-option>
            <a-option value="generated">已生成</a-option>
            <a-option value="ready">就绪</a-option>
            <a-option value="running">执行中</a-option>
            <a-option value="completed">已完成</a-option>
            <a-option value="failed">执行失败</a-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-input-search
            v-model="filters.search"
            placeholder="搜索脚本名称或描述"
            @search="handleFilterChange"
          />
        </a-col>
        <a-col :span="4">
          <a-button @click="resetFilters">重置</a-button>
        </a-col>
      </a-row>
    </div>

    <!-- 脚本列表 -->
    <div class="script-list">
      <a-table
        :columns="columns"
        :data-source="scripts"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="id"
      >
        <!-- 脚本类型列 -->
        <template #script_type="{ record }">
          <a-tag :color="getScriptTypeColor(record.script_type)">
            {{ record.script_type_display }}
          </a-tag>
        </template>

        <!-- 状态列 -->
        <template #status="{ record }">
          <a-tag :color="getStatusColor(record.status)">
            {{ record.status_display }}
          </a-tag>
        </template>

        <!-- 进度列 -->
        <template #progress="{ record }">
          <div class="progress-info">
            <div class="progress-text">
              {{ getProgressText(record) }}
            </div>
            <a-progress
              :percent="getProgressPercent(record)"
              :status="getProgressStatus(record)"
              size="small"
            />
          </div>
        </template>

        <!-- 操作列 -->
        <template #actions="{ record }">
          <a-space>
            <a-button
              type="text"
              size="small"
              @click="viewScript(record)"
            >
              查看
            </a-button>
            <a-button
              v-if="record.status === 'draft'"
              type="text"
              size="small"
              @click="generateYaml(record)"
              :loading="generatingScripts.includes(record.id)"
            >
              生成脚本
            </a-button>
            <a-button
              v-if="['generated', 'ready', 'completed'].includes(record.status)"
              type="text"
              size="small"
              @click="executeScript(record)"
              :loading="executingScripts.includes(record.id)"
            >
              执行
            </a-button>
            <a-dropdown>
              <a-button type="text" size="small">
                更多
                <icon-down />
              </a-button>
              <template #content>
                <a-doption @click="editScript(record)">编辑</a-doption>
                <a-doption
                  v-if="record.yaml_content"
                  @click="downloadYaml(record)"
                >
                  下载YAML
                </a-doption>
                <a-doption @click="viewExecutions(record)">执行记录</a-doption>
                <a-doption @click="duplicateScript(record)">复制</a-doption>
                <a-doption
                  class="danger-option"
                  @click="deleteScript(record)"
                >
                  删除
                </a-doption>
              </template>
            </a-dropdown>
          </a-space>
        </template>
      </a-table>
    </div>

    <!-- 创建/编辑脚本模态框 -->
    <ScriptFormModal
      v-model:visible="showCreateModal"
      :script="editingScript"
      :projects="projects"
      :templates="templates"
      @success="handleCreateSuccess"
    />

    <!-- 脚本详情模态框 -->
    <ScriptDetailModal
      v-model:visible="showDetailModal"
      :script="selectedScript"
      @refresh="loadScripts"
    />

    <!-- 执行记录模态框 -->
    <ExecutionListModal
      v-model:visible="showExecutionModal"
      :script="selectedScript"
    />

    <!-- 模板管理模态框 -->
    <TemplateManageModal
      v-model:visible="showTemplateModal"
      @template-selected="handleTemplateSelected"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { Message, Modal } from '@arco-design/web-vue';
import {
  IconRobot,
  IconPlus,
  IconFileText,
  IconDown
} from '@arco-design/web-vue/es/icon';
import { automationScriptService, type AutomationScript } from '@/services/automationScriptService';
import ScriptFormModal from '@/components/automation-script/ScriptFormModal.vue';
import ScriptDetailModal from '@/components/automation-script/ScriptDetailModal.vue';
import ExecutionListModal from '@/components/automation-script/ExecutionListModal.vue';
import TemplateManageModal from '@/components/automation-script/TemplateManageModal.vue';

// 响应式数据
const scripts = ref<AutomationScript[]>([]);
const projects = ref<any[]>([]);
const templates = ref<any[]>([]);
const loading = ref(false);
const generatingScripts = ref<string[]>([]);
const executingScripts = ref<string[]>([]);

// 模态框状态
const showCreateModal = ref(false);
const showDetailModal = ref(false);
const showExecutionModal = ref(false);
const showTemplateModal = ref(false);
const editingScript = ref<AutomationScript | null>(null);
const selectedScript = ref<AutomationScript | null>(null);

// 筛选条件
const filters = reactive({
  project: undefined,
  script_type: undefined,
  status: undefined,
  search: ''
});

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条记录`
});

// 表格列配置
const columns = [
  {
    title: '脚本名称',
    dataIndex: 'name',
    key: 'name',
    width: 200,
    ellipsis: true
  },
  {
    title: '脚本类型',
    dataIndex: 'script_type',
    key: 'script_type',
    width: 120,
    slots: { customRender: 'script_type' }
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100,
    slots: { customRender: 'status' }
  },
  {
    title: '进度',
    key: 'progress',
    width: 150,
    slots: { customRender: 'progress' }
  },
  {
    title: '项目',
    dataIndex: 'project_name',
    key: 'project_name',
    width: 120,
    ellipsis: true
  },
  {
    title: '创建者',
    dataIndex: 'creator_name',
    key: 'creator_name',
    width: 100
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 150,
    customRender: ({ text }: { text: string }) => {
      return new Date(text).toLocaleString();
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    slots: { customRender: 'actions' }
  }
];

// 方法
const loadScripts = async () => {
  loading.value = true;
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      ...filters
    };
    
    // 移除空值
    Object.keys(params).forEach(key => {
      if (params[key] === undefined || params[key] === '') {
        delete params[key];
      }
    });

    const response = await automationScriptService.getScripts(params);
    scripts.value = response.data.results || response.data;
    pagination.total = response.data.count || scripts.value.length;
  } catch (error: any) {
    console.error('加载脚本列表失败:', error);
    Message.error('加载脚本列表失败');
  } finally {
    loading.value = false;
  }
};

const handleFilterChange = () => {
  pagination.current = 1;
  loadScripts();
};

const resetFilters = () => {
  Object.keys(filters).forEach(key => {
    filters[key] = undefined;
  });
  handleFilterChange();
};

const handleTableChange = (paginationInfo: any) => {
  pagination.current = paginationInfo.current;
  pagination.pageSize = paginationInfo.pageSize;
  loadScripts();
};

const viewScript = (script: AutomationScript) => {
  selectedScript.value = script;
  showDetailModal.value = true;
};

const editScript = (script: AutomationScript) => {
  editingScript.value = script;
  showCreateModal.value = true;
};

const generateYaml = async (script: AutomationScript) => {
  generatingScripts.value.push(script.id);
  try {
    await automationScriptService.generateYaml(script.id);
    Message.success('YAML脚本生成成功');
    loadScripts();
  } catch (error: any) {
    console.error('生成YAML脚本失败:', error);
    Message.error(error.response?.data?.error || '生成YAML脚本失败');
  } finally {
    generatingScripts.value = generatingScripts.value.filter(id => id !== script.id);
  }
};

const executeScript = async (script: AutomationScript) => {
  executingScripts.value.push(script.id);
  try {
    await automationScriptService.executeScript(script.id);
    Message.success('脚本执行已开始，请查看执行记录');
    loadScripts();
  } catch (error: any) {
    console.error('执行脚本失败:', error);
    Message.error(error.response?.data?.error || '执行脚本失败');
  } finally {
    executingScripts.value = executingScripts.value.filter(id => id !== script.id);
  }
};

const downloadYaml = async (script: AutomationScript) => {
  try {
    const response = await automationScriptService.downloadYaml(script.id);
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.download = `${script.name}.yaml`;
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

const viewExecutions = (script: AutomationScript) => {
  selectedScript.value = script;
  showExecutionModal.value = true;
};

const duplicateScript = (script: AutomationScript) => {
  const duplicatedScript = {
    ...script,
    name: `${script.name} - 副本`,
    status: 'draft',
    yaml_content: '',
    generated_at: undefined
  };
  editingScript.value = duplicatedScript as AutomationScript;
  showCreateModal.value = true;
};

const deleteScript = (script: AutomationScript) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除脚本"${script.name}"吗？此操作不可恢复。`,
    onOk: async () => {
      try {
        await automationScriptService.deleteScript(script.id);
        Message.success('脚本删除成功');
        loadScripts();
      } catch (error: any) {
        console.error('删除脚本失败:', error);
        Message.error('删除脚本失败');
      }
    }
  });
};

const handleCreateSuccess = () => {
  showCreateModal.value = false;
  editingScript.value = null;
  loadScripts();
};

const handleTemplateSelected = (template: any) => {
  // 基于模板创建新脚本
  editingScript.value = {
    name: `基于${template.name}的脚本`,
    description: template.description,
    script_type: template.template_type === 'web_login' ? 'web' : 'web',
    test_cases_content: template.test_case_template || '',
    yaml_content: template.yaml_template
  } as AutomationScript;
  showTemplateModal.value = false;
  showCreateModal.value = true;
};

// 辅助方法
const getScriptTypeColor = (type: string) => {
  const colors = {
    web: 'blue',
    android: 'green',
    ios: 'orange'
  };
  return colors[type] || 'gray';
};

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

const getProgressText = (script: AutomationScript) => {
  const statusTexts = {
    draft: '待生成',
    generated: '已生成',
    ready: '就绪',
    running: '执行中',
    completed: '已完成',
    failed: '执行失败'
  };
  return statusTexts[script.status] || '未知';
};

const getProgressPercent = (script: AutomationScript) => {
  const percentMap = {
    draft: 20,
    generated: 60,
    ready: 80,
    running: 90,
    completed: 100,
    failed: 100
  };
  return percentMap[script.status] || 0;
};

const getProgressStatus = (script: AutomationScript) => {
  if (script.status === 'failed') return 'exception';
  if (script.status === 'completed') return 'success';
  if (script.status === 'running') return 'active';
  return 'normal';
};

// 生命周期
onMounted(() => {
  loadScripts();
  // 加载项目列表和模板列表
  // loadProjects();
  // loadTemplates();
});
</script>

<style scoped>
.automation-script-container {
  padding: 24px;
}

.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  color: white;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  font-size: 32px;
}

.page-description {
  font-size: 14px;
  opacity: 0.9;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filter-toolbar {
  background: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.script-list {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.progress-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.progress-text {
  font-size: 12px;
  color: var(--color-text-2);
}

.danger-option {
  color: var(--color-danger);
}

.danger-option:hover {
  background-color: var(--color-danger-light-1);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .header-actions {
    width: 100%;
    justify-content: center;
  }
  
  .filter-toolbar .arco-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .filter-toolbar .arco-col {
    width: 100% !important;
  }
}
</style>