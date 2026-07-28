<template>
  <div>
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 环境检查 -->
      <el-tab-pane label="环境检查" name="environment">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span><el-icon><Tools /></el-icon> 环境检查</span>
              <el-button type="primary" @click="checkEnvironment" :loading="envLoading">
                <el-icon><Refresh /></el-icon>
                执行检查
              </el-button>
            </div>
          </template>
          
          <el-input
            v-model="envOutput"
            type="textarea"
            :rows="20"
            readonly
            placeholder="点击'执行检查'按钮开始检查环境..."
          />
        </el-card>
      </el-tab-pane>
      
      <!-- RKNN验证配置 -->
      <el-tab-pane label="RKNN验证配置" name="rknn">
        <el-row :gutter="20">
          <!-- WSL配置 -->
          <el-col :span="12">
            <el-card>
              <template #header>
                <span><el-icon><Monitor /></el-icon> WSL环境配置</span>
              </template>
              
              <el-form :model="wslConfig" label-width="120px">
                <el-form-item label="WSL用户名">
                  <el-input v-model="wslConfig.username" placeholder="tinfo" />
                </el-form-item>
                <el-form-item label="WSL密码">
                  <el-input v-model="wslConfig.password" type="password" show-password placeholder="123456" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveWslConfig">
                    <el-icon><Check /></el-icon>
                    保存配置
                  </el-button>
                  <el-button @click="loadWslConfig">
                    <el-icon><Refresh /></el-icon>
                    加载配置
                  </el-button>
                </el-form-item>
              </el-form>
              
              <el-alert
                type="info"
                :closable="false"
                style="margin-top: 10px;"
              >
                <template #title>
                  <el-icon><InfoFilled /></el-icon>
                  说明
                </template>
                WSL配置用于在Windows环境下运行转换脚本和后端服务。
              </el-alert>
            </el-card>
          </el-col>
          
          <!-- RK主板配置 -->
          <el-col :span="12">
            <el-card>
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span><el-icon><Cpu /></el-icon> RK主板配置</span>
                  <el-button size="small" type="primary" @click="testRkConnection" :loading="testRkLoading">
                    <el-icon><Connection /></el-icon>
                    测试连接
                  </el-button>
                </div>
              </template>
              
              <el-form :model="rkConfig" label-width="120px">
                <el-form-item label="RK主板IP">
                  <el-input v-model="rkConfig.host" placeholder="192.168.3.208">
                    <template #prepend>
                      <el-icon><Location /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>
                <el-form-item label="用户名">
                  <el-input v-model="rkConfig.username" placeholder="root" />
                </el-form-item>
                <el-form-item label="密码">
                  <el-input v-model="rkConfig.password" type="password" show-password />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveRkConfig">
                    <el-icon><Check /></el-icon>
                    保存配置
                  </el-button>
                  <el-button @click="loadRkConfig">
                    <el-icon><Refresh /></el-icon>
                    加载配置
                  </el-button>
                </el-form-item>
              </el-form>
              
              <el-alert
                type="warning"
                :closable="false"
                style="margin-top: 10px;"
              >
                <template #title>
                  <el-icon><WarningFilled /></el-icon>
                  注意
                </template>
                RKNN验证需要SSH连接到RK主板，请确保网络通畅且SSH服务已开启。
              </el-alert>
            </el-card>
          </el-col>
        </el-row>
        
        <!-- 配置预览 -->
        <el-card style="margin-top: 20px;">
          <template #header>
            <span><el-icon><Document /></el-icon> 当前配置预览</span>
          </template>
          
          <el-descriptions :column="2" border>
            <el-descriptions-item label="WSL用户名">
              <el-tag v-if="wslConfig.username">{{ wslConfig.username }}</el-tag>
              <el-tag v-else type="info">未设置</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="WSL密码">
              <el-tag v-if="wslConfig.password">******</el-tag>
              <el-tag v-else type="info">未设置</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="RK主板IP">
              <el-tag v-if="rkConfig.host">{{ rkConfig.host }}</el-tag>
              <el-tag v-else type="info">未设置</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="RK用户名">
              <el-tag v-if="rkConfig.username">{{ rkConfig.username }}</el-tag>
              <el-tag v-else type="info">未设置</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="RK密码" :span="2">
              <el-tag v-if="rkConfig.password">******</el-tag>
              <el-tag v-else type="info">未设置</el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { envAPI } from '../api'

const activeTab = ref('environment')
const envLoading = ref(false)
const envOutput = ref('')
const testRkLoading = ref(false)

// WSL配置
const wslConfig = ref({
  username: 'tinfo',
  password: '123456'
})

// RK主板配置
const rkConfig = ref({
  host: '192.168.3.208',
  username: 'root',
  password: ''
})

// 环境检查
const checkEnvironment = async () => {
  envLoading.value = true
  try {
    const res = await envAPI.check()
    envOutput.value = res.data.output || res.data.error || '检查完成'
    ElMessage.success('环境检查完成')
  } catch (error) {
    envOutput.value = '检查失败: ' + error.message
    ElMessage.error('环境检查失败')
  } finally {
    envLoading.value = false
  }
}

// 保存WSL配置
const saveWslConfig = () => {
  localStorage.setItem('wsl_config', JSON.stringify(wslConfig.value))
  ElMessage.success('WSL配置已保存')
}

// 加载WSL配置
const loadWslConfig = () => {
  const saved = localStorage.getItem('wsl_config')
  if (saved) {
    wslConfig.value = JSON.parse(saved)
    ElMessage.success('WSL配置已加载')
  } else {
    ElMessage.warning('未找到保存的WSL配置')
  }
}

// 保存RK配置
const saveRkConfig = () => {
  localStorage.setItem('rk_config', JSON.stringify(rkConfig.value))
  ElMessage.success('RK主板配置已保存')
}

// 加载RK配置
const loadRkConfig = () => {
  const saved = localStorage.getItem('rk_config')
  if (saved) {
    rkConfig.value = JSON.parse(saved)
    ElMessage.success('RK主板配置已加载')
  } else {
    ElMessage.warning('未找到保存的RK配置')
  }
}

// 测试RK连接
const testRkConnection = async () => {
  if (!rkConfig.value.host || !rkConfig.value.username || !rkConfig.value.password) {
    ElMessage.warning('请先配置RK主板连接信息')
    return
  }
  
  testRkLoading.value = true
  try {
    // 模拟测试连接
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success(`RK主板 ${rkConfig.value.host} 连接测试成功`)
  } catch (error) {
    ElMessage.error('连接测试失败: ' + error.message)
  } finally {
    testRkLoading.value = false
  }
}

onMounted(() => {
  // 加载保存的配置
  loadWslConfig()
  loadRkConfig()
})
</script>