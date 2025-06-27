from src.infrastructure import ChromeManager, DevToolsClient

def test_chrome_manager_init():
    cm = ChromeManager(debug_port=9222)
    assert cm.debug_port == 9222

def test_devtools_client_init():
    # 这里只测试初始化，不连真实WebSocket
    client = DevToolsClient("ws://localhost:9222/devtools/page/1")
    assert client.websocket_url.startswith("ws://") 