// Needle 2 Mobile Assistant Frontend Controller

const streamContainer = document.getElementById("stream-container");
const queryInput = document.getElementById("query-input");
const btnMic = document.getElementById("btn-mic");
const voiceStatus = document.getElementById("voice-status");

// 1. 快速填入範例指令
function fillQuery(text) {
  queryInput.value = text;
  submitQuery();
}

// 2. 語音辨識處理 (Web Speech API)
let recognition = null;
let isRecording = false;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.lang = 'zh-TW';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    isRecording = true;
    btnMic.classList.add("listening");
    voiceStatus.textContent = "🎤 聆聽中，請說出指令...";
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    queryInput.value = transcript;
    voiceStatus.textContent = "";
    submitQuery();
  };

  recognition.onerror = (event) => {
    voiceStatus.textContent = "語音辨識錯誤：" + event.error;
    stopRecording();
  };

  recognition.onend = () => {
    stopRecording();
  };
}

function toggleVoiceInput() {
  if (!recognition) {
    alert("您的瀏覽器尚未支援 Web Speech 語音輸入，請直接以鍵盤輸入文字。");
    return;
  }
  if (isRecording) {
    recognition.stop();
    stopRecording();
  } else {
    try {
      recognition.start();
    } catch (e) {
      console.error(e);
    }
  }
}

function stopRecording() {
  isRecording = false;
  btnMic.classList.remove("listening");
  setTimeout(() => { voiceStatus.textContent = ""; }, 2500);
}

function handleKeyPress(e) {
  if (e.key === "Enter") {
    submitQuery();
  }
}

// 3. 提交查詢給 Needle 2 後端推論
async function submitQuery() {
  const query = queryInput.value.trim();
  if (!query) return;

  // 渲染使用者輸入泡泡
  appendUserBubble(query);
  queryInput.value = "";

  // 建立 Loading 占位卡片
  const loadingCard = document.createElement("div");
  loadingCard.className = "card-action-result";
  loadingCard.innerHTML = `<p style="color: #94a3b8; font-size: 0.85rem;">⚡ Needle 2 (45M) 正在本機神經推論中...</p>`;
  streamContainer.appendChild(loadingCard);
  streamContainer.scrollTop = streamContainer.scrollHeight;

  try {
    const startTime = performance.now();
    const response = await fetch("/api/complete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query })
    });

    const elapsed = Math.round(performance.now() - startTime);
    const data = await response.json();
    loadingCard.remove();

    renderActionResult(data, query, elapsed);
  } catch (err) {
    loadingCard.innerHTML = `<p style="color: #f87171; font-size: 0.85rem;">連線異常：${err.message}</p>`;
  }
}

function appendUserBubble(text) {
  const bubble = document.createElement("div");
  bubble.className = "card-user-query";
  bubble.textContent = text;
  streamContainer.appendChild(bubble);
  streamContainer.scrollTop = streamContainer.scrollHeight;
}

// 4. 渲染動作卡片與 Android Intent 執行按鈕
function renderActionResult(res, query, elapsed) {
  const card = document.createElement("div");
  card.className = "card-action-result";

  const results = res.results || [];
  const confidence = res.confidence !== null && res.confidence !== undefined ? (res.confidence * 100).toFixed(1) + "%" : "N/A";
  const tps = res.decode_tps ? res.decode_tps.toFixed(0) + " tok/s" : "";

  if (!results.length) {
    card.innerHTML = `
      <div class="refusal-card">
        <strong>⚠️ 無對應本機功能 (安全拒絕)</strong>
        <p style="margin-top: 4px;">Needle 2 判定目前沒有符合此要求的本機工具，已安全阻斷，未執行任何動作。</p>
        <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 8px;">推論時間：${elapsed}ms · 信心度：${confidence}</div>
      </div>
    `;
    streamContainer.appendChild(card);
    streamContainer.scrollTop = streamContainer.scrollHeight;
    return;
  }

  const actionItem = results[0];
  let badgeClass = "badge-alarm";
  let badgeText = "動作";
  let triggerBtnHtml = "";

  switch (actionItem.type) {
    case "alarm":
    case "timer":
      badgeClass = "badge-alarm";
      badgeText = actionItem.type === "timer" ? "計時器" : "鬧鐘";
      
      const clockIntentUri = `intent:#Intent;action=android.intent.action.SHOW_ALARMS;end`;
      const actionItemEscaped = JSON.stringify(actionItem).replace(/"/g, '&quot;');
      triggerBtnHtml = `
        <div style="display: flex; gap: 8px; flex-direction: column;">
          <button class="btn-trigger-action" onclick="executeIntent('${clockIntentUri}', '${actionItem.human_readable}', JSON.parse('${actionItemEscaped}'))">
            ⏰ 設定手機${badgeText}
          </button>
          <div style="font-size: 0.76rem; color: #94a3b8; text-align: center;">
            已解析：${actionItem.type === 'timer' ? actionItem.minutes + ' 分鐘' : actionItem.hour + ':' + String(actionItem.minute).padStart(2, '0')}
          </div>
        </div>
      `;
      break;

    case "search_in_app":
      badgeClass = "badge-app";
      badgeText = actionItem.app_name + " 搜尋";
      const searchActionEscaped = JSON.stringify(actionItem).replace(/"/g, '&quot;');
      triggerBtnHtml = `
        <button class="btn-trigger-action" onclick="executeWithFallback('${actionItem.deep_uri}', '${actionItem.deep_uri}', '${actionItem.human_readable}', JSON.parse('${searchActionEscaped}'))">
          🔍 開啟 ${actionItem.app_name} 搜尋「${actionItem.query}」
        </button>
      `;
      break;

    case "launch_app":
      badgeClass = "badge-app";
      badgeText = "開啟 App";
      const appIntent = `intent:#Intent;package=${actionItem.package_name};action=android.intent.action.MAIN;category=android.intent.category.LAUNCHER;end`;
      const launchActionEscaped = JSON.stringify(actionItem).replace(/"/g, '&quot;');
      triggerBtnHtml = `
        <button class="btn-trigger-action" onclick="executeIntent('${actionItem.scheme || appIntent}', '${actionItem.human_readable}', JSON.parse('${launchActionEscaped}'))">
          🚀 在手機上啟動 ${actionItem.app_name}
        </button>
      `;
      break;

    case "calendar":
      badgeClass = "badge-calendar";
      badgeText = "行事曆";
      const calIntentUri = `intent:#Intent;action=android.intent.action.INSERT;type=vnd.android.cursor.item/event;S.title=${encodeURIComponent(actionItem.title)};S.eventLocation=${encodeURIComponent(actionItem.location)};S.description=${encodeURIComponent(actionItem.description)};end`;
      const calWebFallback = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(actionItem.title)}&location=${encodeURIComponent(actionItem.location)}&details=${encodeURIComponent(actionItem.description)}`;
      const calActionEscaped = JSON.stringify(actionItem).replace(/"/g, '&quot;');
      triggerBtnHtml = `
        <button class="btn-trigger-action" onclick="executeWithFallback('${calIntentUri}', '${calWebFallback}', '${actionItem.human_readable}', JSON.parse('${calActionEscaped}'))">
          📅 開啟手機行事曆儲存
        </button>
      `;
      break;

    case "navigation":
      badgeClass = "badge-nav";
      badgeText = "導航地圖";
      const navActionEscaped = JSON.stringify(actionItem).replace(/"/g, '&quot;');
      triggerBtnHtml = `
        <button class="btn-trigger-action" onclick="executeWithFallback('${actionItem.geo_uri}', '${actionItem.web_uri}', '${actionItem.human_readable}', JSON.parse('${navActionEscaped}'))">
          🗺️ 開啟 Google Maps 導航
        </button>
      `;
      break;

    case "message":
      badgeClass = "badge-msg";
      badgeText = actionItem.app;
      triggerBtnHtml = `
        <button class="btn-trigger-action" onclick="window.location.href='${actionItem.uri}'">
          💬 在手機上開啟 ${actionItem.app}
        </button>
      `;
      break;

    case "notes":
      badgeClass = "badge-notes";
      badgeText = "備忘筆記";
      triggerBtnHtml = `
        <button class="btn-trigger-action" style="background: linear-gradient(135deg, #0ea5e9, #0284c7); color: white;" onclick="alert('${actionItem.human_readable}')">
          📝 筆記已同步儲存
        </button>
      `;
      break;
  }

  card.innerHTML = `
    <div class="action-header">
      <span class="action-badge ${badgeClass}">${badgeText}</span>
      <span class="action-metrics">⚡ ${elapsed}ms · ${tps} · 信心度 ${confidence}</span>
    </div>
    <div class="action-title">${actionItem.human_readable || "指令解析完成"}</div>
    <div class="action-json-preview">${JSON.stringify(actionItem, null, 2)}</div>
    ${triggerBtnHtml}
  `;

  streamContainer.appendChild(card);
  streamContainer.scrollTop = streamContainer.scrollHeight;
}

// 5. 觸發 Android 原生 Intent (原生 APK 或 Web 瀏覽器跳轉)
function executeIntent(intentUri, message, actionJson) {
  // 如果在原生 Android APK (WebView) 內運行，直接呼叫 Java/Kotlin 原生橋接！
  if (window.AndroidNative && actionJson) {
    window.AndroidNative.executeAction(JSON.stringify(actionJson));
    return;
  }
  try {
    window.location.href = intentUri;
  } catch (e) {
    alert(message);
  }
}

function executeWithFallback(intentUri, fallbackUrl, message, actionJson) {
  // 如果在原生 Android APK 內運行，直接呼叫 Java/Kotlin 原生橋接！
  if (window.AndroidNative && actionJson) {
    window.AndroidNative.executeAction(JSON.stringify(actionJson));
    return;
  }
  const isAndroid = /android/i.test(navigator.userAgent);
  if (isAndroid && intentUri) {
    window.location.href = intentUri;
    setTimeout(() => {
      if (fallbackUrl) window.open(fallbackUrl, "_blank");
    }, 1500);
  } else if (fallbackUrl) {
    window.open(fallbackUrl, "_blank");
  } else {
    alert(message);
  }
}
