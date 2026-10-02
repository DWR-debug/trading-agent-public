import json, threading, time
from http.server import ThreadingHTTPServer
from automation import s10_systemone_bridge as bridge

def test_bridge_binds_loopback():
    assert bridge.HOST == "127.0.0.1"
    assert bridge.PORT == 8765
    assert bridge.LLAMA_BASE.startswith("http://127.0.0.1:")
