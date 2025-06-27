"""
性能诊断器配置文件

包含默认配置和可自定义的参数
"""

import os

# Chrome 配置
CHROME_CONFIG = {
    "path": None,  # Chrome 可执行文件路径，None 时自动检测
    "debug_port": 9222,  # 调试端口
    "headless": False,  # 是否无头模式
    "extra_args": [  # 额外启动参数
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor",
        "--no-sandbox",
    ]
}

# 性能测试配置
PERFORMANCE_CONFIG = {
    "wait_time": 5,  # 页面加载等待时间（秒）
    "timeout": 30,   # 单页面分析超时时间（秒）
    "concurrent": 1, # 并发分析数量
}

# 默认测试 URLs
DEFAULT_TEST_URLS = [
    "https://www.google.com",
    "https://www.github.com",
    "https://www.stackoverflow.com",
]

# 性能阈值配置（毫秒）
PERFORMANCE_THRESHOLDS = {
    "fcp": {"good": 1800, "poor": 3000},      # First Contentful Paint
    "lcp": {"good": 2500, "poor": 4000},      # Largest Contentful Paint
    "ttfb": {"good": 200, "poor": 600},       # Time to First Byte
    "dom_ready": {"good": 2000, "poor": 4000}, # DOM Ready
    "page_load": {"good": 3000, "poor": 5000}  # Page Load
}

# 报告配置
REPORT_CONFIG = {
    "output_dir": "reports",  # 报告输出目录
    "save_json": True,        # 保存 JSON 格式
    "save_text": True,        # 保存文本格式
    "include_raw_data": True, # 包含原始数据
}

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",  # 日志级别: DEBUG, INFO, WARNING, ERROR
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": None,     # 日志文件路径，None 时只输出到控制台
}

# 环境变量覆盖
def get_config_value(config_dict: dict, key: str, env_prefix: str = "PERF_DOCTOR"):
    """
    从环境变量获取配置值，如果不存在则使用默认值
    
    Args:
        config_dict: 配置字典
        key: 配置键名
        env_prefix: 环境变量前缀
    
    Returns:
        配置值
    """
    env_key = f"{env_prefix}_{key.upper()}"
    env_value = os.getenv(env_key)
    
    if env_value is not None:
        # 尝试转换类型
        original_value = config_dict.get(key)
        if isinstance(original_value, bool):
            return env_value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(original_value, int):
            try:
                return int(env_value)
            except ValueError:
                pass
        elif isinstance(original_value, float):
            try:
                return float(env_value)
            except ValueError:
                pass
        return env_value
    
    return config_dict.get(key)

# 应用环境变量覆盖
def apply_env_overrides():
    """应用环境变量覆盖到配置"""
    # Chrome 配置
    CHROME_CONFIG["path"] = get_config_value(CHROME_CONFIG, "path", "PERF_DOCTOR_CHROME")
    CHROME_CONFIG["debug_port"] = get_config_value(CHROME_CONFIG, "debug_port", "PERF_DOCTOR_CHROME")
    CHROME_CONFIG["headless"] = get_config_value(CHROME_CONFIG, "headless", "PERF_DOCTOR_CHROME")
    
    # 性能配置
    PERFORMANCE_CONFIG["wait_time"] = get_config_value(PERFORMANCE_CONFIG, "wait_time", "PERF_DOCTOR_PERF")
    PERFORMANCE_CONFIG["timeout"] = get_config_value(PERFORMANCE_CONFIG, "timeout", "PERF_DOCTOR_PERF")
    PERFORMANCE_CONFIG["concurrent"] = get_config_value(PERFORMANCE_CONFIG, "concurrent", "PERF_DOCTOR_PERF")
    
    # 报告配置
    REPORT_CONFIG["output_dir"] = get_config_value(REPORT_CONFIG, "output_dir", "PERF_DOCTOR_REPORT")
    
    # 日志配置
    LOGGING_CONFIG["level"] = get_config_value(LOGGING_CONFIG, "level", "PERF_DOCTOR_LOG")
    LOGGING_CONFIG["file"] = get_config_value(LOGGING_CONFIG, "file", "PERF_DOCTOR_LOG")

# 初始化时应用环境变量
apply_env_overrides()
