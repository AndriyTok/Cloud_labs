import pytest
import time
import requests
from threading import Thread


@pytest.fixture(scope="session")
def server_url():
    """Base URL for test server"""
    return "http://localhost:8000"


@pytest.fixture(scope="session", autouse=True)
def start_server():
    """Start Flask server in background thread"""
    from stability_templates.server.test_server import app

    def run_server():
        app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)

    thread = Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(2)  # Wait for server to start

    yield


@pytest.fixture
def mock_service(server_url):
    """Check if server is running and available"""
    max_retries = 3
    for i in range(max_retries):
        try:
            response = requests.get(f"{server_url}/health", timeout=1)
            if response.status_code == 200:
                return
        except Exception as e:
            if i == max_retries - 1:
                pytest.skip(
                    f"Test server is not running at {server_url}. "
                    "Start with: python -m stability_templates.server.test_server"
                )
            time.sleep(1)
