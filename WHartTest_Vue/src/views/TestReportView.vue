<template>
  <div class="test-report-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1>测试报告</h1>
        <p>查看和分析自动化测试执行结果</p>
      </div>
      <div class="header-actions">
        <a-button @click="refreshReports">
          <template #icon><icon-refresh /></template>
          刷新
        </a-button>
        <a-button type="primary" @click="exportReports">
          <template #icon><icon-download /></template>
          导出报告
        </a-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="总执行次数"
              :value="stats.total_executions"
              :value-style="{ color: '#1890ff' }"
            >
              <template #prefix><icon-play-circle /></template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="成功率"
              :value="stats.success_rate"
              suffix="%"
              :value-style="{ color: '#52c41a' }"
            >
              <template #prefix><icon-check-circle /></template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="平均耗时"
              :value="stats.avg_duration"
              suffix="秒"
              :value-style="{ color: '#faad14' }"
            >
              <template #prefix><icon-clock-circle /></template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="今日执行"
              :value="stats.today_executions"
              :value-style="{ color: '#722ed1' }"
            >
              <template #prefix><icon-calendar /></template>
            </a-statistic>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 筛选和搜索 -->
    <div class="filters-section">
      <a-card>
        <a-form :model="filters" layout="inline">
          <a-form-item label="脚本名称">
            <a-input 
              v-model="filters.script_name" 
              placeholder="搜索脚本名称"
              allow-clear
              @change="handleFilterChange"
            />
          </a-form-item>
          <a-form-item label="执行状态">
            <a-select 
              v-model="filters.status" 
              placeholder="选择状态"
              allow-clear
              @change="handleFilterChange"
            >
              <a-option value="completed">已完成</a-option>
              <a-option value="failed">执行失败</a-option>
              <a-option value="stopped">已停止</a-option>
            </a-select>
          </a-form-item>
          <a-form-item label="执行时间">
            <a-range-picker 
              v-model="filters.date_range"
              @change="handleFilterChange"
            />
          </a-form-item>
          <a-form-item label="项目">
            <a-select 
              v-model="filters.project_id" 
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
          </a-form-item>
        </a-form>
      </a-card>
    </div>

    <!-- 报告列表 -->
    <div class="reports-section">
      <a-card>
        <template #title>
          <div class="section-title">
            <span>执行报告列表</span>
            <a-tag>{{ pagination.total }} 条记录</a-tag>
          </div>
        </template>

        <a-table
          :columns="columns"
          :data="reports"
          :loading="loading"
          :pagination="pagination"
          @page-change="handlePageChange"
          @page-size-change="handlePageSizeChange"
        >
          <!-- 脚本名称 -->
          <template #script_name="{ record }">
            <div class="script-info">
              <div class="script-name">{{ record.script_name }}</div>
              <div class="script-desc">{{ record.script_description }}</div>
            </div>
          </template>

          <!-- 执行状态 -->
          <template #status="{ record }">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>

          <!-- 执行结果 -->
          <template #result="{ record }">
            <div class="execution-result">
              <div class="result-stats">
                <span class="success">✓ {{ record.success_steps }}</span>
                <span class="failed">✗ {{ record.failed_steps }}</span>
                <span class="total">总计 {{ record.total_steps }}</span>
              </div>
              <a-progress 
                :percent="getSuccessRate(record)" 
                size="small"
                :status="record.status === 'completed' ? 'success' : 'exception'"
              />
            </div>
          </template>

          <!-- 执行时间 -->
          <template #duration="{ record }">
            <div class="duration-info">
              <div>{{ formatDuration(record.duration) }}</div>
              <div class="start-time">{{ formatTime(record.start_time) }}</div>
            </div>
          </template>

          <!-- 操作 -->
          <template #actions="{ record }">
            <a-space>
              <a-button 
                type="text" 
                size="small"
                @click="viewReport(record)"
              >
                <template #icon><icon-eye /></template>
                查看
              </a-button>
              <a-button 
                type="text" 
                size="small"
                @click="downloadReport(record)"
              >
                <template #icon><icon-download /></template>
                下载
              </a-button>
              <a-dropdown>
                <a-button type="text" size="small">
                  <template #icon><icon-more /></template>
                </a-button>
                <template #content>
                  <a-doption @click="rerunScript(record)">
                    <template #icon><icon-refresh /></template>
                    重新执行
                  </a-doption>
                  <a-doption @click="compareReport(record)">
                    <template #icon><icon-swap /></template>
                    对比报告
                  </a-doption>
                  <a-doption @click="shareReport(record)">
                    <template #icon><icon-share-alt /></template>
                    分享报告
                  </a-doption>
                </template>
              </a-dropdown>
            </a-space>
          </template>
        </a-table>
      </a-card>
    </div>

    <!-- 报告详情模态框 -->
    <a-modal
      v-model:visible="reportDetailVisible"
      title="测试报告详情"
      width="90%"
      :footer="false"
    >
      <ExecutionReportViewer
        v-if="selectedReport"
        :report="selectedReport"
        :execution-id="selectedReport.id"
      />
    </a-modal>

    <!-- 报告对比模态框 -->
    <a-modal
      v-model:visible="compareModalVisible"
      title="报告对比"
      width="95%"
      :footer="false"
    >
      <ReportComparison
        v-if="compareReports.length > 0"
        :reports="compareReports"
      />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { Message } from '@arco-design/web-vue';
import {
  IconRefresh,
  IconDownload,
  IconPlayCircle,
  IconCheckCircle,
  IconClockCircle,
  IconCalendar,
  IconEye,
  IconMore,
  IconSwap,
  IconShareAlt
} from '@arco-design/web-vue/es/icon';
import { automationScriptService } from '@/services/automationScriptService';
import ExecutionReportViewer from '@/components/automation-script/ExecutionReportViewer.vue';
import ReportComparison from '@/components/automation-script/ReportComparison.vue';

interface TestReport {
  id: string;
  script_name: string;
  script_description: string;
  status: 'completed' | 'failed' | 'stopped';
  success_steps: number;
  failed_steps: number;
  total_steps: number;
  duration: number;
  start_time: string;
  end_time: string;
  project_id: string;
  project_name: string;
}

interface Stats {
  total_executions: number;
  success_rate: number;
  avg_duration: number;
  today_executions: number;
}

// 响应式数据
const loading = ref(false);
const reports = ref<TestReport[]>([]);
const projects = ref<any[]>([]);
const stats = ref<Stats>({
  total_executions: 0,
  success_rate: 0,
  avg_duration: 0,
  today_executions: 0
});

const filters = reactive({
  script_name: '',
  status: '',
  date_range: [],
  project_id: ''
});

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条记录`
});

const reportDetailVisible = ref(false);
const compareModalVisible = ref(false);
const selectedReport = ref<TestReport | null>(null);
const compareReports = ref<TestReport[]>([]);

// 表格列配置
const columns = [
  {
    title: '脚本名称',
    dataIndex: 'script_name',
    slotName: 'script_name',
    width: 200
  },
  {
    title: '执行状态',
    dataIndex: 'status',
    slotName: 'status',
    width: 100
  },
  {
    title: '执行结果',
    slotName: 'result',
    width: 200
  },
  {
    title: '执行时间',
    slotName: 'duration',
    width: 150
  },
  {
    title: '项目',
    dataIndex: 'project_name',
    width: 120
  },
  {
    title: '操作',
    slotName: 'actions',
    width: 150,
    fixed: 'right'
  }
];

// 初始化
onMounted(() => {
  loadProjects();
  loadStats();
  loadReports();
});

const loadProjects = async () => {
  try {
    const response = await automationScriptService.getProjects();
    projects.value = response.data.results || response.data;
  } catch (error) {
    console.error('加载项目失败:', error);
  }
};

const loadStats = async () => {
  try {
    const response = await automationScriptService.getExecutionStats();
    stats.value = response.data;
  } catch (error) {
    console.error('加载统计数据失败:', error);
  }
};

const loadReports = async () => {
  loading.value = true;
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      ...filters,
      date_start: filters.date_range[0],
      date_end: filters.date_range[1]
    };

    const response = await automationScriptService.getExecutionReports(params);
    reports.value = response.data.results || response.data;
    pagination.total = response.data.count || 0;
  } catch (error) {
    console.error('加载报告失败:', error);
    Message.error('加载报告失败');
  } finally {
    loading.value = false;
  }
};

const refreshReports = () => {
  loadStats();
  loadReports();
};

const handleFilterChange = () => {
  pagination.current = 1;
  loadReports();
};

const handlePageChange = (page: number) => {
  pagination.current = page;
  loadReports();
};

const handlePageSizeChange = (pageSize: number) => {
  pagination.pageSize = pageSize;
  pagination.current = 1;
  loadReports();
};

const viewReport = (report: TestReport) => {
  selectedReport.value = report;
  reportDetailVisible.value = true;
};

const downloadReport = async (report: TestReport) => {
  try {
    const response = await automationScriptService.downloadExecutionReport(report.id);
    
    // 创建下载链接
    const blob = new Blob([response.data], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${report.script_name}_${report.id}.json`;
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

const exportReports = async () => {
  try {
    const params = { ...filters };
    const response = await automationScriptService.exportExecutionReports(params);
    
    // 创建下载链接
    const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `test_reports_${new Date().toISOString().split('T')[0]}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    Message.success('报告导出成功');
  } catch (error) {
    console.error('导出报告失败:', error);
    Message.error('导出报告失败');
  }
};

const rerunScript = async (report: TestReport) => {
  try {
    await automationScriptService.rerunScript(report.id);
    Message.success('脚本重新执行已启动');
    refreshReports();
  } catch (error) {
    console.error('重新执行失败:', error);
    Message.error('重新执行失败');
  }
};

const compareReport = (report: TestReport) => {
  compareReports.value = [report];
  compareModalVisible.value = true;
};

const shareReport = async (report: TestReport) => {
  try {
    const response = await automationScriptService.shareReport(report.id);
    const shareUrl = response.data.share_url;
    
    // 复制到剪贴板
    await navigator.clipboard.writeText(shareUrl);
    Message.success('分享链接已复制到剪贴板');
  } catch (error) {
    console.error('分享报告失败:', error);
    Message.error('分享报告失败');
  }
};

// 工具函数
const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed': return 'green';
    case 'failed': return 'red';
    case 'stopped': return 'orange';
    default: return 'gray';
  }
};

const getStatusText = (status: string) => {
  switch (status) {
    case 'completed': return '已完成';
    case 'failed': return '执行失败';
    case 'stopped': return '已停止';
    default: return '未知';
  }
};

const getSuccessRate = (record: TestReport) => {
  if (record.total_steps === 0) return 0;
  return Math.round((record.success_steps / record.total_steps) * 100);
};

const formatDuration = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return mins > 0 ? `${mins}分${secs}秒` : `${secs}秒`;
};

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString();
};
</script>

<style scoped>
.test-report-view {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-content h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.header-content p {
  margin: 0;
  color: #666;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-cards {
  margin-bottom: 24px;
}

.filters-section {
  margin-bottom: 24px;
}

.reports-section {
  margin-bottom: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.script-info {
  line-height: 1.4;
}

.script-name {
  font-weight: 500;
  color: #1890ff;
}

.script-desc {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.execution-result {
  line-height: 1.4;
}

.result-stats {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
}

.result-stats .success {
  color: #52c41a;
}

.result-stats .failed {
  color: #ff4d4f;
}

.result-stats .total {
  color: #666;
}

.duration-info {
  line-height: 1.4;
}

.start-time {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}
</style>