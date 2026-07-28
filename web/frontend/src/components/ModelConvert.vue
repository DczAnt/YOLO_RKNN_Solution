<template>
  <div>
    <el-row :gutter="20">
      <!-- PT转ONNX -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>PT → ONNX 转换</span>
          </template>
          
          <el-form :model="onnxForm" label-width="100px">
            <el-form-item label="PT模型">
              <el-select v-model="onnxForm.pt_model" placeholder="选择PT模型">
                <el-option
                  v-for="model in ptModels"
                  :key="model.name"
                  :label="model.name"
                  :value="model.name"
                />
              </el-select>
            </el-form-item>
            
            <el-form-item label="输入尺寸">
              <el-input-number v-model="onnxForm.imgsz" :min="320" :max="1280" :step="32" />
            </el-form-item>
            
            <el-form-item label="Opset版本">
              <el-input-number v-model="onnxForm.opset" :min="9" :max="17" />
            </el-form-item>
            
            <el-form-item label="简化模型">
              <el-switch v-model="onnxForm.simplify" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="convertToOnnx" :loading="onnxLoading">
                开始转换
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- ONNX转RKNN -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>ONNX → RKNN 转换</span>
          </template>
          
          <el-form :model="rknnForm" label-width="100px">
            <el-form-item label="ONNX模型">
              <el-select v-model="rknnForm.onnx_model" placeholder="选择ONNX模型">
                <el-option
                  v-for="model in onnxModels"
                  :key="model.name"
                  :label="model.name"
                  :value="model.name"
                />
              </el-select>
            </el-form-item>
            
            <el-form-item label="目标芯片">
              <el-select v-model="rknnForm.platform" placeholder="选择RK芯片">
                <el-option
                  v-for="platform in platforms"
                  :key="platform.id"
                  :label="platform.name"
                  :value="platform.id"
                >
                  <div style="display: flex; justify-content: space-between;">
                    <span>{{ platform.name }}</span>
                    <el-tag v-if="platform.recommended" type="success" size="small">推荐</el-tag>
                  </div>
                </el-option>
              </el-select>
              <div v-if="selectedPlatform" style="margin-top: 5px; font-size: 12px; color: #909399;">
                {{ selectedPlatform.description }} | 内存: {{ selectedPlatform.memory }}
              </div>
            </el-form-item>
            
            <el-form-item label="精度类型">
              <el-radio-group v-model="rknnForm.precision">
                <el-radio value="fp16">FP16</el-radio>
                <el-radio value="int8">INT8</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item label="量化数据集" v-if="rknnForm.precision === 'int8'">
              <el-input v-model="rknnForm.quantize_dataset" placeholder="quantize_dataset.txt" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="convertToRknn" :loading="rknnLoading">
                开始转换
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 支持的芯片平台信息 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <span>支持的RK芯片平台</span>
      </template>
      
      <el-table :data="platforms" style="width: 100%">
        <el-table-column prop="name" label="芯片型号" width="120" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="memory" label="内存" width="100" />
        <el-table-column label="推荐" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.recommended" type="success">推荐</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { modelAPI, convertAPI, platformAPI } from '../api'

const models = ref([])
const platforms = ref([])
const onnxLoading = ref(false)
const rknnLoading = ref(false)

const onnxForm = ref({
  pt_model: '',
  imgsz: 640,
  opset: 12,
  simplify: true,
  dynamic: false
})

const rknnForm = ref({
  onnx_model: '',
  platform: 'rk3588',
  precision: 'fp16',
  quantize_dataset: '',
  mean_values: [0, 0, 0],
  std_values: [255, 255, 255]
})

const ptModels = computed(() => models.value.filter(m => m.type === 'pt'))
const onnxModels = computed(() => models.value.filter(m => m.type === 'onnx'))
const selectedPlatform = computed(() => platforms.value.find(p => p.id === rknnForm.value.platform))

const loadModels = async () => {
  try {
    const res = await modelAPI.list()
    models.value = res.data.models
  } catch (error) {
    ElMessage.error('加载模型列表失败')
  }
}

const loadPlatforms = async () => {
  try {
    const res = await platformAPI.list()
    platforms.value = res.data.platforms
  } catch (error) {
    ElMessage.error('加载芯片平台失败')
  }
}

const convertToOnnx = async () => {
  if (!onnxForm.value.pt_model) {
    ElMessage.warning('请选择PT模型')
    return
  }
  
  onnxLoading.value = true
  try {
    const res = await convertAPI.toOnnx(onnxForm.value)
    ElMessage.success('任务已创建: ' + res.data.task_id)
    loadModels()
  } catch (error) {
    ElMessage.error('转换失败: ' + error.message)
  } finally {
    onnxLoading.value = false
  }
}

const convertToRknn = async () => {
  if (!rknnForm.value.onnx_model) {
    ElMessage.warning('请选择ONNX模型')
    return
  }
  
  if (rknnForm.value.precision === 'int8' && !rknnForm.value.quantize_dataset) {
    ElMessage.warning('INT8量化需要量化数据集')
    return
  }
  
  rknnLoading.value = true
  try {
    const res = await convertAPI.toRknn(rknnForm.value)
    ElMessage.success('任务已创建: ' + res.data.task_id)
    loadModels()
  } catch (error) {
    ElMessage.error('转换失败: ' + error.message)
  } finally {
    rknnLoading.value = false
  }
}

onMounted(() => {
  loadModels()
  loadPlatforms()
})

defineExpose({ loadModels })
</script>