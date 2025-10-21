# vheer-2api ✨ - 将 Vheer 网站魔法封装为 OpenAI 格式 API

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/lzA6/vheer-2api/blob/main/LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg?logo=docker)](https://hub.docker.com/)
[![Tech Stack](https://img.shields.io/badge/stack-FastAPI%20%7C%20Playwright-orange.svg)](https://fastapi.tiangolo.com/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repo-green.svg?logo=github)](https://github.com/lzA6/vheer-2api)

> "任何足够先进的技术，都与魔法无异。" —— 亚瑟·克拉克

欢迎来到 `vheer-2api` 的世界！在这里，我们不只是编写代码，我们是在施展一种名为"自动化"的现代魔法。这个项目的核心思想非常纯粹：**如果一个服务只提供了精美的图形界面（UI），而没有提供程序接口（API），那我们就创造一个！**

我们相信，技术的价值在于赋能和连接。`vheer-2api` 就是这种信念的产物，它像一座桥梁，将 [Vheer](https://vheer.com) 强大的 AIGC 能力与广阔的 API 生态连接起来，让不计其数的应用、机器人、工作流都能轻松调用这份"魔法"。

## 🎯 项目概览

`vheer-2api` 是一个高性能代理服务，将 Vheer 网站的 AI 生成功能封装为标准化的 OpenAI API 格式。它使用无头浏览器模拟真实用户操作，让开发者能够通过熟悉的 API 接口调用 Vheer 的文生图、图生图、图生视频等功能。

### 🏗️ 系统架构

```mermaid
graph TB
    subgraph "客户端应用"
        A[Web应用] --> B[API调用]
        C[移动应用] --> B
        D[自动化脚本] --> B
        E[聊天机器人] --> B
    end

    subgraph "vheer-2api 服务层"
        B --> F[FastAPI Server]
        F --> G[认证中间件]
        G --> H[路由分发]
        
        H --> I[文生图 /v1/images/generations]
        H --> J[图生图 /v1/images/edits]
        H --> K[图生视频 /v1/video/generations]
        H --> L[模型列表 /v1/models]
        
        I --> M[Vheer Provider]
        J --> M
        K --> M
        L --> M
    end

    subgraph "浏览器自动化层"
        M --> N[Playwright Browser]
        N --> O[页面管理]
        O --> P[网络监听器]
        O --> Q[元素操作器]
        
        P --> R[结果捕获]
        Q --> S[用户模拟]
    end

    subgraph "目标服务"
        R --> T[Vheer.com]
        S --> T
        T --> U[🖼️ 生成图片]
        T --> V[🎬 生成视频]
    end

    subgraph "响应返回"
        U --> W[OpenAI格式封装]
        V --> W
        W --> X[JSON响应]
        X --> A
        X --> C
        X --> D
        X --> E
    end

    style A fill:#e1f5fe
    style F fill:#f3e5f5
    style M fill:#fff3e0
    style N fill:#e8f5e8
    style T fill:#ffebee
    style W fill:#f1f8e9
```

### ✨ 核心特性

| 功能模块 | 状态 | 描述 | API 端点 |
|---------|------|------|----------|
| 🖼️ 文生图 | ✅ 已完成 | 根据文本描述生成高质量图像 | `POST /v1/images/generations` |
| 🎨 图生图 | ✅ 已完成 | 基于参考图像进行风格转换和编辑 | `POST /v1/images/edits` |
| 🎬 图生视频 | ✅ 已完成 | 将静态图像转换为动态视频 | `POST /v1/video/generations` |
| 📋 模型列表 | ✅ 已完成 | 获取可用的 AI 模型信息 | `GET /v1/models` |
| 🐳 容器化部署 | ✅ 已完成 | Docker 一键部署 | - |
| 🧪 Web UI 测试 | ✅ 已完成 | 内置测试界面 | `GET /` |

## 🚀 快速开始

### 环境要求

- 🐳 Docker & Docker Compose
- 📦 Git
- 🌐 网络连接

### 3 步部署指南

**步骤 1: 获取项目代码**
```bash
git clone https://github.com/lzA6/vheer-2api.git
cd vheer-2api
```

**步骤 2: 配置身份凭证**

1. 登录 [Vheer.com](https://vheer.com)
2. 打开开发者工具 (F12) → 网络(Network)选项卡
3. 复制任意请求的 Cookie 值

![获取 Cookie 指南](https://i.postimg.cc/pXyG3YjD/cookie-guide.png)

4. 配置环境变量：
```bash
cp .env.example .env
nano .env  # 或使用你喜欢的编辑器
```

```env
# 配置文件示例
API_MASTER_KEY=sk-your-secret-key-here
NGINX_PORT=8088
VHEER_COOKIE="your-copied-cookie-value-here"
```

**步骤 3: 启动服务**
```bash
docker-compose up -d --build
```

服务启动后，访问 `http://localhost:8088` 即可使用 Web 测试界面！

## 🔧 API 使用指南

### 认证方式
所有 API 请求需要在 Header 中包含认证信息：
```http
Authorization: Bearer sk-your-secret-key-here
```

### 🖼️ 文生图 (Text-to-Image)
```bash
curl -X POST "http://localhost:8088/v1/images/generations" \
  -H "Authorization: Bearer sk-your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "一只戴着墨镜的酷猫，赛博朋克风格",
    "n": 1,
    "size": "1024x1024"
  }'
```

### 🎨 图生图 (Image-to-Image)
```bash
curl -X POST "http://localhost:8088/v1/images/edits" \
  -H "Authorization: Bearer sk-your-secret-key-here" \
  -F "image=@input.jpg" \
  -F "prompt=将这张照片转换为水彩画风格" \
  -F "n=1" \
  -F "size=1024x1024"
```

### 🎬 图生视频 (Image-to-Video)
```bash
curl -X POST "http://localhost:8088/v1/video/generations" \
  -H "Authorization: Bearer sk-your-secret-key-here" \
  -F "image=@input.jpg" \
  -F "prompt=让这张图像动起来，添加轻微的镜头移动效果"
```

## 🧠 技术深度解析

### 核心架构设计

```mermaid
flowchart TD
    A[客户端请求] --> B{API Gateway}
    B --> C[认证验证]
    C --> D[请求路由]
    
    D --> E[文生图处理器]
    D --> F[图生图处理器] 
    D --> G[图生视频处理器]
    D --> H[模型列表处理器]
    
    E --> I[任务队列]
    F --> I
    G --> I
    
    I --> J[浏览器管理器]
    J --> K[Playwright实例]
    K --> L[创建新页面]
    
    L --> M[配置网络监听]
    L --> N[导航到Vheer]
    
    N --> O[执行用户操作]
    O --> P[输入文本/上传图片]
    P --> Q[点击生成按钮]
    
    Q --> R[等待结果]
    R --> S{结果捕获策略}
    
    S --> T[主要策略<br>监听API响应]
    S --> U[备用策略<br>监听媒体请求]
    
    T --> V[解析JSON获取URL]
    U --> W[捕获媒体文件URL]
    
    V --> X[返回结果]
    W --> X
    
    X --> Y[清理资源]
    Y --> Z[返回客户端]
    
    style A fill:#4CAF50
    style B fill:#2196F3
    style J fill:#FF9800
    style K fill:#FF5722
    style S fill:#9C27B0
    style Z fill:#4CAF50
```

### 🎯 核心技术栈

| 技术组件 | 版本 | 用途 | 关键特性 |
|---------|------|------|----------|
| **FastAPI** | 0.104+ | API 服务器框架 | 🚀 高性能、🔧 类型提示、📚 自动文档 |
| **Playwright** | 1.40+ | 浏览器自动化 | 🌐 多浏览器支持、📡 网络拦截、⚡ 快速执行 |
| **Python** | 3.8+ | 后端编程语言 | 🐍 简洁语法、📦 丰富生态、🔗 异步支持 |
| **Docker** | 20.10+ | 容器化平台 | 📦 环境隔离、🔧 一键部署、⚖️ 资源控制 |
| **Pydantic** | 2.0+ | 数据验证 | ✅ 类型验证、🔒 数据安全、📝 自动文档 |

### 🔍 核心算法：智能结果捕获

```python
async def _wait_for_result_url(self, page: Page, timeout: int = 300) -> str:
    """
    智能结果捕获系统 - 双策略确保稳定获取生成结果
    """
    result_future = asyncio.Future()
    
    # 策略1: API响应监听（主要）
    async def handle_api_response(response: Response):
        if ("https://vheer.com/app/" in response.url and 
            response.request.method == "POST"):
            try:
                json_data = await response.json()
                if (json_data.get("message") == "Success" and 
                    json_data.get("status") == "success"):
                    download_urls = json_data.get("downloadUrls", [])
                    if download_urls and not result_future.done():
                        result_future.set_result(download_urls[0])
            except:
                pass
    
    # 策略2: 媒体文件监听（备用）
    async def handle_media_response(response: Response):
        if (response.request.method == "GET" and 
            "access.vheer.com/results/" in response.url and
            any(ext in response.url for ext in ['.jpg', '.png', '.mp4'])):
            if not result_future.done():
                result_future.set_result(response.url)
    
    # 注册监听器
    page.on("response", handle_api_response)
    page.on("response", handle_media_response)
    
    try:
        return await asyncio.wait_for(result_future, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError("生成超时，请重试")
```

### 📊 性能优化策略

| 优化领域 | 当前方案 | 未来优化 | 预期收益 |
|---------|----------|----------|----------|
| **并发处理** | 🔒 全局锁串行处理 | 🎯 浏览器上下文池 | 300% 吞吐量提升 |
| **资源复用** | 🔄 请求间复用浏览器 | 🔧 页面实例复用 | 50% 内存优化 |
| **网络监听** | 📡 双策略结果捕获 | 🎪 多事件源融合 | 99% 成功率 |
| **错误处理** | 🔄 基础重试机制 | 🧩 智能容错策略 | 自动恢复能力 |

## 🗂️ 项目结构

```
vheer-2api/
├── 📁 app/                          # 核心应用代码
│   ├── 📁 core/                     # 核心组件
│   │   ├── __init__.py
│   │   ├── config.py               # 🔧 配置管理
│   │   └── security.py             # 🔒 安全认证
│   ├── 📁 providers/               # 服务提供商
│   │   ├── __init__.py
│   │   ├── base_provider.py        # 🏗️ 提供商基类
│   │   └── vheer_provider.py       # 🎯 Vheer核心逻辑
│   └── 📁 utils/                   # 工具函数
│       └── sse_utils.py           # 📊 流式传输
├── 📁 static/                      # 静态资源
│   ├── index.html                 # 🧪 Web测试界面
│   ├── style.css                  # 🎨 样式文件
│   └── script.js                  # ⚡ 前端逻辑
├── 📄 main.py                     # 🚀 FastAPI主入口
├── 📄 requirements.txt            # 📦 Python依赖
├── 📄 Dockerfile                  # 🐳 容器构建
├── 📄 docker-compose.yml          # 🎯 编排配置
├── 📄 nginx.conf                  # 🌐 反向代理
├── 📄 .env.example                # 🔧 环境配置模板
└── 📄 README.md                   # 📚 项目文档
```

## 🎯 设计哲学

### 架构原则

1. **🔄 标准化接口**
   - 严格遵循 OpenAI API 规范
   - 提供一致的开发者体验
   - 兼容现有生态工具

2. **🛡️ 稳健性设计**
   - 双策略结果捕获机制
   - 完善的错误处理和重试
   - 资源泄漏防护

3. **⚡ 性能优化**
   - 异步非阻塞架构
   - 智能资源管理
   - 最小化浏览器开销

### 技术创新

```mermaid
graph LR
    A[传统爬虫] --> B[基于DOM解析]
    B --> C[易受前端变更影响]
    
    D[vheer-2api] --> E[基于网络监听]
    E --> F[监控API通信]
    F --> G[更高稳定性]
    E --> H[分析网络流量]
    H --> I[直接获取数据]
    
    style D fill:#4CAF50
    style G fill:#4CAF50
    style I fill:#4CAF50
    style A fill:#F44336
    style C fill:#F44336
```

## 🚧 限制与注意事项

### ⚠️ 当前限制

| 限制类型 | 描述 | 影响程度 | 解决方案 |
|---------|------|----------|----------|
| **并发性能** | 单实例串行处理 | 🟡 中等 | 部署多个实例负载均衡 |
| **资源消耗** | 浏览器实例内存占用 | 🟡 中等 | 优化浏览器配置 |
| **稳定性** | 依赖Vheer前端稳定性 | 🟡 中等 | 持续监控和适配 |
| **生成时间** | 比原生API稍慢 | 🟢 轻微 | 异步处理+进度反馈 |

### 🔮 路线图

**短期目标 (v1.1)**
- [ ] 浏览器上下文池实现
- [ ] 流式进度反馈
- [ ] 增强错误处理和重试
- [ ] 性能监控和指标

**中期目标 (v1.5)**
- [ ] 分布式浏览器集群
- [ ] 多账号负载均衡
- [ ] 插件化提供商架构
- [ ] 高级缓存策略

**长期愿景 (v2.0)**
- [ ] 通用 Web-UI 转 API 框架
- [ ] 可视化规则配置
- [ ] 机器学习辅助适配
- [ ] 企业级特性支持

## 🤝 贡献指南

我们欢迎各种形式的贡献！无论是代码改进、文档完善，还是功能建议，都是宝贵的贡献。

### 开发环境搭建

1. **环境准备**
```bash
git clone https://github.com/lzA6/vheer-2api.git
cd vheer-2api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **安装 Playwright 浏览器**
```bash
playwright install chromium
```

3. **开发模式启动**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8088
```

### 贡献流程

1. 🍴 Fork 项目
2. 🌿 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 💾 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 📤 推送到分支 (`git push origin feature/AmazingFeature`)
5. 🔔 开启 Pull Request

## 📞 支持与交流

- 🐛 **问题反馈**: [GitHub Issues](https://github.com/lzA6/vheer-2api/issues)
- 💡 **功能建议**: [GitHub Discussions](https://github.com/lzA6/vheer-2api/discussions)
- 📧 **联系维护者**: 通过 GitHub 直接联系

## 📄 许可证

本项目采用 Apache 2.0 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者，特别感谢：

- Vheer.com 提供的优质 AI 生成服务
- FastAPI 和 Playwright 团队提供的优秀工具
- 所有测试者和问题反馈者

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐️ Star 支持我们！**

> 🚀 去创造属于你的魔法吧！

</div>
