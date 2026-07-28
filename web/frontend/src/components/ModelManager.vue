<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>模型列表</span>
          <el-upload
            :show-file-list="false"
            :before-upload="beforeUpload"
            :http-request="handleUpload"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>
              上传模型
            </el-button>
          </el-upload>
        </div>
      </template>

      <el-table :data="models" style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="文件名" width="300" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeColor(row.type)">{{ row.type.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="size" label="大小" width="150">
          <template #default="{ row }">
            {{ formatSize(row.size) }}
          </template>
        </el-table-column>
        <el-table-column prop="mtime" label="修改时间" width="200">
          <template #default="{ row }">
            {{ formatTime(row.mtime) }}
          </template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button size="small" @click="handleDownload(row)">
              <el-icon><Download /></el-icon>
              下载
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { modelAPI } from '../api'

const models = ref([])
const loading = ref(false)

const loadModels = async () => {
  loading.value = true
  try {
    const res = await modelAPI.list()
    models.value = res.data.models
  } catch (error) {
    ElMessage.error('加载模型列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const beforeUpload = (file) => {
  const isModel = file.name.endsWith('.pt') || file.name.endsWith('.onnx')
  if (!isModel) {
    ElMessage.error('只能上传 .pt 或 .onnx 文件')
    return false
  }
  return true
}

const handleUpload = async ({ file }) => {
  try {
    await modelAPI.upload(file)
    ElMessage.success('上传成功')
    loadModels()
  } catch (error) {
    ElMessage.error('上传失败: ' + error.message)
  }
}

const handleDownload = (row) => {
  const url = modelAPI.download(row.name)
  window.open(url, '_blank')
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除该模型？', '提示', {
      type: 'warning'
    })
    await modelAPI.delete(row.name)
    ElMessage.success('删除成功')
    loadModels()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

const getTypeColor = (type) => {
  const colors = {
    pt: 'primary',
    onnx: 'success',
    rknn: 'warning'
  }
  return colors[type] || 'info'
}

const formatSize = (size) => {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + ' KB'
  return (size / 1024 / 1024).toFixed(2) + ' MB'
}

const formatTime = (time) => {
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadModels()
})

defineExpose({ loadModels })
</script>