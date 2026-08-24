package com.example.needleassistant

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.provider.AlarmClock
import android.provider.CalendarContract
import android.widget.Toast
import org.json.JSONObject

/**
 * Android Intent Dispatcher for Needle 2
 * 將 Needle 2 推論出的結構化 Action JSON 轉譯為 Android 原生 Intent 並執行的分派器。
 */
class IntentDispatcher(private val context: Context) {

    fun dispatchAction(actionJson: JSONObject): Boolean {
        return try {
            val type = actionJson.optString("type")
            when (type) {
                "alarm" -> handleSetAlarm(actionJson)
                "timer" -> handleSetTimer(actionJson)
                "calendar" -> handleCreateCalendarEvent(actionJson)
                "launch_app" -> handleLaunchApp(actionJson)
                "navigation" -> handleNavigation(actionJson)
                "message" -> handleSendMessage(actionJson)
                "notes" -> handleNotes(actionJson)
                else -> {
                    Toast.makeText(context, "未知的動作類型: $type", Toast.LENGTH_SHORT).show()
                    false
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
            Toast.makeText(context, "執行失敗: ${e.message}", Toast.LENGTH_SHORT).show()
            false
        }
    }

    private fun handleSetAlarm(json: JSONObject): Boolean {
        val hour = json.getInt("hour")
        val minute = json.getInt("minute")
        val label = json.optString("label", "鬧鐘")

        val intent = Intent(AlarmClock.ACTION_SET_ALARM).apply {
            putExtra(AlarmClock.EXTRA_HOUR, hour)
            putExtra(AlarmClock.EXTRA_MINUTES, minute)
            putExtra(AlarmClock.EXTRA_MESSAGE, label)
            putExtra(AlarmClock.EXTRA_SKIP_UI, false)
            flags = Intent.FLAG_ACTIVITY_NEW_TASK
        }
        context.startActivity(intent)
        return true
    }

    private fun handleSetTimer(json: JSONObject): Boolean {
        val seconds = json.getInt("seconds")
        val label = json.optString("label", "計時器")

        val intent = Intent(AlarmClock.ACTION_SET_TIMER).apply {
            putExtra(AlarmClock.EXTRA_LENGTH, seconds)
            putExtra(AlarmClock.EXTRA_MESSAGE, label)
            putExtra(AlarmClock.EXTRA_SKIP_UI, false)
            flags = Intent.FLAG_ACTIVITY_NEW_TASK
        }
        context.startActivity(intent)
        return true
    }

    private fun handleCreateCalendarEvent(json: JSONObject): Boolean {
        val title = json.getString("title")
        val location = json.optString("location", "")
        val description = json.optString("description", "")

        val intent = Intent(Intent.ACTION_INSERT).apply {
            data = CalendarContract.Events.CONTENT_URI
            putExtra(CalendarContract.Events.TITLE, title)
            putExtra(CalendarContract.Events.EVENT_LOCATION, location)
            putExtra(CalendarContract.Events.DESCRIPTION, description)
            flags = Intent.FLAG_ACTIVITY_NEW_TASK
        }
        context.startActivity(intent)
        return true
    }

    private fun handleLaunchApp(json: JSONObject): Boolean {
        val packageName = json.getString("package_name")
        val launchIntent = context.packageManager.getLaunchIntentForPackage(packageName)
        if (launchIntent != null) {
            launchIntent.flags = Intent.FLAG_ACTIVITY_NEW_TASK
            context.startActivity(launchIntent)
            return true
        } else {
            // 若未安裝該 App，引導至 Google Play Store
            val storeIntent = Intent(Intent.ACTION_VIEW, Uri.parse("market://details?id=$packageName")).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(storeIntent)
            return false
        }
    }

    private fun handleNavigation(json: JSONObject): Boolean {
        val destination = json.getString("destination")
        val gmmIntentUri = Uri.parse("google.navigation:q=${Uri.encode(destination)}")
        val mapIntent = Intent(Intent.ACTION_VIEW, gmmIntentUri).apply {
            setPackage("com.google.android.apps.maps")
            flags = Intent.FLAG_ACTIVITY_NEW_TASK
        }
        if (mapIntent.resolveActivity(context.packageManager) != null) {
            context.startActivity(mapIntent)
        } else {
            val webIntent = Intent(Intent.ACTION_VIEW, Uri.parse("https://www.google.com/maps/dir/?api=1&destination=${Uri.encode(destination)}")).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(webIntent)
        }
        return true
    }

    private fun handleSendMessage(json: JSONObject): Boolean {
        val uriStr = json.getString("uri")
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(uriStr)).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK
        }
        context.startActivity(intent)
        return true
    }

    private fun handleNotes(json: JSONObject): Boolean {
        val msg = json.optString("human_readable", "筆記已儲存")
        Toast.makeText(context, msg, Toast.LENGTH_LONG).show()
        return true
    }
}
