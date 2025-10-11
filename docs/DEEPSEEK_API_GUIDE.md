# DeepSeek API 配置指南

## 概述

本系统集成DeepSeek API进行AI智能代码分析，生成专业的自然语言报告。本指南将详细介绍如何配置和使用DeepSeek API功能。

## 🔑 API密钥配置

### 方法1: 环境变量配置（推荐）

```bash
# Linux/Mac
export DEEPSEEK_API_KEY="your_api_key_here"

# Windows
set DEEPSEEK_API_KEY=your_api_key_here

# 永久设置（Linux/Mac）
echo 'export DEEPSEEK_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### 方法2: 直接编辑配置文件

编辑 `api/deepseek_config.py` 文件：

```python
class DeepSeekConfig:
    def __init__(self):
        # 优先使用环境变量，否则使用默认值
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "sk-75db9bf464d44ee78b5d45a655431710")
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat"
        self.max_tokens = 2000
        self.temperature = 0.7
```

## 🚀 获取API密钥

### 1. 注册DeepSeek账户
1. 访问 [DeepSeek开放平台](https://platform.deepseek.com/)
2. 注册账户并完成验证
3. 登录到控制台

### 2. 创建API密钥
1. 在控制台中导航到"API密钥"页面
2. 点击"创建新密钥"
3. 设置密钥名称和权限
4. 复制生成的API密钥

### 3. 充值账户
1. 在控制台中导航到"余额"页面
2. 选择充值金额
3. 完成支付流程
4. 确认余额到账

## ⚙️ 配置参数说明

### 基础配置

| 参数 | 描述 | 默认值 | 说明 |
|------|------|--------|------|
| `api_key` | API密钥 | - | 从DeepSeek平台获取 |
| `base_url` | API基础URL | `https://api.deepseek.com/v1` | 通常不需要修改 |
| `model` | 使用的模型 | `deepseek-chat` | 推荐使用最新版本 |
| `max_tokens` | 最大生成token数 | `2000` | 控制报告长度 |
| `temperature` | 生成温度 | `0.7` | 控制创造性，0-1之间 |

### 高级配置

```python
class DeepSeekConfig:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "your_default_key")
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat"
        self.max_tokens = 2000
        self.temperature = 0.7
        
        # 请求超时设置
        self.timeout = 30
        
        # 重试设置
        self.max_retries = 3
        self.retry_delay = 1
        
        # 请求头设置
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
```

## 🔧 使用场景

### 1. 单文件分析

当上传单个代码文件时，系统会：
1. 使用传统工具进行基础检测
2. 将检测结果发送给DeepSeek API
3. 生成专业的自然语言分析报告

### 2. 项目分析

当上传项目文件时，系统会：
1. 扫描项目中的所有代码文件
2. 按语言分组进行分析
3. 生成项目级别的综合AI报告

### 3. 多语言分析

系统支持以下语言的AI分析：
- **Python**: 语法、逻辑、安全、性能问题
- **Java**: 空指针、内存泄漏、资源管理
- **C/C++**: 缓冲区溢出、内存泄漏、指针问题
- **JavaScript**: XSS、内存泄漏、异步问题
- **Go**: 并发安全、错误处理、性能优化

## 📊 AI报告特性

### 报告内容
- **总体评估**: 代码质量整体评价
- **主要问题分析**: 重点问题详细说明
- **改进建议**: 具体的修复建议
- **优先级排序**: 按重要性排序的问题列表

### 报告格式
- **Markdown格式**: 支持下载和分享
- **结构化内容**: 清晰的章节划分
- **专业术语**: 使用准确的技术语言
- **中文输出**: 便于理解的分析报告

## 🛠️ 故障排除

### 常见问题

#### 1. API密钥无效
**错误信息**: `401 Unauthorized`
**解决方案**:
- 检查API密钥是否正确
- 确认密钥是否已激活
- 验证密钥权限设置

#### 2. 余额不足
**错误信息**: `402 Insufficient Balance`
**解决方案**:
- 登录DeepSeek控制台检查余额
- 进行账户充值
- 系统会自动使用模拟报告作为备选

#### 3. 请求超时
**错误信息**: `TimeoutError`
**解决方案**:
- 检查网络连接
- 增加超时时间设置
- 减少max_tokens参数

#### 4. 模型不可用
**错误信息**: `404 Model Not Found`
**解决方案**:
- 检查模型名称是否正确
- 确认模型是否可用
- 更新到最新版本

### 调试模式

启用详细日志输出：

```python
import logging

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)

# 在API调用中添加日志
async def call_deepseek_api(prompt: str) -> str:
    try:
        print(f"🤖 调用DeepSeek API生成真实AI报告...")
        print(f"API密钥: {deepseek_config.api_key[:10]}...{deepseek_config.api_key[-10:]}")
        
        # API调用代码...
        
    except Exception as e:
        print(f"⚠️ 调用DeepSeek API失败: {e}")
        return generate_mock_ai_report(prompt)
```

## 📈 性能优化

### 1. 请求优化
- 合理设置`max_tokens`参数
- 使用适当的`temperature`值
- 避免频繁的API调用

### 2. 缓存策略
- 对相同内容的分析结果进行缓存
- 设置合理的缓存过期时间
- 避免重复分析相同文件

### 3. 并发控制
- 限制同时进行的API请求数量
- 使用队列管理请求
- 实现请求重试机制

## 🔒 安全考虑

### 1. API密钥安全
- 不要在代码中硬编码API密钥
- 使用环境变量存储敏感信息
- 定期轮换API密钥

### 2. 数据隐私
- 确保代码内容不会泄露
- 遵守数据保护法规
- 考虑使用本地模型作为备选

### 3. 访问控制
- 限制API访问频率
- 监控异常使用模式
- 实施适当的访问控制

## 📝 最佳实践

### 1. 配置管理
```python
# 推荐：使用环境变量
api_key = os.getenv("DEEPSEEK_API_KEY")

# 不推荐：硬编码密钥
api_key = "sk-1234567890abcdef"
```

### 2. 错误处理
```python
try:
    result = await call_deepseek_api(prompt)
    return result
except Exception as e:
    logger.error(f"AI分析失败: {e}")
    return generate_fallback_report()
```

### 3. 性能监控
```python
import time

start_time = time.time()
result = await call_deepseek_api(prompt)
end_time = time.time()

logger.info(f"AI分析耗时: {end_time - start_time:.2f}秒")
```

## 🔄 更新和维护

### 1. 定期检查
- 监控API使用情况
- 检查余额状态
- 更新模型版本

### 2. 配置备份
- 备份配置文件
- 记录配置变更
- 测试配置更新

### 3. 版本管理
- 跟踪API版本更新
- 测试新功能
- 更新文档

## 📞 技术支持

### DeepSeek官方支持
- [DeepSeek文档](https://platform.deepseek.com/docs)
- [API参考](https://platform.deepseek.com/api-docs)
- [社区论坛](https://community.deepseek.com/)

### 系统支持
- 查看系统日志
- 检查配置文件
- 联系系统维护者

---

*最后更新: 2024年*

