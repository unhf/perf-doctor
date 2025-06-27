# 项目结构说明

```
perf-doctor/
├── Pipfile                    # Python 依赖管理文件
├── Pipfile.lock              # 锁定的依赖版本
├── README.md                 # 项目说明文档
├── config.py                 # 配置文件（阈值、Chrome参数等）
├── examples.py               # API使用示例
├── test_modules.py           # 模块测试脚本
├── core/
│   └── main.py              # 主程序入口
├── modules/                  # 核心模块目录
│   ├── __init__.py          # 模块包初始化
│   ├── chrome_manager.py    # Chrome进程管理
│   ├── devtools_client.py   # DevTools WebSocket客户端
│   ├── performance_collector.py  # 性能数据收集
│   ├── report_generator.py  # 报告生成与分析
│   └── performance_doctor.py     # 主分析控制器
└── reports/                  # 生成的报告文件目录
    ├── *.json               # JSON格式详细报告
    └── *.txt                # 文本格式可读报告
```

## 模块功能说明

### 1. ChromeManager (`modules/chrome_manager.py`)
- **功能**: Chrome 进程生命周期管理
- **主要方法**:
  - `start_chrome()`: 启动Chrome实例或连接现有实例
  - `create_new_tab()`: 创建新标签页
  - `close_tab()`: 关闭指定标签页
  - `cleanup()`: 清理资源，关闭Chrome进程

### 2. DevToolsClient (`modules/devtools_client.py`)
- **功能**: WebSocket通信与DevTools命令处理
- **主要方法**:
  - `connect()`: 建立WebSocket连接
  - `send_command()`: 发送DevTools命令
  - `enable_domain()`: 启用DevTools域
  - `navigate_to()`: 页面导航
  - `execute_javascript()`: 执行JavaScript代码

### 3. PerformanceCollector (`modules/performance_collector.py`)
- **功能**: 收集和解析页面性能数据
- **主要方法**:
  - `collect_performance_data()`: 收集完整性能数据
  - `_collect_paint_metrics()`: 收集绘制相关指标
  - `_collect_navigation_timing()`: 收集导航时序数据
  - `get_memory_usage()`: 获取内存使用情况

### 4. ReportGenerator (`modules/report_generator.py`)
- **功能**: 性能数据分析与报告生成
- **主要方法**:
  - `generate_report()`: 生成完整性能报告
  - `_calculate_scores()`: 计算性能评分
  - `_generate_recommendations()`: 生成优化建议
  - `format_report_text()`: 格式化文本报告
  - `save_report()`: 保存报告到文件

### 5. PerformanceDoctor (`modules/performance_doctor.py`)
- **功能**: 主控制器，整合所有组件
- **主要方法**:
  - `analyze_page()`: 分析单个页面
  - `analyze_multiple_pages()`: 批量分析页面
  - `generate_summary_report()`: 生成汇总报告
  - `save_reports()`: 批量保存报告

## 配置文件 (`config.py`)

包含以下配置项：
- `CHROME_CONFIG`: Chrome启动配置
- `PERFORMANCE_CONFIG`: 性能测试配置
- `DEFAULT_TEST_URLS`: 默认测试URL列表
- `PERFORMANCE_THRESHOLDS`: 性能阈值定义
- `REPORT_CONFIG`: 报告输出配置
- `LOGGING_CONFIG`: 日志配置

## 使用方式

### 1. 命令行使用
```bash
# 使用默认URL测试
python core/main.py

# 测试指定URL
python core/main.py https://www.example.com

# 批量测试
python core/main.py https://site1.com https://site2.com
```

### 2. API使用
```python
from modules.performance_doctor import PerformanceDoctor

async def analyze():
    with PerformanceDoctor() as doctor:
        result = await doctor.analyze_page("https://example.com")
        print(f"评分: {result['overall_score']}")
```

### 3. 环境变量配置
```bash
export PERF_DOCTOR_CHROME_PATH="/path/to/chrome"
export PERF_DOCTOR_PERF_WAIT_TIME=10
export PERF_DOCTOR_REPORT_OUTPUT_DIR="./my_reports"
```

## 特色功能

1. **模块化设计**: 每个组件职责单一，便于维护和扩展
2. **详细注释**: 所有关键函数都有详细的文档字符串
3. **配置灵活**: 支持文件配置和环境变量覆盖
4. **错误处理**: 完善的异常处理和资源清理
5. **多格式输出**: 同时生成JSON和文本格式报告
6. **智能评分**: 基于Web Vitals标准的性能评分
7. **优化建议**: 针对性能问题提供具体改进建议

## 代码特点

- **精简**: 主程序仅140行，每个模块功能聚焦
- **注释详细**: 代码注释占比超过40%
- **类型提示**: 使用Python类型注解提高代码可读性
- **异步编程**: 使用asyncio提高并发性能
- **上下文管理**: 支持with语句自动资源管理
