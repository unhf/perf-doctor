from src.analysis.performance.analyzer import PerformanceAnalyzer
from src.analysis.network.analyzer import NetworkAnalyzer

def test_performance_analyzer():
    analyzer = PerformanceAnalyzer()
    data = {
        'PaintCollector': {'data': {'first-contentful-paint': 3000, 'largest-contentful-paint': 4000}},
        'NavigationCollector': {'data': {'pageLoad': 3500}},
        'MemoryCollector': {'data': {'heapUsagePercent': 85}},
        'NetworkCollector': {'data': {'statistics': {'totalRequests': 60, 'totalSize': 6*1024*1024}}}
    }
    result = analyzer.analyze(data)
    assert any(i['type'] == 'slow_fcp' for i in result['issues'])
    assert any(i['type'] == 'slow_lcp' for i in result['issues'])
    assert any(i['type'] == 'slow_load' for i in result['issues'])
    assert any(i['type'] == 'high_memory' for i in result['issues'])
    assert any(r['type'] == 'reduce_requests' for r in result['recommendations'])
    assert any(r['type'] == 'reduce_size' for r in result['recommendations'])

def test_network_analyzer():
    analyzer = NetworkAnalyzer()
    data = {'statistics': {'totalRequests': 100, 'totalSize': 10*1024*1024}}
    result = analyzer.analyze(data)
    assert any(i['type'] == 'too_many_requests' for i in result['issues'])
    assert any(i['type'] == 'large_total_size' for i in result['issues']) 