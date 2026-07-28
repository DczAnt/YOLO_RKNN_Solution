<template>
  <div id="app">
    <el-container style="height: 100vh">
      <!-- 顶部导航 -->
      <el-header style="background: #409EFF; color: white;">
        <div style="display: flex; align-items: center; height: 100%;">
          <el-icon size="24" style="margin-right: 10px;"><Monitor /></el-icon>
          <h2 style="margin: 0;">YOLO-RKNN 模型转换平台</h2>
        </div>
      </el-header>

      <!-- 主体内容 -->
      <el-container>
        <!-- 左侧菜单 -->
        <el-aside width="200px" style="background: #f5f7fa;">
          <el-menu :default-active="activeMenu" @select="handleMenuSelect">
            <el-menu-item index="config">
              <el-icon><Setting /></el-icon>
              <span>配置管理</span>
            </el-menu-item>
            <el-menu-item index="models">
              <el-icon><Folder /></el-icon>
              <span>模型管理</span>
            </el-menu-item>
            <el-menu-item index="convert">
              <el-icon><Refresh /></el-icon>
              <span>模型转换</span>
            </el-menu-item>
            <el-menu-item index="validate">
              <el-icon><Check /></el-icon>
              <span>模型验证</span>
            </el-menu-item>
            <el-menu-item index="tasks">
              <el-icon><List /></el-icon>
              <span>任务列表</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <!-- 右侧内容 -->
        <el-main>
          <!-- 配置管理 -->
          <div v-if="activeMenu === 'config'">
            <ConfigManager />
          </div>

          <!-- 模型管理 -->
          <div v-if="activeMenu === 'models'">
            <ModelManager @refresh="loadModels" />
          </div>

          <!-- 模型转换 -->
          <div v-if="activeMenu === 'convert'">
            <ModelConvert @refresh="loadModels" />
          </div>

          <!-- 模型验证 -->
          <div v-if="activeMenu === 'validate'">
            <ModelValidate />
          </div>

          <!-- 任务列表 -->
          <div v-if="activeMenu === 'tasks'">
            <TaskList />
          </div>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { modelAPI } from './api'
import ConfigManager from './components/ConfigManager.vue'
import ModelManager from './components/ModelManager.vue'
import ModelConvert from './components/ModelConvert.vue'
import ModelValidate from './components/ModelValidate.vue'
import TaskList from './components/TaskList.vue'

const activeMenu = ref('config')

const handleMenuSelect = (index) => {
  activeMenu.value = index
}

const loadModels = async () => {
  // 刷新模型列表
}

onMounted(() => {
  // 初始化
})
</script>

<style>
#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}

.el-header {
  padding: 0 20px;
}

.el-aside {
  border-right: 1px solid #e6e6e6;
}

.el-main {
  padding: 20px;
  background: #fff;
}
</style>
