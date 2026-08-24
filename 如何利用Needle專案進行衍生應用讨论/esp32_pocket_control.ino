/*
 * ESP32 Pocket Control — ESP32-WROOM Arduino firmware
 *
 * Prerequisites:
 * 1. Install the ESP32 board package in Arduino IDE.
 * 2. Install the ArduinoJson library (Library Manager).
 * 3. Enter your Wi-Fi SSID/password below.
 * 4. Confirm LED_PIN for your specific ESP32-WROOM development board.
 *
 * Security note:
 * This sketch is intentionally for a trusted local Wi-Fi prototype using an LED.
 * Do not expose it to the internet or use it for relays, mains power, locks, or
 * other safety-critical hardware without authentication and hardware safeguards.
 */

#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

const char *WIFI_SSID = "YOUR_WIFI_SSID";
const char *WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// GPIO 2 is common on many ESP32-WROOM dev boards, but not universal.
// Change this after confirming your board's onboard LED pin or external LED wiring.
constexpr uint8_t LED_PIN = 2;
constexpr uint8_t PWM_BITS = 8;
constexpr uint32_t PWM_FREQUENCY = 5000;

WebServer server(80);
bool ledOn = false;
uint8_t ledBrightness = 0;

void sendCorsHeaders() {
  // Required for the Expo web preview. Native Android/iOS builds do not use browser CORS.
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "Content-Type");
}

void writeLed() {
  ledcWrite(LED_PIN, ledOn ? ledBrightness : 0);
}

void sendJson(int status, JsonDocument &document) {
  String output;
  serializeJson(document, output);
  sendCorsHeaders();
  server.send(status, "application/json", output);
}

void sendError(int status, const char *message) {
  JsonDocument response;
  response["success"] = false;
  response["message"] = message;
  sendJson(status, response);
}

void addState(JsonDocument &document) {
  JsonObject state = document["state"].to<JsonObject>();
  JsonObject led = state["led"].to<JsonObject>();
  led["on"] = ledOn;
  led["brightness"] = ledBrightness;
}

void handleHealth() {
  JsonDocument response;
  response["ok"] = true;
  response["message"] = "ready";
  response["uptime_ms"] = millis();
  sendJson(200, response);
}

void handleState() {
  JsonDocument response;
  JsonObject led = response["led"].to<JsonObject>();
  led["on"] = ledOn;
  led["brightness"] = ledBrightness;
  sendJson(200, response);
}

bool hasOnlyCommandKeys(JsonDocument &document) {
  for (JsonPair keyValue : document.as<JsonObject>()) {
    const String key = keyValue.key().c_str();
    if (key != "action" && key != "on" && key != "brightness") {
      return false;
    }
  }
  return true;
}

void handleCommand() {
  const String body = server.arg("plain");
  if (body.isEmpty()) {
    sendError(400, "request body is required");
    return;
  }

  JsonDocument command;
  const DeserializationError error = deserializeJson(command, body);
  if (error || !command.is<JsonObject>()) {
    sendError(400, "request body must be a JSON object");
    return;
  }

  if (!hasOnlyCommandKeys(command) || !command.containsKey("action") ||
      !command.containsKey("on") || !command.containsKey("brightness")) {
    sendError(400, "command must contain only action, on, and brightness");
    return;
  }

  const char *action = command["action"] | "";
  if (String(action) != "set_led" || !command["on"].is<bool>() || !command["brightness"].is<int>()) {
    sendError(400, "invalid set_led command");
    return;
  }

  const int requestedBrightness = command["brightness"].as<int>();
  if (requestedBrightness < 0 || requestedBrightness > 255) {
    sendError(400, "brightness must be an integer from 0 to 255");
    return;
  }

  ledOn = command["on"].as<bool>();
  ledBrightness = ledOn ? static_cast<uint8_t>(requestedBrightness) : 0;
  writeLed();

  JsonDocument response;
  response["success"] = true;
  response["message"] = "LED updated";
  addState(response);
  sendJson(200, response);
}

void handleOptions() {
  sendCorsHeaders();
  server.send(204);
}

void connectToWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.print("ESP32 Pocket Control is ready at http://");
  Serial.println(WiFi.localIP());
}

void setup() {
  Serial.begin(115200);
  ledcAttach(LED_PIN, PWM_FREQUENCY, PWM_BITS);
  writeLed();
  connectToWifi();

  server.on("/health", HTTP_GET, handleHealth);
  server.on("/state", HTTP_GET, handleState);
  server.on("/command", HTTP_POST, handleCommand);
  server.on("/health", HTTP_OPTIONS, handleOptions);
  server.on("/state", HTTP_OPTIONS, handleOptions);
  server.on("/command", HTTP_OPTIONS, handleOptions);
  server.onNotFound([]() { sendError(404, "route not found"); });
  server.begin();
}

void loop() {
  server.handleClient();
}
