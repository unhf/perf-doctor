"""
绘制指标收集器

收集First Contentful Paint (FCP)、Largest Contentful Paint (LCP)等绘制相关指标
"""

from typing import Dict, Any, List
from ..base.collector import BaseCollector
from ...core.types import CollectorResult
from .fcp import FCPHelper
from .lcp import LCPHelper

class PaintCollector(BaseCollector):
    """绘制指标收集器"""
    def __init__(self, client):
        super().__init__(client, "PaintCollector", "收集绘制相关指标")
        self.fcp_helper = FCPHelper(client)
        self.lcp_helper = LCPHelper(client)
        self.paint_data = {}
    def get_required_domains(self) -> List[str]:
        return ["Performance"]
    async def setup(self) -> bool:
        try:
            await self._enable_required_domains()
            await self.lcp_helper.setup_lcp_observer()
            return True
        except Exception as e:
            self.logger.error(f"设置绘制收集器失败: {e}")
            return False
    async def collect(self) -> CollectorResult:
        try:
            fcp_data = await self.fcp_helper.collect_fcp()
            if fcp_data:
                self.paint_data.update(fcp_data)
            lcp_data = await self.lcp_helper.collect_lcp()
            if lcp_data:
                self.paint_data.update(lcp_data)
            return self._create_result(self.paint_data)
        except Exception as e:
            self.logger.error(f"收集绘制数据失败: {e}")
            return self._create_result({}, str(e)) 