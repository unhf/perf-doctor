import pytest
from src.core import Config, PerfDoctorException, PerformanceData

def test_config():
    config = Config()
    assert config.chrome.chrome_path
    assert config.collection.wait_time > 0

def test_exception():
    with pytest.raises(PerfDoctorException):
        raise PerfDoctorException("test error")

def test_performance_data():
    data = PerformanceData(url="https://a.com", timestamp=1, load_time=100)
    assert data.url == "https://a.com" 