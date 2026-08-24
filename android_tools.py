"""
Android System Tools for Needle 2
==================================
定義對接 Android 系統底層功能的專用工具 Schema：
1. 鬧鐘設定 (Set Alarm)
2. 倒數計時器 (Set Timer)
3. 應用程式內深度搜尋 (Search in App: YouTube, Spotify, Google, Maps)
4. 應用程式啟動 (App Launcher)
5. 行事曆與行程安排 (Calendar & Schedules)
6. 地圖與導航 (Navigation & Maps)
7. 簡訊與通訊傳送 (SMS & Messaging)
8. 本地速記備忘 (Device Notes)
"""

import datetime
import json
import os
from typing import Annotated, Literal

import needle

NOTES_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mobile_notes.json")


def _get_notes():
    if os.path.exists(NOTES_DB_FILE):
        try:
            with open(NOTES_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_notes(notes):
    with open(NOTES_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)


# ==========================================
# 1. 鬧鐘工具 (Set Alarm)
# ==========================================

@needle.tool
def set_alarm(
    hour: Annotated[int, needle.Field(ge=0, le=23, description="Hour of the alarm in 24h format (0-23)")] = 8,
    minute: Annotated[int, needle.Field(ge=0, le=59, description="Minute of the alarm (0-59)")] = 0,
    label: Annotated[str, needle.Field(description="Label or title for the alarm")] = "鬧鐘"
):
    """Set a wake-up alarm clock for a specific time on the phone.

    Args:
        hour: alarm hour (0-23)
        minute: alarm minute (0-59)
        label: title or note for the alarm
    """
    time_str = f"{hour:02d}:{minute:02d}"
    return {
        "type": "alarm",
        "hour": hour,
        "minute": minute,
        "label": label or "鬧鐘",
        "human_readable": f"已為您設定鬧鐘：{time_str}（{label or '鬧鐘'}）",
        "android_intent": {
            "action": "android.intent.action.SET_ALARM",
            "extras": {
                "android.intent.extra.alarm.HOUR": hour,
                "android.intent.extra.alarm.MINUTES": minute,
                "android.intent.extra.alarm.MESSAGE": label or "鬧鐘"
            }
        }
    }


# ==========================================
# 2. 計時器工具 (Set Timer)
# ==========================================

@needle.tool
def set_timer(
    minutes: Annotated[int, needle.Field(ge=1, le=1440, description="Duration in minutes")] = 5,
    seconds: Annotated[int, needle.Field(ge=0, le=59, description="Extra seconds")] = 0,
    label: Annotated[str, needle.Field(description="Label or purpose of the timer")] = "計時器"
):
    """Start a countdown timer on the phone.

    Args:
        minutes: duration in minutes
        seconds: extra seconds
        label: purpose of the countdown
    """
    total_seconds = minutes * 60 + seconds
    human_duration = f"{minutes}分鐘" if seconds == 0 else f"{minutes}分{seconds}秒"
    return {
        "type": "timer",
        "minutes": minutes,
        "seconds": total_seconds,
        "label": label or "計時器",
        "human_readable": f"已設定倒數計時：{human_duration}（{label or '計時器'}）",
        "android_intent": {
            "action": "android.intent.action.SET_TIMER",
            "extras": {
                "android.intent.extra.alarm.LENGTH": total_seconds,
                "android.intent.extra.alarm.MESSAGE": label or "計時器"
            }
        }
    }


# ==========================================
# 3. 應用程式內深度搜尋 (Search in App)
# ==========================================

@needle.tool
def search_in_app(
    app: Annotated[Literal["youtube", "spotify", "google", "maps"], needle.Field(description="App platform to search in: 'youtube', 'spotify', 'google', 'maps'")],
    query: Annotated[str, needle.Field(description="Search keywords, video topic, artist, or place name")]
):
    """Search for content, videos, music, or places directly inside an app (YouTube, Spotify, Google, Maps).

    Args:
        app: target app ('youtube', 'spotify', 'google', 'maps')
        query: search keyword or video title
    """
    if app == "youtube":
        deep_uri = f"https://www.youtube.com/results?search_query={query}"
        app_name = "YouTube"
    elif app == "spotify":
        deep_uri = f"https://open.spotify.com/search/{query}"
        app_name = "Spotify"
    elif app == "maps":
        deep_uri = f"https://www.google.com/maps/search/?api=1&query={query}"
        app_name = "Google Maps"
    else:
        deep_uri = f"https://www.google.com/search?q={query}"
        app_name = "Google"

    return {
        "type": "search_in_app",
        "app": app,
        "app_name": app_name,
        "query": query,
        "deep_uri": deep_uri,
        "human_readable": f"正在 {app_name} 搜尋：『{query}』",
        "android_intent": {
            "action": "android.intent.action.VIEW",
            "data": deep_uri
        }
    }


# ==========================================
# 4. 應用程式啟動工具 (App Launcher)
# ==========================================

@needle.tool
def launch_app(
    app_name: Annotated[str, needle.Field(description="Name of the application to open, e.g. 'YouTube', 'LINE', 'Camera', 'Maps', 'Settings', 'Calculator', 'Chrome'")]
):
    """Open an installed mobile app on the phone.

    Args:
        app_name: application name
    """
    app_packages = {
        "youtube": {"pkg": "com.google.android.youtube", "name": "YouTube", "scheme": "vnd.youtube://"},
        "line": {"pkg": "jp.naver.line.android", "name": "LINE", "scheme": "line://"},
        "camera": {"pkg": "com.android.camera", "name": "相機", "action": "android.media.action.IMAGE_CAPTURE"},
        "maps": {"pkg": "com.google.android.apps.maps", "name": "Google 地圖", "scheme": "geo:0,0"},
        "calculator": {"pkg": "com.google.android.calculator", "name": "計算機", "scheme": "calc://"},
        "calc": {"pkg": "com.google.android.calculator", "name": "計算機", "scheme": "calc://"},
        "settings": {"pkg": "com.android.settings", "name": "系統設定", "action": "android.settings.SETTINGS"},
        "chrome": {"pkg": "com.android.chrome", "name": "Google Chrome", "scheme": "googlechrome://"},
        "spotify": {"pkg": "com.spotify.music", "name": "Spotify", "scheme": "spotify://"},
    }

    key = app_name.lower().strip()
    matched = app_packages.get(key, None)
    pkg = matched["pkg"] if matched else f"com.{key}"
    display_name = matched["name"] if matched else app_name
    scheme = matched.get("scheme", "") if matched else ""
    action = matched.get("action", "android.intent.action.MAIN") if matched else "android.intent.action.MAIN"

    return {
        "type": "launch_app",
        "app_name": display_name,
        "package_name": pkg,
        "scheme": scheme,
        "action": action,
        "human_readable": f"正在開啟應用程式：{display_name}",
        "android_intent": {
            "package": pkg,
            "action": action
        }
    }


# ==========================================
# 5. 行事曆工具 (Calendar)
# ==========================================

@needle.tool
def create_calendar_event(
    title: Annotated[str, needle.Field(description="Title or subject of the meeting or event")],
    start_time: Annotated[str, needle.Field(description="Start time, e.g. '2026-08-25 14:00'")],
    location: Annotated[str, needle.Field(description="Location of the meeting")] = "",
    description: Annotated[str, needle.Field(description="Notes or agenda")] = ""
):
    """Schedule and insert a new calendar event into the system calendar.

    Args:
        title: meeting or event title
        start_time: starting date and time
        location: meeting location
        description: extra notes
    """
    return {
        "type": "calendar",
        "title": title,
        "start_time": start_time,
        "location": location,
        "description": description,
        "human_readable": f"已建立行事曆行程：『{title}』時間：{start_time}" + (f" 地點：{location}" if location else ""),
        "android_intent": {
            "action": "android.intent.action.INSERT",
            "data": "content://com.android.calendar/events",
            "extras": {
                "title": title,
                "eventLocation": location,
                "description": description,
                "beginTime": start_time
            }
        }
    }


# ==========================================
# 6. 地圖導航工具 (Navigation)
# ==========================================

@needle.tool
def navigate_to_location(
    destination: Annotated[str, needle.Field(description="Destination name, address, or landmark")]
):
    """Open navigation to a map destination.

    Args:
        destination: target landmark or address
    """
    geo_uri = f"google.navigation:q={destination}"
    web_uri = f"https://www.google.com/maps/dir/?api=1&destination={destination}"

    return {
        "type": "navigation",
        "destination": destination,
        "geo_uri": geo_uri,
        "web_uri": web_uri,
        "human_readable": f"已為您規劃前往『{destination}』的導航路線",
        "android_intent": {
            "action": "android.intent.action.VIEW",
            "data": geo_uri
        }
    }


# ==========================================
# 7. 快速簡訊傳送 (Messaging)
# ==========================================

@needle.tool
def send_quick_message(
    recipient: Annotated[str, needle.Field(description="Recipient name or number")],
    message: Annotated[str, needle.Field(description="Message body text")]
):
    """Send or draft a quick text message to a contact.

    Args:
        recipient: contact name or number
        message: text message body
    """
    sms_uri = f"sms:{recipient}?body={message}"
    return {
        "type": "message",
        "app": "簡訊",
        "recipient": recipient,
        "message": message,
        "uri": sms_uri,
        "human_readable": f"準備發送簡訊給 {recipient}：『{message}』",
        "android_intent": {
            "action": "android.intent.action.SENDTO",
            "data": sms_uri
        }
    }


# ==========================================
# 8. 本機備忘筆記 (Notes)
# ==========================================

@needle.tool
def manage_device_notes(
    action: Annotated[Literal["add", "list", "clear"], needle.Field(description="'add', 'list', or 'clear'")],
    content: Annotated[str, needle.Field(description="Note text")] = ""
):
    """Record a quick voice note or list notes on the device.

    Args:
        action: 'add', 'list', or 'clear'
        content: note text
    """
    notes = _get_notes()
    if action == "add":
        if not content:
            return {"type": "notes", "status": "error", "message": "筆記內容不能為空"}
        new_entry = {
            "id": len(notes) + 1,
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": content
        }
        notes.append(new_entry)
        _save_notes(notes)
        return {
            "type": "notes",
            "action": "add",
            "note": new_entry,
            "human_readable": f"已為您新增本機筆記：『{content}』",
            "total_notes": len(notes)
        }
    elif action == "list":
        return {
            "type": "notes",
            "action": "list",
            "notes": notes,
            "total_notes": len(notes),
            "human_readable": f"目前共有 {len(notes)} 則備忘筆記"
        }
    return {"type": "notes", "status": "error", "message": "未知操作"}


def get_android_tools():
    return [
        set_alarm,
        set_timer,
        search_in_app,
        launch_app,
        create_calendar_event,
        navigate_to_location,
        send_quick_message,
        manage_device_notes,
    ]
