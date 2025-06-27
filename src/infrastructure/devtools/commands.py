"""
DevTools命令定义模块

定义所有DevTools命令的常量和方法
"""

from typing import Dict, Any, Optional


class DevToolsCommands:
    """DevTools命令定义"""
    
    # 域启用命令
    PERFORMANCE_ENABLE = "Performance.enable"
    NETWORK_ENABLE = "Network.enable"
    RUNTIME_ENABLE = "Runtime.enable"
    PAGE_ENABLE = "Page.enable"
    
    # 页面命令
    PAGE_NAVIGATE = "Page.navigate"
    PAGE_GET_RESPONSE_BODY = "Network.getResponseBody"
    
    # 运行时命令
    RUNTIME_EVALUATE = "Runtime.evaluate"
    
    # 性能命令
    PERFORMANCE_GET_METRICS = "Performance.getMetrics"
    
    @staticmethod
    def enable_domain(domain: str) -> Dict[str, Any]:
        """启用域命令"""
        return {
            "method": f"{domain}.enable",
            "params": {}
        }
    
    @staticmethod
    def navigate_to(url: str) -> Dict[str, Any]:
        """导航命令"""
        return {
            "method": "Page.navigate",
            "params": {"url": url}
        }
    
    @staticmethod
    def execute_javascript(expression: str, return_by_value: bool = True) -> Dict[str, Any]:
        """执行JavaScript命令"""
        return {
            "method": "Runtime.evaluate",
            "params": {
                "expression": expression,
                "returnByValue": return_by_value
            }
        }
    
    @staticmethod
    def get_response_body(request_id: str) -> Dict[str, Any]:
        """获取响应体命令"""
        return {
            "method": "Network.getResponseBody",
            "params": {"requestId": request_id}
        }
    
    @staticmethod
    def get_performance_metrics() -> Dict[str, Any]:
        """获取性能指标命令"""
        return {
            "method": "Performance.getMetrics",
            "params": {}
        }
    
    @staticmethod
    def enable_network_tracking() -> Dict[str, Any]:
        """启用网络跟踪命令"""
        return {
            "method": "Network.enable",
            "params": {}
        }
    
    @staticmethod
    def enable_page_tracking() -> Dict[str, Any]:
        """启用页面跟踪命令"""
        return {
            "method": "Page.enable",
            "params": {}
        }
    
    @staticmethod
    def enable_runtime_tracking() -> Dict[str, Any]:
        """启用运行时跟踪命令"""
        return {
            "method": "Runtime.enable",
            "params": {}
        } 