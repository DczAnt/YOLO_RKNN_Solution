<template>
  <div>
    <!-- 测试图片管理 -->
    <el-card style="margin-bottom: 20px;">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>测试图片</span>
          <el-upload
            :show-file-list="false"
            :before-upload="beforeImageUpload"
            :http-request="handleImageUpload"
          >
            <el-button type="primary" size="small">
              <el-icon><Upload /></el-icon>
              上传图片
            </el-button>
          </el-upload>
        </div>
      </template>
      
      <el-table :data="images" style="width: 100%" v-loading="imageLoading" max-height="200">
        <el-table-column prop="name" label="文件名" />
        <el-table-column prop="size" label="大小" width="100">
          <template #default="{ row }">
            {{ formatSize(row.size) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click.stop="selectImage(row.name)">
              <el-icon><Check /></el-icon>
              选择
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="selectedImageName" style="margin-top: 10px; padding: 10px; background: #f0f9ff; border-radius: 4px;">
        <el-icon><Picture /></el-icon>
        当前选择: <strong>{{ selectedImageName }}</strong>
      </div>
    </el-card>

    <el-row :gutter="20">
      <!-- PT模型验证 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>PT模型验证</span>
          </template>
          
          <el-form :model="ptValidateForm" label-width="100px">
            <el-form-item label="PT模型">
              <el-select v-model="ptValidateForm.model" placeholder="选择模型">
                <el-option v-for="m in ptModels" :key="m.name" :label="m.name" :value="m.name" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="测试图片">
              <el-input v-model="ptValidateForm.image" placeholder="点击上方图片选择" readonly>
                <template #append>
                  <el-button v-if="ptValidateForm.image" @click="ptValidateForm.image = ''">
                    <el-icon><Close /></el-icon>
                  </el-button>
                </template>
              </el-input>
            </el-form-item>
            
            <el-form-item label="置信度">
              <el-slider v-model="ptValidateForm.conf_threshold" :min="0" :max="1" :step="0.05" show-input />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="validatePt" :loading="ptLoading">
                开始验证
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- ONNX模型验证 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>ONNX模型验证</span>
          </template>
          
          <el-form :model="onnxValidateForm" label-width="100px">
            <el-form-item label="ONNX模型">
              <el-select v-model="onnxValidateForm.model" placeholder="选择模型">
                <el-option v-for="m in onnxModels" :key="m.name" :label="m.name" :value="m.name" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="测试图片">
              <el-input v-model="onnxValidateForm.image" placeholder="点击上方图片选择" readonly>
                <template #append>
                  <el-button v-if="onnxValidateForm.image" @click="onnxValidateForm.image = ''">
                    <el-icon><Close /></el-icon>
                  </el-button>
                </template>
              </el-input>
            </el-form-item>
            
            <el-form-item label="置信度">
              <el-slider v-model="onnxValidateForm.conf_threshold" :min="0" :max="1" :step="0.05" show-input />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="validateOnnx" :loading="onnxLoading">
                开始验证
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- RKNN模型验证 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>RKNN模型验证</span>
          </template>
          
          <el-form :model="rknnValidateForm" label-width="100px">
            <el-form-item label="RKNN模型">
              <el-select v-model="rknnValidateForm.model" placeholder="选择模型">
                <el-option v-for="m in rknnModels" :key="m.name" :label="m.name" :value="m.name" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="测试图片">
              <el-input v-model="rknnValidateForm.image" placeholder="点击上方图片选择" readonly>
                <template #append>
                  <el-button v-if="rknnValidateForm.image" @click="rknnValidateForm.image = ''">
                    <el-icon><Close /></el-icon>
                  </el-button>
                </template>
              </el-input>
            </el-form-item>
            
            <el-form-item label="置信度">
              <el-slider v-model="rknnValidateForm.conf_threshold" :min="0" :max="1" :step="0.05" show-input />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="validateRknn" :loading="rknnLoading">
                开始验证
              </el-button>
            </el-form-item>
          </el-form>
          
          <el-alert
            v-if="!hasRkConfig"
            type="warning"
            :closable="false"
            style="margin-top: 10px;"
          >
            <template #title>
              <el-icon><WarningFilled /></el-icon>
              未配置RKNN验证
            </template>
            请先在"配置管理"中设置RK主板连接信息
          </el-alert>
        </el-card>
      </el-col>
    </el-row>

    <!-- 验证结果 -->
    <el-card style="margin-top: 20px;" v-if="validateResult">
      <template #header>
        <span>验证结果</span>
      </template>
      
      <el-descriptions :column="3" border>
        <el-descriptions-item label="状态">
          <el-tag :type="validateResult.status === 'completed' ? 'success' : 'danger'">
            {{ validateResult.status === 'completed' ? '成功' : '失败' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="消息">{{ validateResult.message }}</el-descriptions-item>
        <el-descriptions-item label="进度">{{ validateResult.progress }}%</el-descriptions-item>
      </el-descriptions>
      
      <div v-if="validateResult.result" style="margin-top: 20px;">
        <h4>检测结果:</h4>
        <el-input
          v-model="validateResult.result.output"
          type="textarea"
          :rows="10"
          readonly
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { modelAPI, imageAPI, validateAPI } from '../api'

const models = ref([])
const images = ref([])
const imageLoading = ref(false)
const ptLoading = ref(false)
const onnxLoading = ref(false)
const rknnLoading = ref(false)
const validateResult = ref(null)
const selectedImageName = ref('')

const ptValidateForm = ref({
  model: '',
  image: '',
  conf_threshold: 0.25,
  iou_threshold: 0.45
})

const onnxValidateForm = ref({
  model: '',
  image: '',
  conf_threshold: 0.25
})

const rknnValidateForm = ref({
  model: '',
  image: '',
  host: '',
  username: '',
  password: '',
  conf_threshold: 0.25
})

const ptModels = computed(() => models.value.filter(m => m.type === 'pt'))
const onnxModels = computed(() => models.value.filter(m => m.type === 'onnx'))
const rknnModels = computed(() => models.value.filter(m => m.type === 'rknn'))

// 检查是否已配置RKNN
const hasRkConfig = computed(() => {
  const saved = localStorage.getItem('rk_config')
  if (saved) {
    const config = JSON.parse(saved)
    return config.host && config.username && config.password
  }
  return false
})

const loadModels = async () => {
  try {
    const res = await modelAPI.list()
    models.value = res.data.models
  } catch (error) {
    ElMessage.error('加载模型列表失败')
  }
}

const loadImages = async () => {
  imageLoading.value = true
  try {
    const res = await imageAPI.list()
    images.value = res.data.images
  } catch (error) {
    ElMessage.error('加载图片列表失败')
  } finally {
    imageLoading.value = false
  }
}

const beforeImageUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  return true
}

const handleImageUpload = async ({ file }) => {
  try {
    await imageAPI.upload(file)
    ElMessage.success('上传成功')
    loadImages()
  } catch (error) {
    ElMessage.error('上传失败: ' + error.message)
  }
}

const selectImage = (name) => {
  selectedImageName.value = name
  ptValidateForm.value.image = name
  onnxValidateForm.value.image = name
  rknnValidateForm.value.image = name
  ElMessage.success('已选择图片: ' + name)
}

const validatePt = async () => {
  if (!ptValidateForm.value.model || !ptValidateForm.value.image) {
    ElMessage.warning('请选择模型和测试图片')
    return
  }
  
  ptLoading.value = true
  try {
    const res = await validateAPI.pt(ptValidateForm.value)
    ElMessage.success('验证任务已创建: ' + res.data.task_id)
  } catch (error) {
    ElMessage.error('验证失败: ' + error.message)
  } finally {
    ptLoading.value = false
  }
}

const validateOnnx = async () => {
  if (!onnxValidateForm.value.model || !onnxValidateForm.value.image) {
    ElMessage.warning('请选择模型和测试图片')
    return
  }
  
  onnxLoading.value = true
  try {
    const res = await validateAPI.onnx(onnxValidateForm.value)
    ElMessage.success('验证任务已创建: ' + res.data.task_id)
  } catch (error) {
    ElMessage.error('验证失败: ' + error.message)
  } finally {
    onnxLoading.value = false
  }
}

const validateRknn = async () => {
  if (!rknnValidateForm.value.model || !rknnValidateForm.value.image) {
    ElMessage.warning('请选择模型和测试图片')
    return
  }
  
  // 从localStorage加载RK配置
  const saved = localStorage.getItem('rk_config')
  if (saved) {
    const config = JSON.parse(saved)
    rknnValidateForm.value.host = config.host
    rknnValidateForm.value.username = config.username
    rknnValidateForm.value.password = config.password
  }
  
  if (!rknnValidateForm.value.host || !rknnValidateForm.value.username || !rknnValidateForm.value.password) {
    ElMessage.warning('请先在配置管理中设置RK主板连接信息')
    return
  }
  
  rknnLoading.value = true
  try {
    const res = await validateAPI.rknn(rknnValidateForm.value)
    ElMessage.success('验证任务已创建: ' + res.data.task_id)
  } catch (error) {
    ElMessage.error('验证失败: ' + error.message)
  } finally {
    rknnLoading.value = false
  }
}

const formatSize = (size) => {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + ' KB'
  return (size / 1024 / 1024).toFixed(2) + ' MB'
}

onMounted(() => {
  loadModels()
  loadImages()
})
</script>
