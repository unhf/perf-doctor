from src.collectors.base import BaseCollector, CollectorManager
import pytest

class DummyClient:
    async def enable_domain(self, domain):
        return True

class DummyCollector(BaseCollector):
    def get_required_domains(self):
        return ["Performance"]
    async def setup(self):
        return True
    async def collect(self):
        return self._create_result({"dummy": 1})

def test_collector_manager_register():
    cm = CollectorManager(DummyClient())
    c = DummyCollector(DummyClient(), "Dummy")
    cm.register_collector(c)
    assert cm.get_collector("Dummy") is c
    assert len(cm.get_all_collectors()) == 1 