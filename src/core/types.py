"""
类型定义模块

定义项目中使用的数据类型
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PerformanceData:
    """性能数据"""
    url: str
    timestamp: float
    load_time: int
    fcp: Optional[float] = None
    lcp: Optional[float] = None
    fid: Optional[float] = None
    cls: Optional[float] = None
    ttfb: Optional[float] = None
    dom_ready: Optional[float] = None
    page_load: Optional[float] = None


@dataclass
class NetworkRequest:
    """网络请求"""
    request_id: str
    url: str
    method: str
    status: int
    mime_type: str
    transfer_size: int
    response_time: float
    request_headers: Dict[str, str] = field(default_factory=dict)
    response_headers: Dict[str, str] = field(default_factory=dict)
    request_body: str = ""
    response_body: str = ""
    error_text: str = ""
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    domain: str = ""
    is_static: bool = False
    is_api: bool = False
    is_third_party: bool = False
    category: str = "Other"


@dataclass
class NetworkData:
    """网络数据"""
    statistics: Dict[str, Any]
    resources: List[NetworkRequest]
    analysis: Dict[str, List[NetworkRequest]]


@dataclass
class MemoryData:
    """内存数据"""
    used_js_heap_size: int
    total_js_heap_size: int
    js_heap_size_limit: int
    heap_usage_percent: float


@dataclass
class NavigationData:
    """导航数据"""
    navigation_start: int
    fetch_start: int
    domain_lookup_start: int
    domain_lookup_end: int
    connect_start: int
    connect_end: int
    request_start: int
    response_start: int
    response_end: int
    dom_loading: int
    dom_interactive: int
    dom_content_loaded_event_start: int
    dom_content_loaded_event_end: int
    dom_complete: int
    load_event_start: int
    load_event_end: int
    dns_lookup: int
    tcp_connect: int
    ttfb: int
    dom_ready: int
    page_load: int
    navigation_type: int
    redirect_count: int


@dataclass
class PaintData:
    """绘制数据"""
    first_paint: Optional[float] = None
    first_contentful_paint: Optional[float] = None
    largest_contentful_paint: Optional[float] = None


@dataclass
class CollectorResult:
    """收集器结果"""
    type: str
    data: Dict[str, Any]
    timestamp: float
    error: Optional[str] = None


@dataclass
class AnalysisResult:
    """分析结果"""
    key_metrics: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    issues: List[Dict[str, Any]]
    score: float


@dataclass
class ReportData:
    """报告数据"""
    url: str
    timestamp: float
    performance_data: PerformanceData
    network_data: NetworkData
    memory_data: MemoryData
    navigation_data: NavigationData
    paint_data: PaintData
    analysis_result: AnalysisResult
    collector_results: Dict[str, CollectorResult]


@dataclass
class ReportOptions:
    """报告选项"""
    output_format: str = "html"  # html, json
    output_dir: str = "reports"
    include_response_body: bool = True
    max_response_size: int = 1024 * 1024
    template_name: str = "default" 