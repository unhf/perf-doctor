# 🔍 Chrome Performance Doctor

<div align="center">

**一个基于 Python 的智能网页性能分析工具**

*通过 WebSocket 连接 Chrome DevTools，自动分析页面性能指标并生成详细报告*

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Chrome](https://img.shields.io/badge/Chrome-DevTools-orange.svg)](https://developer.chrome.com/docs/devtools/)
[![Version](https://img.shields.io/badge/Version-1.0.0-brightgreen.svg)](https://github.com)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)](https://github.com)

</div>

---

## 🎬 效果演示

<div align="center">

```
🔍 Chrome Performance Doctor 分析报告
============================================================
总页面数: 1
成功分析: 1
失败分析: 0

📊 [1] https://httpbin.org/json
    总体评分: 84.6/100
    ✅ FCP: 1308ms (good)
    ⚠️ TTFB: 506ms (needs_improvement)
    ✅ DOM_READY: 1281ms (good)
    ✅ PAGE_LOAD: 1282ms (good)
    🔴 高优先级问题: 1 项
       • Time to First Byte: 首字节时间为 506ms，服务器响应较慢

✅ 分析完成! 📁 报告已保存到 reports/ 目录
```

</div>

---

## ✨ 特性

| 特性 | 描述 |
|------|------|
| 🚀 **自动化分析** | 无需手动操作，自动打开页面并收集性能数据 |
| 📊 **全面指标** | 支持 FCP、LCP、TTFB、DOM Ready、Page Load 等关键指标 |
| 📈 **智能评分** | 基于 Web Vitals 标准的自动评分系统 |
| 💡 **优化建议** | 针对性能问题提供具体的优化建议 |
| 🔄 **批量测试** | 支持同时分析多个页面 |
| 📁 **多格式报告** | 生成 JSON 和文本格式的详细报告 |
| 🌐 **兼容性强** | 支持现有 Chrome 实例，不会干扰正常浏览 |

## 🛠 系统要求

- **Python**: 3.7+
- **浏览器**: Google Chrome 或 Chromium
- **系统**: macOS、Windows 或 Linux## 📦 安装

### 方式一：使用 Pipenv（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd perf-doctor

# 2. 安装 Pipenv（如果未安装）
pip install pipenv

# 3. 安装项目依赖
pipenv install

# 4. 激活虚拟环境
pipenv shell
```

### 方式二：直接使用 pip

```bash
# 克隆项目
git clone <repository-url>
cd perf-doctor

# 安装依赖
pip install websockets==12.0 requests==2.31.0 psutil==5.9.8
```## 🚀 快速开始

### 基本用法

```bash
# 使用默认 URL 进行测试
python core/main.py

# 测试单个页面
python core/main.py https://www.example.com

# 测试多个页面
python core/main.py https://www.google.com https://www.github.com https://www.stackoverflow.com
```

### 在 Pipenv 环境中运行

```bash
pipenv run python core/main.py https://www.example.com
```

### 🎯 高级用法示例

```python
# API 使用示例
import asyncio
from modules.performance_doctor import PerformanceDoctor

async def analyze_my_site():
    with PerformanceDoctor() as doctor:
        result = await doctor.analyze_page("https://example.com")
        print(f"性能评分: {result['overall_score']:.1f}/100")

asyncio.run(analyze_my_site())
```## ⚙️ 配置

### 文件配置

编辑 `config.py` 文件来自定义配置：

```python
# Chrome 配置
CHROME_CONFIG = {
    "path": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "debug_port": 9222,
    "headless": False,
}

# 性能测试配置
PERFORMANCE_CONFIG = {
    "wait_time": 5,    # 页面加载等待时间（秒）
    "timeout": 30,     # 单页面分析超时时间（秒）
    "concurrent": 1,   # 并发分析数量
}

# 默认测试 URLs
DEFAULT_TEST_URLS = [
    "https://www.google.com",
    "https://www.github.com",
    # 添加更多 URL...
]
```

### 环境变量配置

```bash
# Chrome 配置
export PERF_DOCTOR_CHROME_PATH="/path/to/chrome"
export PERF_DOCTOR_CHROME_DEBUG_PORT=9222
export PERF_DOCTOR_CHROME_HEADLESS=false

# 性能配置
export PERF_DOCTOR_PERF_WAIT_TIME=5
export PERF_DOCTOR_PERF_TIMEOUT=30
export PERF_DOCTOR_PERF_CONCURRENT=1

# 报告配置
export PERF_DOCTOR_REPORT_OUTPUT_DIR="./reports"

# 日志配置
export PERF_DOCTOR_LOG_LEVEL="INFO"
export PERF_DOCTOR_LOG_FILE="./perf-doctor.log"
```

## 📊 输出示例

### 控制台输出

<details>
<summary>点击查看详细输出示例</summary>

```
🔍 Chrome Performance Doctor 分析报告
============================================================
总页面数: 3
成功分析: 3
失败分析: 0

📊 [1] https://www.google.com
    总体评分: 85.2/100
    ✅ FCP: 1200ms (good)
    ✅ LCP: 1800ms (good)
    ⚠️ TTFB: 250ms (needs_improvement)
    ✅ DOM_READY: 1500ms (good)
    ✅ PAGE_LOAD: 2100ms (good)

📊 [2] https://www.github.com
    总体评分: 72.8/100
    ⚠️ FCP: 2100ms (needs_improvement)
    ❌ LCP: 4200ms (poor)
    ✅ TTFB: 180ms (good)
    ⚠️ DOM_READY: 2800ms (needs_improvement)
    ⚠️ PAGE_LOAD: 3600ms (needs_improvement)
    🔴 高优先级问题: 1 项
       • Largest Contentful Paint: 最大内容绘制时间为 4200ms，需要优化

📈 汇总统计
========================================
平均评分: 79.0/100
评级分布:
  ✅ 优秀 (≥80分): 1 个
  ⚠️  一般 (50-79分): 2 个
  ❌ 较差 (<50分): 0 个

💾 保存报告到: reports

✅ 分析完成!
```

</details>

### 📁 报告文件

生成的报告保存在 `reports/` 目录下：

| 文件类型 | 格式 | 描述 |
|----------|------|------|
| `report_1_YYYYMMDD_HHMMSS.json` | JSON | 详细的结构化数据报告 |
| `report_1_YYYYMMDD_HHMMSS.txt` | 文本 | 可读性强的格式化报告 |
| `summary_YYYYMMDD_HHMMSS.json` | JSON | 批量分析汇总报告 |

## 🏗 架构设计

<div align="center">

```
┌─────────────────────────────────────────────────────────┐
│                 Performance Doctor                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │ Chrome      │  │ DevTools     │  │ Performance     │ │
│  │ Manager     │◄─┤ Client       │◄─┤ Collector       │ │
│  └─────────────┘  └──────────────┘  └─────────────────┘ │
│         │                                   │           │
│         ▼                                   ▼           │
│  ┌─────────────┐                   ┌─────────────────┐  │
│  │ Report      │◄──────────────────┤ Main Controller │  │
│  │ Generator   │                   │                 │  │
│  └─────────────┘                   └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

</div>

### 📁 项目结构

```
perf-doctor/
├── 📁 modules/                    # 核心模块目录
│   ├── 🔧 chrome_manager.py       # Chrome 进程管理
│   ├── 🌐 devtools_client.py      # DevTools WebSocket 客户端
│   ├── 📊 performance_collector.py # 性能数据收集
│   ├── 📋 report_generator.py     # 报告生成与分析
│   └── 🎯 performance_doctor.py   # 主分析控制器
├── 📄 core/main.py               # 主程序入口
├── ⚙️ config.py                  # 配置文件
├── 📚 examples.py                # 使用示例
├── 🧪 test_modules.py            # 模块测试
└── 📁 reports/                   # 生成的报告文件
```

### 🧩 核心模块

<table>
<tr>
<td width="30%"><strong>🔧 ChromeManager</strong></td>
<td>负责 Chrome 进程管理，包括启动、检测现有实例、创建/关闭标签页</td>
</tr>
<tr>
<td><strong>🌐 DevToolsClient</strong></td>
<td>WebSocket 客户端，处理与 Chrome DevTools 的通信</td>
</tr>
<tr>
<td><strong>📊 PerformanceCollector</strong></td>
<td>收集各种性能指标，包括 Paint Timing、Navigation Timing 等</td>
</tr>
<tr>
<td><strong>📋 ReportGenerator</strong></td>
<td>分析性能数据，计算评分，生成优化建议</td>
</tr>
<tr>
<td><strong>🎯 PerformanceDoctor</strong></td>
<td>主控制器，整合所有组件完成完整的分析流程</td>
</tr>
</table>

## 📈 性能指标说明

### 🎯 核心指标

<table>
<thead>
<tr>
<th width="25%">指标</th>
<th width="40%">说明</th>
<th width="35%">评分标准</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>🎨 FCP</strong><br><small>First Contentful Paint</small></td>
<td>首次内容绘制时间<br>页面首次渲染内容的时间</td>
<td>
✅ 优秀: ≤ 1.8s<br>
⚠️ 需要改进: 1.8s - 3.0s<br>
❌ 较差: > 3.0s
</td>
</tr>
<tr>
<td><strong>🖼 LCP</strong><br><small>Largest Contentful Paint</small></td>
<td>最大内容绘制时间<br>最大内容元素的渲染时间</td>
<td>
✅ 优秀: ≤ 2.5s<br>
⚠️ 需要改进: 2.5s - 4.0s<br>
❌ 较差: > 4.0s
</td>
</tr>
<tr>
<td><strong>⚡ TTFB</strong><br><small>Time to First Byte</small></td>
<td>首字节时间<br>服务器响应第一个字节的时间</td>
<td>
✅ 优秀: ≤ 200ms<br>
⚠️ 需要改进: 200ms - 600ms<br>
❌ 较差: > 600ms
</td>
</tr>
<tr>
<td><strong>📄 DOM Ready</strong><br><small>DOM Content Loaded</small></td>
<td>DOM 准备时间<br>HTML 文档完全加载和解析的时间</td>
<td>
✅ 优秀: ≤ 2.0s<br>
⚠️ 需要改进: 2.0s - 4.0s<br>
❌ 较差: > 4.0s
</td>
</tr>
<tr>
<td><strong>🏁 Page Load</strong><br><small>Load Event</small></td>
<td>页面完整加载时间<br>所有资源加载完成的时间</td>
<td>
✅ 优秀: ≤ 3.0s<br>
⚠️ 需要改进: 3.0s - 5.0s<br>
❌ 较差: > 5.0s
</td>
</tr>
</tbody>
</table>

## 🤔 常见问题

<details>
<summary><strong>❓ Chrome 启动失败</strong></summary>

**问题**: 程序提示 "Chrome 启动失败"

**解决方案**:
- 确保系统中安装了 Chrome 或 Chromium 浏览器
- 在配置文件中指定正确的 Chrome 路径
- 检查 Chrome 是否被其他进程占用

</details>

<details>
<summary><strong>❓ 连接 DevTools 失败</strong></summary>

**问题**: 无法连接到 Chrome DevTools

**解决方案**:
- 检查调试端口（默认 9222）是否被其他程序占用
- 在配置中修改为其他可用端口
- 确保防火墙没有阻止本地连接

</details>

<details>
<summary><strong>❓ 页面分析超时</strong></summary>

**问题**: 分析过程中出现超时错误

**解决方案**:
- 增加 `PERFORMANCE_CONFIG["wait_time"]` 的值
- 检查网络连接是否稳定
- 尝试分析更简单的页面进行测试

</details>

<details>
<summary><strong>❓ 权限问题</strong></summary>

**问题**: 在某些系统中遇到权限错误

**解决方案**:
- 在 macOS/Linux 中使用 `sudo` 运行（不推荐）
- 调整 Chrome 启动参数，添加 `--no-sandbox`
- 使用非管理员账户运行 Chrome

</details>

## 🛠 开发指南

### 添加新的性能指标

1. **在 `PerformanceCollector` 中添加收集逻辑**
   ```python
   async def _collect_new_metric(self):
       # 实现新指标的收集逻辑
       pass
   ```

2. **在 `ReportGenerator` 中添加阈值和评分计算**
   ```python
   # 在配置中添加新阈值
   "new_metric": {"good": 100, "poor": 300}
   ```

3. **更新配置文件中的阈值设置**

### 自定义报告格式

```python
from modules.report_generator import ReportGenerator

class CustomReportGenerator(ReportGenerator):
    def format_report_text(self, report):
        # 自定义报告格式
        return custom_formatted_text
```

### 贡献代码

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

<div align="center">

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证

## 🤝 贡献

欢迎提交 [Issue](../../issues) 和 [Pull Request](../../pulls)！

**如果这个项目对你有帮助，请给个 ⭐ Star！**

</div>
