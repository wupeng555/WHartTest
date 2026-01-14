<template>
  <div class="report-comparison">
    <!-- 对比选择器 -->
    <div class="comparison-selector">
      <a-form layout="inline">
        <a-form-item label="基准报告">
          <a-select 
            v-model="baseReportId" 
            placeholder="选择基准报告"
            style="width: 300px"
            @change="handleBaseReportChange"
          >
            <a-option 
              v-for="report in availableReports" 
              :key="report.id" 
              :value="report.id"
            >
              {{ report.script_name }} - {{ formatTime(report.start_time) }}
            </a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="对比报告">
          <a-select 
            v-model="compareReportId" 
            placeholder="选择对比报告"
            style="width: 300px"
            @change="handleCompareReportChange"
          >
            <a-option 
              v-for="report in availableReports" 
              :key="report.id" 
              :value="report.id"
            >
              {{ report.script_name }} - {{ formatTime(report.start_time) }}
            </a-option>
          </a-select>
        </a-form-item>
        <a-form-item>
          <a-button type="primary" @click="performComparison">
            <template #icon><icon-swap /></template>
            开始对比
          </a-button>
        </a-form-item>
      </a-form>
    </div>

    <!-- 对比结果 -->
    <div v-if="comparisonResult" class="comparison-result">
      <!-- 总体对比 -->
      <a-card title="总体对比" class="overview-comparison">
        <a-row :gutter="24">
          <a-col :span="12">
            <div class="report-summary">
              <h4>基准报告</h4>
              <div class="summary-stats">
                <a-statistic 
                  title="成功率" 
                  :value="getSuccessRate(comparisonResult.base_report)" 
                  suffix="%" 
                />
                <a-statistic 
                  title="执行时长" 
                  :value="formatDuration(comparisonResult.base_report.duration)" 
                />
                <a-statistic 
                  title="总步骤数" 
                  :value="comparisonResult.base_report.total_steps" 
                />
              </div>
            </div>
          </a-col>
          <a-col :span="12">
            <div class="report-summary">
              <h4>对比报告</h4>
              <div class="summary-stats">
                <a-statistic 
                  title="成功率" 
                  :value="getSuccessRate(comparisonResult.compare_report)" 
                  suffix="%" 
                  :value-style="getComparisonStyle('success_rate')"
                />
                <a-statistic 
                  title="执行时长" 
                  :value="formatDuration(comparisonResult.compare_report.duration)" 
                  :value-style="getComparisonStyle('duration')"
                />
                <a-statistic 
                  title="总步骤数" 
                  :value="comparisonResult.compare_report.total_steps" 
                  :value-style="getComparisonStyle('total_steps')"
                />
              </div>
            </div>
          </a-col>
        </a-row>

        <!-- 差异指标 -->
        <div class="difference-metrics">
          <h4>差异分析</h4>
          <a-row :gutter="16">
            <a-col :span="8">
              <a-card size="small">
                <a-statistic
                  title="成功率差异"
                  :value="comparisonResult.differences.success_rate_diff"
                  suffix="%"
                  :value-style="getDifferenceStyle(comparisonResult.differences.success_rate_diff)"
                >
                  <template #prefix>
                    <icon-arrow-up v-if="comparisonResult.differences.success_rate_diff > 0" />
                    <icon-arrow-down v-else-if="comparisonResult.differences.success_rate_diff < 0" />
                    <icon-minus v-else />
                  </template>
                </a-statistic>
              </a-card>
            </a-col>
            <a-col :span="8">
              <a-card size="small">
                <a-statistic
                  title="时长差异"
                  :value="Math.abs(comparisonResult.differences.duration_diff)"
                  suffix="秒"
                  :value-style="getDifferenceStyle(-comparisonResult.differences.duration_diff)"
                >
                  <template #prefix>
                    <icon-arrow-up v-if="comparisonResult.differences.duration_diff > 0" />
                    <icon-arrow-down v-else-if="comparisonResult.differences.duration_diff < 0" />
                    <icon-minus v-else />
                  </template>
                </a-statistic>
              </a-card>
            </a-col>
            <a-col :span="8">
              <a-card size="small">
                <a-statistic
                  title="步骤差异"
                  :value="Math.abs(comparisonResult.differences.steps_diff)"
                  :value-style="getDifferenceStyle(comparisonResult.differences.steps_diff)"
                >
                  <template #prefix>
                    <icon-arrow-up v-if="comparisonResult.differences.steps_diff > 0" />
                    <icon-arrow-down v-else-if="comparisonResult.differences.steps_diff < 0" />
                    <icon-minus v-else />
                  </template>
                </a-statistic>
              </a-card>
            </a-col>
          </a-row>
        </div>
      </a-card>

      <!-- 步骤详细对比 -->
      <a-card title="步骤详细对比" class="steps-comparison">
        <a-table
          :columns="stepColumns"
          :data="comparisonResult.step_comparison"
          :pagination="false"
          size="small"
        >
          <!-- 步骤名称 -->
          <template #step_name="{ record }">
            <div class="step-info">
              <div class="step-title">{{ record.step_name }}</div>
              <div class="step-desc">{{ record.description }}</div>
            </div>
          </template>

          <!-- 基准结果 -->
          <template #base_result="{ record }">
            <a-tag :color="record.base_status === 'success' ? 'green' : 'red'">
              {{ record.base_status === 'success' ? '成功' : '失败' }}
            </a-tag>
            <div class="step-time">{{ record.base_duration }}ms</div>
          </template>

          <!-- 对比结果 -->
          <template #compare_result="{ record }">
            <a-tag :color="record.compare_status === 'success' ? 'green' : 'red'">
              {{ record.compare_status === 'success' ? '成功' : '失败' }}
            </a-tag>
            <div class="step-time">{{ record.compare_duration }}ms</div>
          </template>

          <!-- 差异 -->
          <template #difference="{ record }">
            <div class="step-difference">
              <div v-if="record.status_changed" class="status-change">
                <a-tag 
                  :color="record.status_improved ? 'green' : 'red'"
                  size="small"
                >
                  {{ record.status_improved ? '改善' : '退化' }}
                </a-tag>
              </div>
              <div class="time-difference">
                <span 
                  :class="['time-diff', record.time_improved ? 'improved' : 'degraded']"
                >
                  {{ record.time_diff > 0 ? '+' : '' }}{{ record.time_diff }}ms
                </span>
              </div>
            </div>
          </template>
        </a-table>
      </a-card>

      <!-- 性能趋势图 -->
      <a-card title="性能趋势对比" class="performance-chart">
        <div ref="chartContainer" class="chart-container"></div>
      </a-card>

      <!-- 截图对比 -->
      <a-card v-if="comparisonResult.screenshot_comparison" title="截图对比" class="screenshot-comparison">
        <div class="screenshot-grid">
          <div 
            v-for="(comparison, index) in comparisonResult.screenshot_comparison" 
            :key="index"
            class="screenshot-pair"
          >
            <div class="screenshot-header">
              <h5>步骤 {{ comparison.step_number }}: {{ comparison.step_name }}</h5>
            </div>
            <div class="screenshot-images">
              <div class="screenshot-item">
                <div class="screenshot-label">基准报告</div>
                <img :src="comparison.base_screenshot" :alt="`基准-${comparison.step_name}`" />
              </div>
              <div class="screenshot-item">
                <div class="screenshot-label">对比报告</div>
                <img :src="comparison.compare_screenshot" :alt="`对比-${comparison.step_name}`" />
              </div>
            </div>
            <div v-if="comparison.difference_score" class="difference-score">
              <a-progress 
                :percent="comparison.difference_score" 
                :status="comparison.difference_score > 90 ? 'success' : 'exception'"
                size="small"
              />
              <span class="score-text">相似度: {{ comparison.difference_score }}%</span>
            </div>
          </div>
        </div>
      </a-card>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <a-spin size="large">
        <div class="loading-text">正在分析对比数据...</div>
      </a-spin>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue';
import { Message } from '@arco-design/web-vue';
import {
  IconSwap,
  IconArrowUp,
  IconArrowDown,
  IconMinus
} from '@arco-design/web-vue/es/icon';
import { automationScriptService } from '@/services/automationScriptService';
import * as echarts from 'echarts';

interface ComparisonResult {
  base_report: any;
  compare_report: any;
  differences: {
    success_rate_diff: number;
    duration_diff: number;
    steps_diff: number;
  };
  step_comparison: any[];
  screenshot_comparison?: any[];
}

const props = defineProps<{
  reports?: any[];
}>();

// 响应式数据
const loading = ref(false);
const availableReports = ref<any[]>([]);
const baseReportId = ref('');
const compareReportId = ref('');
const comparisonResult = ref<ComparisonResult | null>(null);
const chartContainer = ref<HTMLElement>();

// 表格列配置
const stepColumns = [
  {
    title: '步骤',
    dataIndex: 'step_number',
    width: 80
  },
  {
    title: '步骤名称',
    slotName: 'step_name',
    width: 200
  },
  {
    title: '基准结果',
    slotName: 'base_result',
    width: 120
  },
  {
    title: '对比结果',
    slotName: 'compare_result',
    width: 120
  },
  {
    title: '差异',
    slotName: 'difference',
    width: 150
  }
];

// 初始化
onMounted(() => {
  loadAvailableReports();
  if (props.reports && props.reports.length > 0) {
    baseReportId.value = props.reports[0].id;
  }
});

const loadAvailableReports = async () => {
  try {
    const response = await automationScriptService.getExecutionReports({
      page_size: 100,
      status: 'completed'
    });
    availableReports.value = response.data.results || response.data;
  } catch (error) {
    console.error('加载报告列表失败:', error);
  }
};

const handleBaseReportChange = (reportId: string) => {
  baseReportId.value = reportId;
  if (comparisonResult.value) {
    comparisonResult.value = null;
  }
};

const handleCompareReportChange = (reportId: string) => {
  compareReportId.value = reportId;
  if (comparisonResult.value) {
    comparisonResult.value = null;
  }
};

const performComparison = async () => {
  if (!baseReportId.value || !compareReportId.value) {
    Message.warning('请选择要对比的报告');
    return;
  }

  if (baseReportId.value === compareReportId.value) {
    Message.warning('请选择不同的报告进行对比');
    return;
  }

  loading.value = true;
  try {
    const response = await automationScriptService.compareReports({
      base_report_id: baseReportId.value,
      compare_report_id: compareReportId.value
    });
    
    comparisonResult.value = response.data;
    
    // 渲染性能图表
    nextTick(() => {
      renderPerformanceChart();
    });
    
    Message.success('报告对比完成');
  } catch (error) {
    console.error('报告对比失败:', error);
    Message.error('报告对比失败');
  } finally {
    loading.value = false;
  }
};

const renderPerformanceChart = () => {
  if (!chartContainer.value || !comparisonResult.value) return;

  const chart = echarts.init(chartContainer.value);
  
  const baseSteps = comparisonResult.value.step_comparison.map(step => step.base_duration);
  const compareSteps = comparisonResult.value.step_comparison.map(step => step.compare_duration);
  const stepNames = comparisonResult.value.step_comparison.map(step => `步骤${step.step_number}`);

  const option = {
    title: {
      text: '步骤执行时间对比',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['基准报告', '对比报告'],
      top: 30
    },
    xAxis: {
      type: 'category',
      data: stepNames,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '执行时间 (ms)'
    },
    series: [
      {
        name: '基准报告',
        type: 'line',
        data: baseSteps,
        itemStyle: {
          color: '#1890ff'
        }
      },
      {
        name: '对比报告',
        type: 'line',
        data: compareSteps,
        itemStyle: {
          color: '#52c41a'
        }
      }
    ]
  };

  chart.setOption(option);
  
  // 响应式调整
  window.addEventListener('resize', () => {
    chart.resize();
  });
};

// 工具函数
const getSuccessRate = (report: any) => {
  if (report.total_steps === 0) return 0;
  return Math.round((report.success_steps / report.total_steps) * 100);
};

const formatDuration = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return mins > 0 ? `${mins}分${secs}秒` : `${secs}秒`;
};

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString();
};

const getComparisonStyle = (metric: string) => {
  if (!comparisonResult.value) return {};
  
  const diff = comparisonResult.value.differences;
  let value = 0;
  
  switch (metric) {
    case 'success_rate':
      value = diff.success_rate_diff;
      break;
    case 'duration':
      value = -diff.duration_diff; // 时间越短越好
      break;
    case 'total_steps':
      value = diff.steps_diff;
      break;
  }
  
  if (value > 0) {
    return { color: '#52c41a' };
  } else if (value < 0) {
    return { color: '#ff4d4f' };
  }
  return {};
};

const getDifferenceStyle = (diff: number) => {
  if (diff > 0) {
    return { color: '#52c41a' };
  } else if (diff < 0) {
    return { color: '#ff4d4f' };
  }
  return { color: '#666' };
};
</script>

<style scoped>
.report-comparison {
  padding: 16px;
}

.comparison-selector {
  margin-bottom: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.comparison-result {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.overview-comparison .summary-stats {
  display: flex;
  gap: 24px;
  margin-top: 16px;
}

.difference-metrics {
  margin-top: 24px;
}

.difference-metrics h4 {
  margin: 0 0 16px 0;
}

.steps-comparison .step-info {
  line-height: 1.4;
}

.step-title {
  font-weight: 500;
}

.step-desc {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.step-time {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.step-difference {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.time-diff.improved {
  color: #52c41a;
}

.time-diff.degraded {
  color: #ff4d4f;
}

.performance-chart .chart-container {
  height: 400px;
  width: 100%;
}

.screenshot-comparison .screenshot-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.screenshot-pair {
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  padding: 16px;
}

.screenshot-header h5 {
  margin: 0 0 16px 0;
  color: #1890ff;
}

.screenshot-images {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 12px;
}

.screenshot-item {
  text-align: center;
}

.screenshot-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
}

.screenshot-item img {
  width: 100%;
  max-height: 200px;
  object-fit: contain;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
}

.difference-score {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-text {
  font-size: 12px;
  color: #666;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.loading-text {
  margin-top: 16px;
  color: #666;
}
</style>