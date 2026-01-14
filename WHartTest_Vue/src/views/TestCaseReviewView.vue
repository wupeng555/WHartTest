<template>
  <div class="testcase-review-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <icon-robot class="title-icon" />
            AI测试用例评审
          </h1>
          <p class="page-description">智能测试用例质量评审与改进建议</p>
        </div>
        <div class="header-actions">
          <a-button type="primary" @click="showCreateModal = true">
            <template #icon><icon-plus /></template>
            新建评审
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
            v-model="filters.status"
            placeholder="评审状态"
            allow-clear
            @change="handleFilterChange"
          >
            <a-option value="pending">待评审</a-option>
            <a-option value="reviewing">评审中</a-option>
            <a-option value="completed">已完成</a-option>
            <a-option value="failed">评审失败</a-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model="filters.review_type"
            placeholder="评审类型"
            allow-clear
            @change="handleFilterChange"
          >
            <a-option value="completeness">完整性评审</a-option>
            <a-option value="boundary">边界值评审</a-option>
            <a-option value="ambiguity">二义性检查</a-option>
            <a-option value="logic">逻辑性评审</a-option>
            <a-option value="coverage">覆盖率评审</a-option>
            <a-option value="custom">自定义评审</a-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-input-search
            v-model="filters.search"
            placeholder="搜索评审标题或描述"
            @search="handleFilterChange"
          />
        </a-col>
        <a-col :span="4">
          <a-button @click="resetFilters">重置</a-button>
        </a-col>
      </a-row>
    </div>

    <!-- 评审列表 -->
    <div class="review-list">
      <a-table
        :columns="columns"
        :data-source="reviews"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="id"
      >
        <!-- 状态列 -->
        <template #status="{ record }">
          <a-tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </a-tag>
        </template>

        <!-- 评审类型列 -->
        <template #review_type="{ record }">
          <a-tag>{{ getReviewTypeText(record.review_type) }}</a-tag>
        </template>

        <!-- 评分列 -->
        <template #review_score="{ record }">
          <div v-if="record.review_score !== null">
            <a-rate
              :model-value="record.review_score / 2"
              :count="5"
              :allow-half="true"
              disabled
            />
            <span class="score-text">{{ record.review_score }}/10</span>
          </div>
          <span v-else class="no-score">-</span>
        </template>

        <!-- 文件信息列 -->
        <template #file_info="{ record }">
          <div v-if="record.original_file">
            <div class="file-name">
              <icon-file class="file-icon" />
              {{ getFileName(record.original_file) }}
            </div>
            <div class="file-meta">
              {{ record.file_type?.toUpperCase() }} • {{ formatFileSize(record.file_size) }}
            </div>
          </div>
          <span v-else class="no-file">无文件</span>
        </template>

        <!-- 操作列 -->
        <template #actions="{ record }">
          <a-space>
            <a-button
              type="text"
              size="small"
              @click="viewReview(record)"
            >
              查看
            </a-button>
            <a-button
              v-if="record.status === 'pending'"
              type="text"
              size="small"
              @click="startReview(record)"
              :loading="startingReviews.includes(record.id)"
            >
              开始评审
            </a-button>
            <a-dropdown>
              <a-button type="text" size="small">
                更多
                <icon-down />
              </a-button>
              <template #content>
                <a-doption @click="editReview(record)">编辑</a-doption>
                <a-doption
                  v-if="record.original_file"
                  @click="downloadFile(record)"
                >
                  下载文件
                </a-doption>
                <a-doption @click="duplicateReview(record)">复制</a-doption>
                <a-doption
                  class="danger-option"
                  @click="deleteReview(record)"
                >
                  删除
                </a-doption>
              </template>
            </a-dropdown>
          </a-space>
        </template>
      </a-table>
    </div>

    <!-- 创建/编辑评审模态框 -->
    <ReviewFormModal
      v-model:visible="showCreateModal"
      :review="editingReview"
      :projects="projects"
      @success="handleCreateSuccess"
    />

    <!-- 评审详情模态框 -->
    <ReviewDetailModal
      v-model:visible="showDetailModal"
      :review="selectedReview"
      @refresh="loadReviews"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { Message, Modal } from '@arco-design/web-vue';
import {
  IconRobot,
  IconPlus,
  IconFile,
  IconDown,
} from '@arco-design/web-vue/es/icon';
import { testcaseReviewService, type TestCaseReview } from '@/services/testcaseReviewService';
import { projectService } from '@/services/projectService';
import ReviewFormModal from '@/components/testcase-review/ReviewFormModal.vue';
import ReviewDetailModal from '@/components/testcase-review/ReviewDetailModal.vue';

// 响应式数据
const loading = ref(false);
const reviews = ref<TestCaseReview[]>([]);
const projects = ref<any[]>([]);
const showCreateModal = ref(false);
const showDetailModal = ref(false);
const editingReview = ref<TestCaseReview | null>(null);
const selectedReview = ref<TestCaseReview | null>(null);
const startingReviews = ref<string[]>([]);

// 筛选条件
const filters = reactive({
  project: undefined,
  status: undefined,
  review_type: undefined,
  search: '',
});

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条记录`,
});

// 表格列配置
const columns = [
  {
    title: '评审标题',
    dataIndex: 'title',
    width: 200,
    ellipsis: true,
  },
  {
    title: '项目',
    dataIndex: 'project_name',
    width: 120,
  },
  {
    title: '状态',
    dataIndex: 'status',
    width: 100,
    slotName: 'status',
  },
  {
    title: '评审类型',
    dataIndex: 'review_type',
    width: 120,
    slotName: 'review_type',
  },
  {
    title: '文件信息',
    dataIndex: 'file_info',
    width: 200,
    slotName: 'file_info',
  },
  {
    title: '评分',
    dataIndex: 'review_score',
    width: 150,
    slotName: 'review_score',
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    width: 150,
    render: ({ record }: { record: TestCaseReview }) => {
      return new Date(record.created_at).toLocaleString();
    },
  },
  {
    title: '操作',
    width: 150,
    slotName: 'actions',
  },
];

// 生命周期
onMounted(() => {
  loadProjects();
  loadReviews();
});

// 方法
const loadProjects = async () => {
  try {
    const response = await projectService.getProjects();
    projects.value = response.data.results || response.data;
  } catch (error) {
    console.error('加载项目列表失败:', error);
  }
};

const loadReviews = async () => {
  loading.value = true;
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      ...filters,
    };

    // 移除空值
    Object.keys(params).forEach(key => {
      if (params[key] === undefined || params[key] === '') {
        delete params[key];
      }
    });

    const response = await testcaseReviewService.getReviews(params);
    const data = response.data;

    reviews.value = data.results || data;
    pagination.total = data.count || data.length;
  } catch (error) {
    console.error('加载评审列表失败:', error);
    Message.error('加载评审列表失败');
  } finally {
    loading.value = false;
  }
};

const handleFilterChange = () => {
  pagination.current = 1;
  loadReviews();
};

const resetFilters = () => {
  Object.keys(filters).forEach(key => {
    filters[key] = key === 'search' ? '' : undefined;
  });
  handleFilterChange();
};

const handleTableChange = (paginationInfo: any) => {
  pagination.current = paginationInfo.current;
  pagination.pageSize = paginationInfo.pageSize;
  loadReviews();
};

const viewReview = (review: TestCaseReview) => {
  selectedReview.value = review;
  showDetailModal.value = true;
};

const editReview = (review: TestCaseReview) => {
  editingReview.value = review;
  showCreateModal.value = true;
};

const startReview = async (review: TestCaseReview) => {
  if (!review.api_key || !review.api_base_url) {
    Message.warning('请先配置AI API信息');
    editReview(review);
    return;
  }

  startingReviews.value.push(review.id);
  try {
    await testcaseReviewService.startReview(review.id);
    Message.success('评审已开始，请稍后查看结果');
    loadReviews();
  } catch (error: any) {
    console.error('开始评审失败:', error);
    Message.error(error.response?.data?.error || '开始评审失败');
  } finally {
    startingReviews.value = startingReviews.value.filter(id => id !== review.id);
  }
};

const downloadFile = async (review: TestCaseReview) => {
  try {
    const response = await testcaseReviewService.downloadFile(review.id);
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.download = getFileName(review.original_file || '');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('文件下载失败:', error);
    Message.error('文件下载失败');
  }
};

const duplicateReview = (review: TestCaseReview) => {
  const duplicated = {
    ...review,
    title: `${review.title} - 副本`,
    id: undefined,
    status: 'pending',
    review_result: undefined,
    error_message: undefined,
    review_score: undefined,
    processing_time: undefined,
    completed_at: undefined,
  };
  editingReview.value = duplicated as TestCaseReview;
  showCreateModal.value = true;
};

const deleteReview = (review: TestCaseReview) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除评审"${review.title}"吗？此操作不可恢复。`,
    onOk: async () => {
      try {
        await testcaseReviewService.deleteReview(review.id);
        Message.success('删除成功');
        loadReviews();
      } catch (error) {
        console.error('删除失败:', error);
        Message.error('删除失败');
      }
    },
  });
};

const handleCreateSuccess = () => {
  showCreateModal.value = false;
  editingReview.value = null;
  loadReviews();
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
</script>

<style scoped>
.testcase-review-container {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  background: white;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #1d2129;
}

.title-icon {
  font-size: 28px;
  color: #165dff;
}

.page-description {
  margin: 0;
  color: #86909c;
  font-size: 14px;
}

.filter-toolbar {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.review-list {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.file-name {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
  margin-bottom: 4px;
}

.file-icon {
  color: #86909c;
}

.file-meta {
  font-size: 12px;
  color: #86909c;
}

.no-file,
.no-score {
  color: #c9cdd4;
  font-style: italic;
}

.score-text {
  margin-left: 8px;
  font-weight: 500;
  color: #1d2129;
}

.danger-option {
  color: #f53f3f !important;
}

.danger-option:hover {
  background-color: #ffece8 !important;
}
</style>