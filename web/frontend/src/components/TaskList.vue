<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>任务列表</span>
          <el-button @click="loadTasks">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-table :data="tasks" style="width: 100%" v-loading="loading">
        <el-table-column prop="task_id" label="任务ID" width="280">
          <template #default="{ row }">
            <el-tooltip :content="row.task_id" placement="top">
              <span>{{ row.task_id.substring(0, 8) }}...</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="task_type" label="任务类型" width="140">
          <template #default="{ row }">
            <el-tag :type="getTaskTypeColor(row.task_type)">
              {{ getTaskTypeText(row.task_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusColor(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="180">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :status="getProgressStatus(row.status)" />
          </template>
        </el-table-column>
        <el-table-column prop="message" label="消息" min-width="200" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
            <el-button size="small" type="danger" @click="deleteTask(row)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 任务详情对话框 -->
    <el-dialog v-model="detailVisible" title="任务详情" width="85%" top="3vh">
      <el-descriptions :column="3" border v-if="currentTask">
        <el-descriptions-item label="任务ID">{{ currentTask.task_id }}</el-descriptions-item>
        <el-descriptions-item label="任务类型">
          <el-tag :type="getTaskTypeColor(currentTask.task_type)">
            {{ getTaskTypeText(currentTask.task_type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusColor(currentTask.status)">{{ getStatusText(currentTask.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="进度">{{ currentTask.progress }}%</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(currentTask.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="消息" :span="3">{{ currentTask.message }}</el-descriptions-item>
      </el-descriptions>
      
      <!-- 验证结果展示 -->
      <div v-if="currentTask && currentTask.result && currentTask.status === 'completed'" style="margin-top: 20px;">
        <el-row :gutter="20">
          <!-- 结果图片 -->
          <el-col :span="12" v-if="parsedResult && parsedResult.result_image">
            <el-card>
              <template #header>
                <span><el-icon><Picture /></el-icon> 检测结果预览</span>
              </template>
              <el-image
                :src="parsedResult.result_image"
                fit="contain"
                style="width: 100%; height: 500px;"
                :preview-src-list="[parsedResult.result_image]"
              >
                <template #error>
                  <div style="text-align: center; padding: 50px; color: #909399;">
                    <el-icon size="50"><Picture /></el-icon>
                    <p>图片加载失败</p>
                  </div>
                </template>
              </el-image>
            </el-card>
          </el-col>
          
          <!-- 性能指标 -->
          <el-col :span="(parsedResult && parsedResult.result_image) ? 12 : 24">
            <el-card v-if="parsedResult && hasValidationData">
              <template #header>
                <span><el-icon><DataLine /></el-icon> 性能指标</span>
              </template>
              
              <el-descriptions :column="2" border>
                <el-descriptions-item label="模型" v-if="parsedResult.model">
                  <el-tag>{{ parsedResult.model }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="测试图片" v-if="parsedResult.image">
                  <el-tag type="info">{{ parsedResult.image }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="检测数量" v-if="parsedResult.count !== undefined">
                  <el-tag type="success" size="large" effect="dark">
                    <el-icon><Check /></el-icon> {{ parsedResult.count }} 个目标
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="推理时间" v-if="parsedResult.inference_time_ms">
                  <el-tag type="warning" size="large">{{ parsedResult.inference_time_ms }} ms</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="FPS" v-if="parsedResult.fps">
                  <el-tag type="primary" size="large">{{ parsedResult.fps }} FPS</el-tag>
                </el-descriptions-item>
              </el-descriptions>
              
              <!-- 类别统计 -->
              <div v-if="parsedResult.class_count && Object.keys(parsedResult.class_count).length > 0" style="margin-top: 20px;">
                <h4 style="margin-bottom: 10px;">
                  <el-icon><Collection /></el-icon> 类别统计:
                </h4>
                <el-space wrap>
                  <el-tag 
                    v-for="(count, cls) in parsedResult.class_count" 
                    :key="cls" 
                    type="info" 
                    size="large"
                    effect="plain"
                  >
                    {{ cls }}: {{ count }}
                  </el-tag>
                </el-space>
              </div>
              
              <!-- 检测详情 -->
              <div v-if="parsedResult.detections && parsedResult.detections.length > 0" style="margin-top: 20px;">
                <h4 style="margin-bottom: 10px;">
                  <el-icon><List /></el-icon> 检测详情:
                </h4>
                <el-table :data="parsedResult.detections" max-height="300" style="width: 100%" border>
                  <el-table-column type="index" label="#" width="50" />
                  <el-table-column prop="class" label="类别" width="120">
                    <template #default="{ row }">
                      <el-tag>{{ row.class }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="confidence" label="置信度" width="200">
                    <template #default="{ row }">
                      <div style="display: flex; align-items: center;">
                        <el-progress 
                          :percentage="row.confidence * 100" 
                          :color="getConfidenceColor(row.confidence)"
                          :show-text="false"
                          style="flex: 1; margin-right: 10px;"
                        />
                        <span style="font-size: 12px; font-weight: bold;">{{ (row.confidence * 100).toFixed(1) }}%</span>
                      </div>
                    </template>
                  </el-table-column>
                  <el-table-column label="边界框 [x1, y1, x2, y2]" v-if="parsedResult.detections[0].bbox">
                    <template #default="{ row }">
                      <code style="font-size: 12px; background: #f5f7fa; padding: 2px 6px; border-radius: 3px;">
                        [{{ row.bbox.map(v => v.toFixed(0)).join(', ') }}]
                      </code>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
      
      <!-- 输出日志 -->
      <div v-if="currentTask && currentTask.result && currentTask.result.output" style="margin-top: 20px;">
        <el-card>
          <template #header>
            <span><el-icon><Document /></el-icon> 输出日志</span>
          </template>
          <el-input
            v-model="currentTask.result.output"
            type="textarea"
            :rows="10"
            readonly
          />
        </el-card>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { convertAPI } from '../api'

const tasks = ref([])
const loading = ref(false)
const detailVisible = ref(false)
const currentTask = ref(null)
let timer = null

// 解析结果数据
const parsedResult = computed(() => {
  if (!currentTask.value || !currentTask.value.result) return null
  
  const result = currentTask.value.result
  
  // 如果result本身就是对象，直接返回
  if (result.model || result.detections || result.count !== undefined) {
    return result
  }
  
  // 如果result.output是JSON字符串，尝试解析
  if (result.output && typeof result.output === 'string') {
    try {
      // 尝试找到JSON部分
      const lines = result.output.split('\n')
      for (let i = lines.length - 1; i >= 0; i--) {
        const line = lines[i].trim()
        if (line.startsWith('{') && line.endsWith('}')) {
          const parsed = JSON.parse(line)
          if (parsed.detections || parsed.count !== undefined) {
            return parsed
          }
        }
      }
    } catch (e) {
      console.error('解析结果失败:', e)
    }
  }
  
  return result
})

// 判断是否有验证数据
const hasValidationData = computed(() => {
  if (!parsedResult.value) return false
  const r = parsedResult.value
  return r.model || r.image || r.count !== undefined || r.inference_time_ms || r.fps || r.detections
})

const loadTasks = async () => {
  loading.value = true
  try {
    const res = await convertAPI.listTasks()
    tasks.value = res.data.tasks
  } catch (error) {
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

const viewDetail = (row) => {
  currentTask.value = row
  detailVisible.value = true
}

const deleteTask = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除该任务？', '提示', {
      type: 'warning'
    })
    await convertAPI.deleteTask(row.task_id)
    ElMessage.success('删除成功')
    loadTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const getTaskTypeColor = (type) => {
  const colors = {
    convert_onnx: 'primary',
    convert_rknn: 'success',
    validate_pt: 'warning',
    validate_onnx: 'info',
    validate_rknn: 'danger'
  }
  return colors[type] || 'info'
}

const getTaskTypeText = (type) => {
  const texts = {
    convert_onnx: 'PT转ONNX',
    convert_rknn: 'ONNX转RKNN',
    validate_pt: 'PT验证',
    validate_onnx: 'ONNX验证',
    validate_rknn: 'RKNN验证'
  }
  return texts[type] || type
}

const getStatusColor = (status) => {
  const colors = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return colors[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

const getProgressStatus = (status) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return null
}

const getConfidenceColor = (confidence) => {
  if (confidence >= 0.8) return '#67C23A'
  if (confidence >= 0.6) return '#E6A23C'
  return '#F56C6C'
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

// 自动刷新任务列表
const startAutoRefresh = () => {
  timer = setInterval(() => {
    loadTasks()
  }, 3000)
}

onMounted(() => {
  loadTasks()
  startAutoRefresh()
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>