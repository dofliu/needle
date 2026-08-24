"""
Needle 2 Desktop Assistant (邊緣端 AI 桌面智慧助理)
===================================================
以 Needle 2 (45M 參數 / 14MB 引擎 / 28MB RAM) 作為本地決策大腦，
提供完全離線、毫秒級響應的系統狀態查詢、筆記管理、檔案搜尋、網址與應用程式開啟等工具呼叫功能。
"""

import datetime
import json
import math
import os
import platform
import subprocess
import sys
import webbrowser
from typing import Annotated, Literal

# 設定標準輸出為 UTF-8 避免 Windows 終端編碼問題
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import needle

# 筆記儲存路徑
NOTES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "desktop_notes.json")


def _load_notes():
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_notes(notes):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)


# ==========================================
# 工具定義 (Tool Definitions)
# ==========================================

@needle.tool
def get_system_status():
    """Get the current computer system status, OS platform, and local time."""
    now = datetime.datetime.now()
    return {
        "os": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "weekday": now.strftime("%A"),
    }


@needle.tool
def add_note(note_text: str):
    """Add a new quick note or todo item to local notes.

    Args:
        note_text: the text content of the note to record
    """
    notes = _load_notes()
    entry = {
        "id": len(notes) + 1,
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "content": note_text
    }
    notes.append(entry)
    _save_notes(notes)
    return {"status": "success", "message": f"已儲存筆記：'{note_text}'", "total_notes": len(notes)}


@needle.tool
def list_notes():
    """List all saved quick notes and todo items."""
    notes = _load_notes()
    return {"status": "success", "notes": notes, "total_notes": len(notes)}


@needle.tool
def search_files(keyword: str):
    """Search for files in the current workspace matching a keyword in their filename.

    Args:
        keyword: keyword to look for in filenames
    """
    results = []
    target_dir = os.path.abspath(".")
    for root, _, files in os.walk(target_dir):
        # 忽略 .git 和 .cache
        if ".git" in root or ".cache" in root or ".venv" in root:
            continue
        for f in files:
            if keyword.lower() in f.lower():
                rel_path = os.path.relpath(os.path.join(root, f), target_dir)
                results.append(rel_path)
                if len(results) >= 8:
                    break
        if len(results) >= 8:
            break

    return {"status": "success", "keyword": keyword, "matches": results, "count": len(results)}


@needle.tool
def open_app_or_url(target: str):
    """Open a desktop application (notepad, calc, explorer) or a web URL in browser.

    Args:
        target: app name ('notepad', 'calc', 'explorer') or website URL
    """
    target_clean = target.strip()
    if target_clean.startswith("http://") or target_clean.startswith("https://") or "www." in target_clean:
        url = target_clean if target_clean.startswith("http") else f"https://{target_clean}"
        webbrowser.open(url)
        return {"status": "success", "opened": "url", "target": url}
    
    app_map = {
        "calc": "calc.exe",
        "calculator": "calc.exe",
        "notepad": "notepad.exe",
        "explorer": "explorer.exe",
        "cmd": "cmd.exe",
    }
    app_exec = app_map.get(target_clean.lower(), target_clean)
    try:
        subprocess.Popen(app_exec, shell=True)
        return {"status": "success", "opened": "application", "target": app_exec}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@needle.tool
def calculate(expression: str):
    """Evaluate a mathematical calculation expression safely.

    Args:
        expression: math expression, e.g. '1024 * 768 / 60'
    """
    safe_dict = {
        "abs": abs, "round": round, "min": min, "max": max,
        "sqrt": math.sqrt, "pi": math.pi, "sin": math.sin, "cos": math.cos
    }
    try:
        cleaned = expression.replace("^", "**")
        result = eval(cleaned, {"__builtins__": None}, safe_dict)
        return {"status": "success", "expression": expression, "result": result}
    except Exception as e:
        return {"status": "error", "message": f"Calculation error: {e}"}


# ==========================================
# 桌面助理類別 (Desktop Assistant Class)
# ==========================================

class DesktopAssistant:
    def __init__(self):
        self.tools = [
            get_system_status,
            add_note,
            list_notes,
            search_files,
            open_app_or_url,
            calculate,
        ]
        system_fact = f"date: {datetime.datetime.now().strftime('%Y-%m-%d %a %H:%M')}; os: {platform.system()}; assistant: NeedleDesktop"
        print("[啟動中] 正在載入 Needle 2 本地推論核心...")
        self.agent = needle.Needle(tools=self.tools, system=system_fact)
        print("[就緒] Needle 2 桌面助理已載入完畢！(引擎大小: 14MB, 記憶體: ~28MB)")

    def process(self, query: str):
        """執行自然語言指令並回傳結果"""
        print(f"\n[使用者指令] {query}")
        
        # 每次全新查詢前先 reset 對話狀態，維持獨立性
        self.agent.reset()
        result = self.agent.run(query)
        
        calls = result.get("function_calls", [])
        executed_results = result.get("results", [])
        confidence = result.get("confidence")
        reasoning = result.get("reasoning")
        tps = result.get("decode_tps", 0)

        print(f"[模型推論] 信心度: {confidence} | 解碼速度: {tps:.1f} tok/s")
        if reasoning:
            print(f"[意圖解析] {reasoning}")

        if not executed_results and not calls:
            print("[助理回應] 抱歉，目前的工具庫無法直接處理這項請求（已安全拒絕，未觸發任何動作）。")
            return result

        print(f"[執行結果] {json.dumps(executed_results, ensure_ascii=False, indent=2)}")
        return result


def run_demo():
    assistant = DesktopAssistant()
    print("=" * 60)
    print("      Needle 2 邊緣智慧桌面助理 - 快速展示測試")
    print("=" * 60)

    test_queries = [
        "What is my computer system status and time?",
        "Add a note: Discuss Needle 2 edge deployment tomorrow at 10am",
        "List all my saved notes",
        "Calculate 1024 * 768 / 60",
        "Search for files with keyword README",
        "Who is the president of France?",  # 離題/未支援查詢測試
    ]

    for q in test_queries:
        assistant.process(q)
        print("-" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        run_demo()
    elif len(sys.argv) > 1:
        # 單一指令模式
        user_query = " ".join(sys.argv[1:])
        assistant = DesktopAssistant()
        assistant.process(user_query)
    else:
        # 互動式 CLI 模式
        assistant = DesktopAssistant()
        print("\n=== Needle 2 桌面助理互動模式 (輸入 'exit' 或 'quit' 退出) ===")
        while True:
            try:
                prompt = input("\n請輸入指令 > ").strip()
                if not prompt:
                    continue
                if prompt.lower() in ("exit", "quit", "q"):
                    print("再見！")
                    break
                assistant.process(prompt)
            except (KeyboardInterrupt, EOFError):
                break
