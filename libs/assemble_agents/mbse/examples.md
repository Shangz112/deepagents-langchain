# MBSE Skill 使用示例

## 快速开始

### 1. 创建示例项目
```bash
python mbse_tool.py create-project --name "电商系统" --sample
```

### 2. 分析需求
```bash
python mbse_tool.py requirements analyze --project ecommerce_project.json
```

### 3. 生成需求追踪矩阵
```bash
python mbse_tool.py requirements trace --project ecommerce_project.json --output traceability_matrix.csv
```

### 4. 生成SysML图表
```bash
# 生成用例图
python mbse_tool.py diagram use-case --project ecommerce_project.json --output use_case_diagram.puml

# 生成类图
python mbse_tool.py diagram class --project ecommerce_project.json --output class_diagram.puml

# 生成序列图
python mbse_tool.py diagram sequence --project ecommerce_project.json --output sequence_diagram.puml
```

### 5. 设计系统架构
```bash
# 设计分层架构
python mbse_tool.py architecture layered --project ecommerce_project.json --output layered_architecture.md

# 设计微服务架构
python mbse_tool.py architecture microservices --project ecommerce_project.json --output microservices_architecture.md
```

### 6. 验证模型
```bash
python mbse_tool.py validate --project ecommerce_project.json
```

## 手动添加需求和组件

### 添加需求
```bash
python mbse_tool.py requirements add \
  --project ecommerce_project.json \
  --id REQ-006 \
  --title "支付功能" \
  --description "用户可以使用信用卡或支付宝进行支付" \
  --type functional \
  --priority high
```

### 添加组件
```bash
python mbse_tool.py model add-component \
  --project ecommerce_project.json \
  --id COMP-005 \
  --name PaymentService \
  --type 业务服务 \
  --description "处理支付相关的业务逻辑"
```

## 输出文件说明

### 项目文件 (.json)
包含完整的项目信息：
- 项目基本信息
- 需求列表
- 组件列表
- 创建和更新时间

### 图表文件 (.puml)
PlantUML格式的SysML图表：
- 可用PlantUML工具转换为图片
- 支持用例图、类图、序列图等

### 架构文档 (.md)
Markdown格式的架构设计文档：
- 分层架构设计
- 微服务架构设计
- 包含技术栈建议和部署架构

### 追踪矩阵 (.csv)
CSV格式的需求追踪矩阵：
- 可用Excel等工具打开
- 包含需求间的关系和组件映射

## 最佳实践

1. **需求管理**
   - 使用有意义的ID命名（如REQ-001, REQ-002）
   - 确保需求描述清晰、具体
   - 设置合适的优先级
   - 标记可测试性

2. **组件设计**
   - 遵循单一职责原则
   - 明确定义组件接口
   - 管理好组件间依赖关系
   - 记录组件职责

3. **模型验证**
   - 定期运行验证检查
   - 修复所有错误
   - 关注警告信息
   - 监控质量指标

4. **文档生成**
   - 及时更新架构文档
   - 保持图表与代码同步
   - 生成可追踪的需求文档
   - 维护版本历史