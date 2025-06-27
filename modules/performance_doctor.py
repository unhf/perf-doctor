"""
性能诊断器主模块

整合所有组件，提供完整的页面性能分析功能
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from .chrome_manager import ChromeManager
from .devtools_client import DevToolsClient
from .performance_collector import PerformanceCollector
from .report_generator import ReportGenerator

class PerformanceDoctor:
    """页面性能诊断器"""
    
    def __init__(self, chrome_path: Optional[str] = None, debug_port: int = 9222,
                 inherit_cookies: bool = True, user_data_dir: Optional[str] = None):
        """
        初始化性能诊断器
        
        Args:
            chrome_path: Chrome 可执行文件路径
            debug_port: Chrome 调试端口
            inherit_cookies: 是否继承现有 Chrome 的 cookies
            user_data_dir: 用户数据目录，None 时自动检测或创建
        """
        self.chrome_manager = ChromeManager(chrome_path, debug_port, inherit_cookies, user_data_dir)
        self.report_generator = ReportGenerator()
        self.logger = logging.getLogger(__name__)
        
        # 运行时组件
        self.devtools_client = None
        self.performance_collector = None
        self.current_tab = None
    
    async def analyze_page(self, url: str, wait_time: int = 5) -> Dict[str, Any]:
        """
        分析单个页面的性能
        
        Args:
            url: 目标页面URL
            wait_time: 页面加载等待时间（秒）
            
        Returns:
            性能分析报告
        """
        self.logger.info(f"开始分析页面: {url}")
        
        try:
            # 1. 启动 Chrome（如果需要）
            if not self.chrome_manager.start_chrome():
                raise Exception("Chrome 启动失败")
            
            # 2. 创建新标签页
            self.current_tab = self.chrome_manager.create_new_tab()
            if not self.current_tab:
                raise Exception("创建标签页失败")
            
            # 3. 连接 DevTools
            websocket_url = self.current_tab["webSocketDebuggerUrl"]
            self.devtools_client = DevToolsClient(websocket_url)
            
            if not await self.devtools_client.connect():
                raise Exception("连接 DevTools 失败")
            
            # 4. 启动事件监听
            listen_task = asyncio.create_task(self.devtools_client.listen_for_events())
            
            # 5. 收集性能数据
            self.performance_collector = PerformanceCollector(self.devtools_client)
            performance_data = await self.performance_collector.collect_performance_data(url, wait_time)
            
            # 6. 生成报告
            report = self.report_generator.generate_report(performance_data)
            
            # 7. 清理
            listen_task.cancel()
            await self.devtools_client.disconnect()
            
            if self.current_tab:
                self.chrome_manager.close_tab(self.current_tab["id"])
            
            self.logger.info(f"页面分析完成: {url}")
            return report
            
        except Exception as e:
            self.logger.error(f"页面分析失败: {e}")
            
            # 清理资源
            if self.devtools_client:
                try:
                    await self.devtools_client.disconnect()
                except:
                    pass
            
            if self.current_tab:
                try:
                    self.chrome_manager.close_tab(self.current_tab["id"])
                except:
                    pass
            
            return {
                "url": url,
                "error": str(e),
                "success": False
            }
    
    async def analyze_multiple_pages(self, urls: List[str], wait_time: int = 5, 
                                   concurrent: int = 1) -> List[Dict[str, Any]]:
        """
        分析多个页面的性能
        
        Args:
            urls: 目标页面URL列表
            wait_time: 每个页面的等待时间（秒）
            concurrent: 并发分析数量（建议为1，避免资源竞争）
            
        Returns:
            性能分析报告列表
        """
        self.logger.info(f"开始批量分析 {len(urls)} 个页面")
        
        if concurrent > 1:
            self.logger.warning("并发分析可能导致资源竞争，建议设置为1")
        
        results = []
        
        if concurrent == 1:
            # 顺序分析
            for i, url in enumerate(urls, 1):
                self.logger.info(f"分析进度: {i}/{len(urls)}")
                result = await self.analyze_page(url, wait_time)
                results.append(result)
                
                # 页面间间隔
                if i < len(urls):
                    await asyncio.sleep(1)
        else:
            # 并发分析（实验性）
            semaphore = asyncio.Semaphore(concurrent)
            
            async def analyze_with_semaphore(url):
                async with semaphore:
                    return await self.analyze_page(url, wait_time)
            
            tasks = [analyze_with_semaphore(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常结果
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    results[i] = {
                        "url": urls[i],
                        "error": str(result),
                        "success": False
                    }
        
        self.logger.info(f"批量分析完成，成功: {sum(1 for r in results if r.get('success', True))}/{len(results)}")
        return results
    
    def generate_summary_report(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成汇总报告
        
        Args:
            reports: 单页面报告列表
            
        Returns:
            汇总报告
        """
        if not reports:
            return {"error": "没有可用的报告数据"}
        
        successful_reports = [r for r in reports if r.get("success", True)]
        failed_reports = [r for r in reports if not r.get("success", True)]
        
        if not successful_reports:
            return {
                "total_pages": len(reports),
                "successful_pages": 0,
                "failed_pages": len(failed_reports),
                "error": "所有页面分析都失败了"
            }
        
        # 计算平均指标
        metrics_sum = {}
        metrics_count = {}
        
        for report in successful_reports:
            for metric_name, score_info in report.get("scores", {}).items():
                if metric_name not in metrics_sum:
                    metrics_sum[metric_name] = 0
                    metrics_count[metric_name] = 0
                
                metrics_sum[metric_name] += score_info["value"]
                metrics_count[metric_name] += 1
        
        average_metrics = {}
        for metric_name in metrics_sum:
            average_metrics[metric_name] = metrics_sum[metric_name] / metrics_count[metric_name]
        
        # 计算平均评分
        total_score = sum(r.get("overall_score", 0) for r in successful_reports)
        average_score = total_score / len(successful_reports)
        
        # 统计评级分布
        rating_distribution = {"good": 0, "needs_improvement": 0, "poor": 0}
        for report in successful_reports:
            score = report.get("overall_score", 0)
            if score >= 80:
                rating_distribution["good"] += 1
            elif score >= 50:
                rating_distribution["needs_improvement"] += 1
            else:
                rating_distribution["poor"] += 1
        
        return {
            "summary": {
                "total_pages": len(reports),
                "successful_pages": len(successful_reports),
                "failed_pages": len(failed_reports),
                "average_score": average_score,
                "rating_distribution": rating_distribution
            },
            "average_metrics": average_metrics,
            "best_performing": max(successful_reports, key=lambda x: x.get("overall_score", 0)),
            "worst_performing": min(successful_reports, key=lambda x: x.get("overall_score", 100)),
            "failed_urls": [r["url"] for r in failed_reports] if failed_reports else [],
            "detailed_reports": reports
        }
    
    def save_reports(self, reports: List[Dict[str, Any]], output_dir: str = "reports"):
        """
        保存所有报告到文件
        
        Args:
            reports: 报告列表
            output_dir: 输出目录
        """
        import os
        from datetime import datetime
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存单页面报告
        for i, report in enumerate(reports):
            if report.get("success", True):
                filename = f"report_{i+1}_{timestamp}.json"
                filepath = os.path.join(output_dir, filename)
                self.report_generator.save_report(report, filepath, "json")
                
                # 同时保存文本格式
                txt_filename = f"report_{i+1}_{timestamp}.txt"
                txt_filepath = os.path.join(output_dir, txt_filename)
                self.report_generator.save_report(report, txt_filepath, "txt")
        
        # 保存汇总报告
        if len(reports) > 1:
            summary = self.generate_summary_report(reports)
            summary_filepath = os.path.join(output_dir, f"summary_{timestamp}.json")
            self.report_generator.save_report(summary, summary_filepath, "json")
        
        self.logger.info(f"所有报告已保存到: {output_dir}")
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.current_tab:
                self.chrome_manager.close_tab(self.current_tab["id"])
            self.chrome_manager.cleanup()
        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup()
