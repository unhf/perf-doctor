# Chrome Performance Doctor

一个用于分析网页性能的Python工具，通过WebSocket连接Chrome DevTools来收集和评估页面性能数据。

## 功能特性

- 🚀 自动启动Chrome浏览器并开启调试模式
- 🔌 通过WebSocket连接Chrome DevTools
- 📊 收集详细的页面性能指标
- 📈 生成性能评估报告
- ⚙️ 可配置的性能阈值和测试URL
- 📝 自动保存性能报告到文件

## 安装依赖

确保您已安装Pipenv，然后运行：

```bash
pipenv install
```

## 使用方法

### 1. 基本使用

```bash
# 运行性能分析
./runner.sh
```

或者直接运行：

```bash
pipenv run python core/main.py
```

### 2. 配置测试URL

编辑 `config.py` 文件，修改 `TEST_URLS` 列表：

```python
TEST_URLS = [
    "https://www.example.com",
    "https://www.github.com",
    # 添加更多URL...
]
```

### 3. 自定义性能阈值

在 `config.py` 中调整性能阈值：

```python
PERFORMANCE_THRESHOLDS = {
    'page_load_time': {
        'excellent': 1000,  # < 1秒为优秀
        'good': 3000        # 1-3秒为良好
    },
    # ... 其他阈值
}
```

## 性能指标说明

工具会收集以下关键性能指标：

- **页面加载时间**: 从导航开始到页面完全加载完成的时间
- **DOM就绪时间**: DOM内容加载完成的时间
- **首字节时间**: 从请求发出到接收到第一个字节的时间
- **DNS查询时间**: DNS解析所用的时间
- **TCP连接时间**: 建立TCP连接所用的时间
- **首次绘制时间**: 浏览器首次绘制内容的时间
- **首次内容绘制时间**: 浏览器首次绘制文本或图像的时间
- **内存使用情况**: JavaScript堆内存的使用情况

## 性能评估标准

- ✅ **优秀**: 指标在最佳范围内
- ⚠️ **良好**: 指标在可接受范围内
- ❌ **需要优化**: 指标超出推荐范围，建议优化

## 系统要求

- macOS (其他系统需要修改Chrome路径)
- Python 3.8+
- Google Chrome浏览器
- 网络连接

## 注意事项

1. 工具会自动启动Chrome浏览器，请确保Chrome已正确安装
2. 如果Chrome已在运行，工具会尝试连接到现有的调试端口
3. 性能数据会受到网络状况、系统负载等因素影响
4. 建议在相同环境下多次测试以获得更准确的结果

## 故障排除

### Chrome启动失败
- 检查Chrome是否正确安装在 `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- 确保端口9222未被其他程序占用

### WebSocket连接失败
- 确保Chrome调试端口正常开启
- 检查防火墙设置
- 尝试重启Chrome浏览器

### 性能数据收集异常
- 确保目标网站可正常访问
- 检查网络连接是否稳定
- 某些网站可能有反爬虫机制

## 项目结构

```
perf-doctor/
├── Pipfile              # Pipenv依赖配置
├── Pipfile.lock         # 锁定的依赖版本
├── runner.sh            # 运行脚本
├── config.py            # 配置文件
├── core/
│   └── main.py          # 主程序
└── README.md           # 说明文档
```

## 贡献

欢迎提交Issue和Pull Request来改进这个工具！
