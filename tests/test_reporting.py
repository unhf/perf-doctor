from src.reporting.base.generator import BaseReportGenerator
from src.reporting.html.generator import HTMLReportGenerator
from src.reporting.json.generator import JSONReportGenerator

def test_base_report_generator():
    class DummyReport(BaseReportGenerator):
        def generate(self):
            return "dummy"
    r = DummyReport({})
    assert r.generate() == "dummy"

def test_html_report_generator():
    data = {"msg": "hello"}
    r = HTMLReportGenerator(data)
    html = r.generate()
    assert "<html>" in html and "hello" in html

def test_json_report_generator():
    data = {"msg": "world"}
    r = JSONReportGenerator(data)
    js = r.generate()
    assert '"msg": "world"' in js 