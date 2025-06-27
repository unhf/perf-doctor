# Chrome Performance Doctor 配置文件

# Chrome调试端口
CHROME_DEBUG_PORT = 9222

# 要测试的URL列表
TEST_URLS = [
    "https://www.baidu.com",
    "https://www.google.com",
    # 添加更多URL...
]

# 性能阈值配置 (单位: 毫秒)
PERFORMANCE_THRESHOLDS = {
    'page_load_time': {
        'excellent': 1000,  # < 1秒为优秀
        'good': 3000        # 1-3秒为良好，>3秒需要优化
    },
    'first_paint_time': {
        'excellent': 1000,  # < 1秒为优秀
        'good': 2000        # 1-2秒为良好，>2秒需要优化
    },
    'first_contentful_paint': {
        'excellent': 1500,  # < 1.5秒为优秀
        'good': 2500        # 1.5-2.5秒为良好，>2.5秒需要优化
    }
}

# Chrome启动参数
CHROME_ARGS = [
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-extensions',
    '--disable-plugins',
    '--disable-default-apps',
    '--disable-background-timer-throttling',
    '--disable-renderer-backgrounding',
    '--disable-backgrounding-occluded-windows'
]

# 报告输出配置
REPORT_CONFIG = {
    'save_to_file': True,
    'file_name': 'performance_report.txt',
    'include_detailed_metrics': True,
    'include_recommendations': True
}
