package com.example.needleassistant

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.PermissionRequest
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var intentDispatcher: IntentDispatcher

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 檢查並請求麥克風與鬧鐘權限
        requestPermissionsIfNeeded()

        intentDispatcher = IntentDispatcher(this)
        webView = WebView(this)
        setContentView(webView)

        setupWebView()

        // 載入打包在 assets 中的離線 Web 介面 (或連線至區域網路端點)
        webView.loadUrl("file:///android_asset/www/index.html")
    }

    private fun setupWebView() {
        val settings: WebSettings = webView.settings
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.allowFileAccess = true
        settings.allowContentAccess = true
        settings.mediaPlaybackRequiresUserGesture = false

        // 注入原生 JavaScript 橋接介面
        webView.addJavascriptInterface(WebAppInterface(), "AndroidNative")

        webView.webViewClient = object : WebViewClient() {}

        webView.webChromeClient = object : WebChromeClient() {
            override fun onPermissionRequest(request: PermissionRequest) {
                // 自動授權 Web 語音辨識所需的麥克風權限
                runOnUiThread {
                    request.grant(request.resources)
                }
            }
        }
    }

    private fun requestPermissionsIfNeeded() {
        val permissions = arrayOf(
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.READ_CALENDAR,
            Manifest.permission.WRITE_CALENDAR
        )
        val needed = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (needed.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, needed.toTypedArray(), 1001)
        }
    }

    inner class WebAppInterface {
        @JavascriptInterface
        fun executeAction(jsonString: String) {
            runOnUiThread {
                intentDispatcher.dispatchAction(jsonString)
            }
        }
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
