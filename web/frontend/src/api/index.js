import axios from 'axios'

const API_BASE = '/api'

// 模型管理
export const modelAPI = {
  // 获取模型列表
  list: () => axios.get(`${API_BASE}/models`),
  
  // 上传模型
  upload: (file, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    return axios.post(`${API_BASE}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress
    })
  },
  
  // 下载模型
  download: (filename) => `${API_BASE}/models/${filename}`,
  
  // 删除模型
  delete: (filename) => axios.delete(`${API_BASE}/models/${filename}`)
}

// 转换任务
export const convertAPI = {
  // PT转ONNX
  toOnnx: (data) => axios.post(`${API_BASE}/convert/onnx`, data),
  
  // ONNX转RKNN
  toRknn: (data) => axios.post(`${API_BASE}/convert/rknn`, data),
  
  // 获取任务状态
  getStatus: (taskId) => axios.get(`${API_BASE}/tasks/${taskId}`),
  
  // 获取所有任务
  listTasks: () => axios.get(`${API_BASE}/tasks`),
  
  // 删除任务
  deleteTask: (taskId) => axios.delete(`${API_BASE}/tasks/${taskId}`)
}

// 模型验证
export const validateAPI = {
  // PT模型验证
  pt: (data) => axios.post(`${API_BASE}/validate/pt`, data),
  
  // ONNX模型验证
  onnx: (data) => axios.post(`${API_BASE}/validate/onnx`, data),
  
  // RKNN模型验证
  rknn: (data) => axios.post(`${API_BASE}/validate/rknn`, data)
}

// 平台信息
export const platformAPI = {
  // 获取支持的芯片平台
  list: () => axios.get(`${API_BASE}/platforms`)
}

// 测试图片
export const imageAPI = {
  // 获取图片列表
  list: () => axios.get(`${API_BASE}/images`),
  
  // 上传测试图片
  upload: (file, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    return axios.post(`${API_BASE}/images/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress
    })
  }
}

// 环境检查
export const envAPI = {
  check: () => axios.get(`${API_BASE}/environment/check`)
}

// 健康检查
export const healthAPI = {
  check: () => axios.get(`${API_BASE}/health`)
}
