# 前端搜索功能修复说明

## 问题

点击"网络搜索供应商"按钮后没有结果显示。

## 原因分析

1. **API调用问题**：
   - 前端使用的是 `/api/search/suppliers`，但没有传递 `product_id`
   - 应该使用 `/api/search/suppliers/{product_id}` 来自动更新产品

2. **超时问题**：
   - MCP调用可能需要10-15秒，但前端超时设置为30秒
   - 已增加到60秒

3. **数据更新问题**：
   - 搜索成功后没有刷新产品列表
   - 已添加 `onRefresh` 回调来刷新列表

## 修复内容

### 1. 更新 API 调用 (`frontend/src/services/api.ts`)
- 添加 `searchSuppliersForProduct` 函数
- 增加超时时间到60秒

### 2. 更新 WebSearchButton (`frontend/src/components/WebSearchButton.tsx`)
- 使用 `searchSuppliersForProduct` 而不是 `searchSuppliers`
- 改进错误处理
- 添加超时错误提示

### 3. 更新 ProductCard (`frontend/src/components/ProductCard.tsx`)
- 添加 `onRefresh` prop
- 搜索成功后自动刷新产品列表

### 4. 更新 App (`frontend/src/App.tsx`)
- 添加 `handleRefresh` 函数
- 传递给 ProductCard 组件

## 测试步骤

1. 启动后端服务：
   ```bash
   cd backend
   python main.py
   ```

2. 启动前端服务：
   ```bash
   cd frontend
   npm run dev
   ```

3. 测试搜索：
   - 打开前端页面
   - 点击产品的"网络搜索供应商"按钮
   - 等待10-15秒（MCP调用时间）
   - 查看供应商列表是否更新

## 预期行为

1. 点击按钮后显示"搜索中..."状态
2. 等待10-15秒（MCP调用）
3. 成功后自动刷新产品列表
4. 新搜索的供应商显示在产品卡片中
5. 如果失败，显示错误信息

## 注意事项

- MCP调用可能需要较长时间，请耐心等待
- 如果超时，会显示超时错误提示
- 搜索成功后会自动更新产品数据

