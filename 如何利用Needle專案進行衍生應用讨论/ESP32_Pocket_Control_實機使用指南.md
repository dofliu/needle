# ESP32 Pocket Control 實機使用指南

本指南說明如何讓手機 App 控制一塊 ESP32-WROOM 開發板的 LED。第一版採用**同一個 Wi‑Fi 區域網路（Local Area Network, LAN）**加上 HTTP API；手機 App 與 ESP32 不需要使用雲端帳號，也不需要把 ESP32 對外公開。

> 本次原型僅應控制板載 LED 或低壓外接 LED。請勿用目前的 HTTP 範例直接控制繼電器、市電、門鎖、馬達或其他高風險設備。

## 一、整體流程

```text
電腦的 Arduino IDE ──USB 燒錄──> ESP32-WROOM
                                      │
                         Wi‑Fi + HTTP API（/health、/state、/command）
                                      │
手機的 Expo Go ──掃描 QR Code──> ESP32 Pocket Control App
                                      │
                             輸入 ESP32 內網 IP、測試、控制 LED
```

## 二、開始前要準備的東西

| 項目 | 用途 | 注意事項 |
| --- | --- | --- |
| ESP32-WROOM 開發板 | 被控制的硬體 | 必須是含 USB 轉序列晶片的開發板，不是只有裸 WROOM 模組。 |
| 可傳資料的 USB 線 | 燒錄程式與讀取序列埠 | 有些充電線沒有資料線，Arduino IDE 會看不到連接埠。 |
| 電腦 | 安裝 Arduino IDE、燒錄韌體 | Windows、macOS、Linux 均可。 |
| Android 或 iPhone 實機 | 執行 Expo Go 與 App | 手機需加入 ESP32 所在的同一個 Wi‑Fi。 |
| 家用或工作室 Wi‑Fi | ESP32 和手機的共同區域網路 | 請避免訪客 Wi‑Fi、AP isolation 或會隔離裝置的網路。 |
| 選配：LED 與 220–330 Ω 電阻 | 若板載 LED 不易辨識 | 外接 LED 長腳接 GPIO 2（經電阻）、短腳接 GND。 |

## 三、你問的兩個重點

### 1. 是否需要先連接 ESP32 並上傳程式碼？

**需要。** 手機 App 是控制端；ESP32 必須先燒錄「接上 Wi‑Fi 並提供 HTTP API」的程式，才會知道如何處理 App 傳來的 LED 命令。韌體檔已放在專案的：

```text
firmware/esp32_pocket_control.ino
```

它提供以下三個端點（Endpoint）：

| HTTP 方法 | 路徑 | 功能 |
| --- | --- | --- |
| `GET` | `/health` | 回報 ESP32 是否已啟動且可回應。 |
| `GET` | `/state` | 讀取 LED 開關與亮度。 |
| `POST` | `/command` | 接受 App 的 `set_led` 命令。 |

### 2. Wi‑Fi、IP 是否要寫死？

**Wi‑Fi 名稱與密碼：第一版需要寫入韌體；IP：不需要、也不建議寫死。**

| 設定項目 | 現在的做法 | 是否建議寫死 | 說明 |
| --- | --- | ---:| --- |
| `WIFI_SSID` | 填入你的 Wi‑Fi 名稱 | 是，原型階段 | ESP32 必須知道要加入哪個 Wi‑Fi。 |
| `WIFI_PASSWORD` | 填入你的 Wi‑Fi 密碼 | 是，原型階段 | 密碼只留在你電腦與板子的原始碼中，不要貼到聊天訊息或公開儲存庫。 |
| `LED_PIN` | 預設為 `2` | 視開發板而定 | GPIO 2 常見於 ESP32 開發板，但不是保證。 |
| ESP32 的 IP 位址 | 路由器用 DHCP 分配 | **否** | 開機後從序列監控視窗讀出，再填到手機 App。 |
| HTTP 連接埠 | 預設 `80` | 可維持預設 | App 的裝置設定畫面預設就是 80。 |

如果 Wi‑Fi 更換，第一版要改 `WIFI_SSID`／`WIFI_PASSWORD` 後重新燒錄。若 IP 變更，**不必重新燒錄**，只要在 App 的「裝置」分頁改成新的 IP 即可。正式版本建議改用路由器的 DHCP 位址保留（DHCP reservation），或後續加入 Wi‑Fi 配網（provisioning）與 mDNS；這樣便不用手動修改程式。

## 四、在 Arduino IDE 安裝 ESP32 支援

1. 安裝最新版 [Arduino IDE](https://www.arduino.cc/en/software)。
2. 打開 **File → Preferences**，在 **Additional Boards Manager URLs** 加入：

   ```text
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```

3. 打開 **Tools → Board → Boards Manager**，搜尋 `esp32`，安裝 Espressif 的 ESP32 平台。
4. 以 USB 資料線連接 ESP32；在 **Tools → Board** 選擇最接近板子型號的選項。若不確定，常見選擇為 `ESP32 Dev Module`。
5. 在 **Tools → Port** 選擇新出現的序列埠（Windows 通常是 `COMx`，macOS 通常是 `/dev/cu.*`）。

Espressif 官方文件確認可在 Arduino IDE 的 Preferences 加入 Board Manager URL，再於 Boards Manager 安裝 ESP32 平台並選擇對應開發板。[1]

## 五、填入 Wi‑Fi 與燒錄 ESP32 韌體

1. 從專案下載或複製 `firmware/esp32_pocket_control.ino` 到你的電腦，使用 Arduino IDE 開啟。
2. 尋找檔案開頭的兩行，**只在本機**填入自己的資料：

   ```cpp
   const char *WIFI_SSID = "YOUR_WIFI_SSID";
   const char *WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
   ```

   例如 Wi‑Fi 名稱為 `MyHome`，才改成 `"MyHome"`；不要把實際密碼傳給我。
3. 確認 `LED_PIN`。範例預設 GPIO 2；若燒錄成功但 LED 沒反應，先查你的開發板原理圖或板面標示。若使用外接 LED，可先接 GPIO 2 與 GND，並串聯 220–330 Ω 電阻。
4. 點 Arduino IDE 的 **Upload**。若出現連不上或 `Connecting...`，按住開發板的 **BOOT** 按鈕不放，等開始寫入後再放開。
5. Upload 成功後，開啟 **Tools → Serial Monitor**，鮑率（baud rate）選擇 `115200`。重按 ESP32 的 `EN`／`RST` 鍵，畫面應顯示：

   ```text
   ESP32 Pocket Control is ready at http://192.168.x.x
   ```

   記下 `192.168.x.x`。這是 DHCP 目前分配給 ESP32 的內網 IP，不是你要寫回程式碼的數值。

> 若你看到 IP 是 `0.0.0.0`、持續出現 `Connecting to Wi‑Fi...` 或一直重開機，通常是 SSID／密碼不正確、Wi‑Fi 為 5 GHz-only（一般 ESP32-WROOM 使用 2.4 GHz Wi‑Fi）、或供電／USB 線不穩。

## 六、先用瀏覽器確認 ESP32 是否真的正常

手機或電腦連上同一個 Wi‑Fi 後，在瀏覽器輸入：

```text
http://<ESP32-IP>/health
```

例如：

```text
http://192.168.1.80/health
```

預期會看到類似：

```json
{"ok":true,"message":"ready","uptime_ms":12345}
```

再輸入 `http://<ESP32-IP>/state`，預期會得到 LED 狀態 JSON。若瀏覽器做不到這一步，App 也無法連到 ESP32；應先排除 IP、Wi‑Fi 或韌體問題。

## 七、手機掃碼與 App 使用方式

### 1. 手機是否可以掃碼就使用 App？

**可以，但這是開發版流程，不是已安裝的 App Store／APK 版本。** 你需要在手機先安裝 **Expo Go**。目前版本沒有使用需要自訂原生建置的函式，因此可先用 Expo Go 載入。

| 平台 | 掃碼方式 |
| --- | --- |
| iPhone | 安裝 Expo Go 後，以手機相機掃描管理介面中的 Expo QR Code，選擇以 Expo Go 開啟。第一次存取區域網路時請選擇「允許」。 |
| Android | 安裝 Expo Go，從 Expo Go 的掃描功能掃描管理介面中的 QR Code。第一次使用時允許網路存取。 |

掃描成功後，請依下列順序操作：

1. 開啟 App 底部的 **裝置** 分頁。
2. 輸入裝置名稱，例如「工作桌 LED」。
3. 在「IP 位址或 mDNS 主機名稱」輸入剛剛在序列監控視窗看到的 IP，例如 `192.168.1.80`。**不要填 `http://`、不要填 `/health`。**
4. HTTP 連接埠填 `80`。
5. 點 **測試連線**。成功時會顯示「ESP32 可連線」或韌體回傳的 `ready`。
6. 點 **儲存裝置**，回到 **控制台**。
7. 點 **重新整理**，確認 App 能讀到 LED 目前狀態。
8. 切換 LED 開關，選擇 25%、50%、100% 或以 `＋／−` 調整亮度，再點 **套用至 ESP32**。
9. 到 **紀錄** 分頁查看成功或失敗的命令，方便檢查連線問題。

> 手機與 ESP32 必須位於同一個區域網路。手機可透過 QR Code 載入開發版，但若手機切換到 4G/5G、VPN、訪客 Wi‑Fi 或不同路由器，就無法控制家中的 ESP32。

## 八、常見問題排除

| 現象 | 可能原因 | 解法 |
| --- | --- | --- |
| Arduino IDE 看不到 Port | USB 線只能充電，或 USB driver 未安裝 | 換資料線／USB 孔；確認 Windows 裝置管理員或 macOS 系統資訊是否看到序列裝置。 |
| Upload 卡在 `Connecting...` | 有些開發板需要手動進入下載模式 | 上傳時按住 BOOT，開始寫入後再放開。 |
| 序列監控沒有 IP | SSID／密碼錯誤，或 Wi‑Fi 不支援 2.4 GHz | 再確認兩行 Wi‑Fi 設定，使用可供 2.4 GHz 裝置連線的 SSID。 |
| `/health` 在瀏覽器失敗 | IP 已變、手機與板子不同網路、ESP32 未連上 Wi‑Fi | 重新開啟 Serial Monitor 讀取新 IP；確認手機與板子連同一個 Wi‑Fi。 |
| App 顯示「離線」 | App 的 IP 或 port 錯誤，或網路隔離 | 在 App「裝置」頁重新測試；瀏覽器先測 `/health`；關閉 VPN。 |
| App 成功但 LED 不亮 | `LED_PIN` 不對，或板載 LED 為 active-low | 查板子 LED 腳位；改 `LED_PIN`；必要時在 `writeLed()` 將 PWM 輸出反相。 |
| 第一次 iPhone 連線失敗 | 本機網路權限被拒絕 | 到 iOS「設定 → 隱私權與安全性 → 本機網路」允許 Expo Go。 |
| QR Code 無法開啟 | Expo Go 未安裝、網路受限制，或開發伺服器未運作 | 先安裝 Expo Go；確認本專案開發伺服器顯示 running；重新掃描 QR Code。 |

## 九、目前版本與下一步

目前版本完成的是按鈕式 LED 控制。Needle 的自然語言功能尚未啟用；下一階段可把「把燈調成 30%」解析成同一種 `set_led` JSON，但 App 仍會先檢查裝置、欄位和亮度範圍才執行。

若要讓第一次使用更順暢，下一步最有價值的是加入**自動配網**或 **mDNS 裝置探索**，讓使用者不必打開 Serial Monitor 查 IP。

## References

[1]: https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html "Espressif Arduino-ESP32 Installation Guide"
