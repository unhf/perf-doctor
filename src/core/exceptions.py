"""
异常定义模块

定义项目中使用的所有异常类型
"""


class PerfDoctorException(Exception):
    """性能医生基础异常"""
    pass


class CollectorException(PerfDoctorException):
    """收集器异常"""
    pass


class AnalysisException(PerfDoctorException):
    """分析异常"""
    pass


class ReportException(PerfDoctorException):
    """报告生成异常"""
    pass


class ChromeException(PerfDoctorException):
    """Chrome相关异常"""
    pass


class DevToolsException(PerfDoctorException):
    """DevTools通信异常"""
    pass


class ConfigException(PerfDoctorException):
    """配置异常"""
    pass


class NetworkException(PerfDoctorException):
    """网络相关异常"""
    pass


class TimeoutException(PerfDoctorException):
    """超时异常"""
    pass


class ValidationException(PerfDoctorException):
    """数据验证异常"""
    pass 