"""
Needle 2 Android Phone Assistant Server
========================================
本地輕量 HTTP 伺服器，為手機提供專屬行動 Web 介面與 Needle 2 意圖解析 API。
包含針對中文口語化指令的語意轉換適配器 (Semantic Normalizer)。
"""

import datetime
import json
import os
import platform
import re
import socket
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# 設定 Windows 終端編碼
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import needle
import android_tools

_DIR = Path(__file__).parent / "mobile_app"
_PORT = 8088


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def normalize_query(raw_query: str) -> str:
    """將口語中文指令進行語意適配，讓 45M 英文核心能 100% 精準匹配工具。"""
    q = raw_query.strip()

    # 1. 應用程式內深度搜尋: 例如 '開啟YouTube搜尋棒球', '在YouTube搜尋大谷翔平', 'Spotify搜尋周杰倫'
    m_search = re.search(r'(在|開啟|打開|去)?\s*(youtube|google|spotify|地圖|maps)?\s*(搜尋|查|找|播放|聽)\s*(.+)', q, re.IGNORECASE)
    if m_search and any(k in q.lower() for k in ["搜尋", "查", "找", "播放", "聽"]):
        app_raw = m_search.group(2) or ("youtube" if "youtube" in q.lower() else "spotify" if "spotify" in q.lower() else "google")
        app_map = {"youtube": "youtube", "google": "google", "spotify": "spotify", "地圖": "maps", "maps": "maps"}
        app = app_map.get(app_raw.lower(), "youtube" if "youtube" in q.lower() else "google")
        kw = m_search.group(4).strip()
        kw = re.sub(r'^(在|的|關於)\s*', '', kw).strip()
        if kw:
            return f"Search {kw} on {app}"

    # 2. 鬧鐘模式 (只要明確包含「鬧鐘 / 叫我起床」，優先當作鬧鐘)
    if any(k in q for k in ["鬧鐘", "叫我起床", "起床", "叫醒", "alarm"]):
        t_match = re.search(r'([0-9０-９]+)\s*[點点時时]\s*([0-9０-９]+)?', q)
        if t_match:
            h = int(t_match.group(1))
            m = int(t_match.group(2)) if t_match.group(2) else 0
            if "半" in q and not t_match.group(2):
                m = 30
            if "下午" in q or "晚上" in q:
                if h < 12:
                    h += 12
            return f"Set alarm for {h:02d}:{m:02d}"
        
        t_colon = re.search(r'([0-9]{1,2}):([0-9]{2})', q)
        if t_colon:
            h = int(t_colon.group(1))
            m = int(t_colon.group(2))
            if "下午" in q or "晚上" in q:
                if h < 12:
                    h += 12
            return f"Set alarm for {h:02d}:{m:02d}"
        return "Set alarm for 08:00"

    # 3. 計時器模式: 例如 '倒數15分鐘', '計時10分鐘'
    if any(k in q for k in ["倒數", "計時", "計時器", "倒計時"]):
        m_timer = re.search(r'([0-9０-９]+)\s*分', q)
        if m_timer:
            mins = int(m_timer.group(1))
            return f"Set timer for {mins} minutes"

    # 4. 導航模式: 例如 '導航到台北101', '帶我去火車站'
    m_nav = re.search(r'(導航到|帶我去|開車去|導航)\s*(.+)', q)
    if m_nav:
        dest = m_nav.group(2).strip()
        return f"Navigate to {dest}"

    # 5. 開啟 App (純開啟無搜尋): 例如 '打開YouTube', '開啟Line'
    m_app = re.search(r'(打開|開啟|啟動|開)\s*([a-zA-Z0-9\u4e00-\u9fa5]+)', q)
    if m_app and not any(k in q for k in ["鬧鐘", "會", "筆記", "搜尋", "查"]):
        app_name = m_app.group(2).strip()
        return f"Open {app_name} app"

    # 6. 行事曆會議模式 (包含 8/25 14:00 開會, 下週三會議, 8/25 07:30)
    if any(k in q for k in ["會議", "開會", "行程", "行程安排", "預約", "提醒", "見面"]) or re.search(r'[0-9]{1,2}[/月-][0-9]{1,2}', q):
        return f"Schedule calendar event: {q}"

    # 7. 備忘筆記模式: 例如 '記下一筆...', '紀錄筆記...'
    m_note = re.search(r'(記下|筆記|備忘|記錄|記一下)\s*[:：]?\s*(.+)', q)
    if m_note:
        return f"Add note: {m_note.group(2).strip()}"

    return q


class AgentManager:
    def __init__(self):
        print("[啟動中] 正在載入 Needle 2 Android 系統級工具庫...")
        self.tools = android_tools.get_android_tools()
        system_fact = f"date: {datetime.datetime.now().strftime('%Y-%m-%d %a %H:%M')}; os: Android; assistant: AndroidNeedle"
        self.agent = needle.Needle(tools=self.tools, system=system_fact)
        print(f"[就緒] Android 助理推論核心載入完成 (工具數: {len(self.tools)})")

    def complete_query(self, raw_query: str):
        adapted_query = normalize_query(raw_query)
        print(f"[語意適配] '{raw_query}' -> '{adapted_query}'")

        self.agent.reset()
        result = self.agent.run(adapted_query)
        return result


_AGENT = None


class MobileRequestHandler(BaseHTTPRequestHandler):
    def _send_response(self, code, body, content_type="application/json; charset=utf-8"):
        data = body if isinstance(body, (bytes, bytearray)) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self._send_response(200, b"", "text/plain")

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            file_path = _DIR / "index.html"
            self._send_response(200, file_path.read_bytes(), "text/html; charset=utf-8")
        elif path == "/style.css":
            file_path = _DIR / "style.css"
            self._send_response(200, file_path.read_bytes(), "text/css; charset=utf-8")
        elif path == "/app.js":
            file_path = _DIR / "app.js"
            self._send_response(200, file_path.read_bytes(), "application/javascript; charset=utf-8")
        elif path == "/api/status":
            self._send_response(200, json.dumps({"status": "ready", "model": "needle-2", "engine": "14MB native"}).encode("utf-8"))
        else:
            self._send_response(404, b"Not Found", "text/plain")

    def do_POST(self):
        if self.path == "/api/complete":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
                query = body.get("query", "").strip()
                if not query:
                    self._send_response(400, json.dumps({"error": "Query cannot be empty"}).encode("utf-8"))
                    return

                print(f"\n[收到手機指令] {query}")
                result = _AGENT.complete_query(query)
                print(f"[推論完成] 信心度: {result.get('confidence')} | 動作: {len(result.get('results', []))} 個")
                json_str = json.dumps(result, ensure_ascii=False)
                self._send_response(200, json_str.encode("utf-8"))
            except Exception as e:
                print(f"[錯誤] {e}")
                self._send_response(500, json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self._send_response(404, b"Not Found", "text/plain")

    def log_message(self, format, *args):
        pass


def main():
    global _AGENT
    _AGENT = AgentManager()
    server = ThreadingHTTPServer(("0.0.0.0", _PORT), MobileRequestHandler)
    local_ip = get_local_ip()

    print("=" * 60)
    print("      Needle 2 行動手機助理服務 (Mobile Action Hub) 已更新啟動！")
    print("=" * 60)
    print(f"💻 電腦端訪問網址： http://127.0.0.1:{_PORT}")
    print(f"📱 手機端訪問網址： http://{local_ip}:{_PORT}")
    print("   (請確保手機與電腦連線至同一個 Wi-Fi 區域網路)")
    print("=" * 60)
    print("等待手機端連線與指令中... (按 Ctrl+C 停止)")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n伺服器已關閉。")


if __name__ == "__main__":
    main()
