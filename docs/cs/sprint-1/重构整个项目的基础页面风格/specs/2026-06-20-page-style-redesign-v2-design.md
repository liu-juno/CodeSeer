# 页面风格重构设计方案

**日期**: 2026-06-20
**需求**: 重构整个项目的基础页面风格
**参考**: TAPD 腾讯敏捷协作平台风格
**版本**: v2.0

---

## 1. 设计目标

将现有"AI 化"紫/靛蓝渐变风格重构为腾讯 TAPD 的企业级蓝色系风格，具体目标：
- 整体配色系统统一为 TAPD 蓝色系
- 引入 Element Plus 组件库统一 UI
- 侧边栏改造为 ElMenu 图标模式
- 所有页面表格/表单/弹窗组件统一
- 视觉上接近 TAPD 企业协作平台风格

---

## 2. 技术选型

| 类别 | 选择 | 说明 |
|------|------|------|
| UI 组件库 | **Element Plus** | Vue 3 原生、企业风格与 TAPD 相近、定制灵活 |
| 图标库 | @element-plus/icons-vue | Element Plus 官方图标 |
| 样式方案 | CSS 变量 + Element Plus 主题覆盖 | 保留现有变量系统，补充 el- 变量覆盖 |

---

## 3. 配色系统（扩展现有变量）

```css
:root {
  /* 已有变量（保留） */
  --color-primary: #2d5bff;
  --color-primary-hover: #1e4ae8;
  --color-bg: #f5f7ff;
  --color-success: #00a870;
  --color-warning: #ff9a2e;
  --color-error: #ff4533;
  
  /* Element Plus 主题覆盖 */
  --el-color-primary: #2d5bff;
  --el-color-primary-light-3: #5a7bff;
  --el-color-primary-light-5: #8aa3ff;
  --el-color-primary-light-7: #b8cbff;
  --el-color-primary-light-8: #d0deff;
  --el-color-primary-light-9: #e8eeff;
  --el-border-radius-base: 8px;
  --el-font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Inter', 'Helvetica Neue', Arial, sans-serif;
}
```

---

## 4. 侧边栏改造

### 目标形态
- 宽度：56px（收起） / 200px（展开）
- 模式：ElMenu vertical 模式，collapse 控制
- 图标：支持 tooltip 提示

### 组件映射
| 现有 | 重构后 |
|------|--------|
| 纯 CSS nav | ElMenu + ElMenuItem |
| 文字 label | tooltip 提示 |
| router-link-active | Element Plus active 机制 |

### 布局结构
```
┌─────┬────────────────────────────────────┐
│ 侧边栏 │          Main Content             │
│ 56px  │                                    │
│ ElMenu │  Topbar + RouterView              │
│        │                                    │
└─────┴────────────────────────────────────┘
```

---

## 5. 页面重构清单

### P0 - 核心页面（表格主导）
| 页面 | 路由 | 核心组件 | 优先级 |
|------|------|----------|--------|
| Projects | /projects | ElTable, ElInput, ElButton | P0 |
| Iterations | /iterations | ElTable, ElSelect, ElButton | P0 |
| Requirements | /requirements | ElTable, ElSelect, ElButton | P0 |
| ProjectDetail | /project/:id | ElTabs, ElTable | P0 |

### P1 - 详情页（表单主导）
| 页面 | 路由 | 核心组件 | 优先级 |
|------|------|----------|--------|
| IterationDetail | /iteration/:id | ElForm, ElInput | P1 |
| RequirementDetail | /requirement/:id | ElForm, ElInput | P1 |

### P2 - 功能页
| 页面 | 路由 | 核心组件 | 优先级 |
|------|------|----------|--------|
| Dashboard | /dashboard | ElCard, ElStatistic | P2 |
| Standup | /standup | ElDatePicker, ElCard | P2 |

### P3 - 配置页
| 页面 | 路由 | 核心组件 | 优先级 |
|------|------|----------|--------|
| Login | /login | ElForm | P3 |
| Settings | /settings | ElForm, ElSwitch | P3 |
| Users | /users | ElTable, ElDialog | P3 |
| McpConfig | /mcp-config | ElForm, ElInput | P3 |
| Modules | /modules | ElTable, ElDialog | P3 |
| Webhooks | /webhooks | ElTable, ElDialog | P3 |
| Documents | /documents | ElTable, ElUpload | P3 |

---

## 6. 组件统一规范

### 6.1 表格（ElTable）
```css
.el-table {
  --el-table-border-color: #e8e9eb;
  --el-table-header-bg-color: #f5f7ff;
  --el-table-row-hover-bg-color: #fafafa;
  border-radius: 12px;
  overflow: hidden;
}
```

### 6.2 按钮
```css
.el-button--primary {
  --el-button-bg-color: #2d5bff;
  --el-button-border-color: #2d5bff;
  --el-button-hover-bg-color: #1e4ae8;
  --el-button-border-radius: 8px;
}
```

### 6.3 弹窗（ElDialog）
```css
.el-dialog {
  --el-dialog-border-radius: 14px;
}
```

### 6.4 表单（ElForm）
```css
.el-form-item__label {
  font-weight: 600;
  color: #1f2329;
}
```

### 6.5 输入框（ElInput）
```css
.el-input {
  --el-input-border-radius: 8px;
}
```

---

## 7. 实施顺序

### 阶段一：基础设施（1-2 天）
1. 安装 Element Plus 及图标库
2. 配置 Element Plus 主题变量覆盖
3. 重构侧边栏为 ElMenu 组件
4. 提取公共布局组件（Layout.vue）

### 阶段二：P0 页面（2-3 天）
5. Projects 页面重构
6. Iterations 页面重构
7. Requirements 页面重构
8. ProjectDetail 页面重构

### 阶段三：P1 页面（1-2 天）
9. IterationDetail 页面重构
10. RequirementDetail 页面重构

### 阶段四：P2/P3 页面（1-2 天）
11. Dashboard/Standup 重构
12. 配置类页面重构（Settings/Users/McpConfig/Modules/Webhooks/Documents）
13. Login 页面重构

---

## 8. 验收标准

- [ ] Element Plus 主题变量覆盖完成，整体视觉符合 TAPD 风格
- [ ] 侧边栏改为 ElMenu 图标模式，支持展开/收起
- [ ] 所有表格页面统一使用 ElTable（Projects/Iterations/Requirements/Dashboard 等）
- [ ] 所有表单页面统一使用 ElForm
- [ ] 所有弹窗统一使用 ElDialog
- [ ] 14+ 页面全部重构完成
- [ ] 响应式适配（侧边栏收起时内容区自适应）

---

## 9. 不在范围内

- 后端 API 修改
- 业务逻辑变更
- 现有组件库（如 @vueuse）替换
- 移动端适配
