export const DEFAULT_ESP32_PORT = 80;
export const MAX_LED_BRIGHTNESS = 255;

export type DeviceConfig = {
  name: string;
  host: string;
  port: number;
  baseUrl: string;
};

export type DeviceConfigInput = {
  name: string;
  host: string;
  port: string | number;
};

export type LedState = {
  on: boolean;
  brightness: number;
  updatedAt: string | null;
};

export type ConnectionStatus = "unknown" | "checking" | "online" | "offline";

export type HealthSnapshot = {
  status: ConnectionStatus;
  message: string;
  checkedAt: string | null;
  deviceUptimeMs?: number;
};

export type CommandLogEntry = {
  id: string;
  createdAt: string;
  action: "set_led";
  on: boolean;
  brightness: number;
  outcome: "success" | "failed";
  message: string;
};

export type LedCommand = {
  action: "set_led";
  on: boolean;
  brightness: number;
};

export type DeviceConfigResult =
  | { valid: true; value: DeviceConfig }
  | { valid: false; message: string };

export const EMPTY_LED_STATE: LedState = {
  on: false,
  brightness: 0,
  updatedAt: null,
};

export const INITIAL_HEALTH: HealthSnapshot = {
  status: "unknown",
  message: "尚未檢查裝置連線",
  checkedAt: null,
};

export function createDeviceConfig(input: DeviceConfigInput): DeviceConfigResult {
  const name = input.name.trim() || "我的 ESP32";
  const host = input.host
    .trim()
    .replace(/^https?:\/\//i, "")
    .replace(/\/.*$/, "")
    .replace(/\s/g, "");
  const port = Number(input.port);

  if (!host) {
    return { valid: false, message: "請輸入 ESP32 的區域網路 IP 或主機名稱。" };
  }

  if (!/^[a-zA-Z0-9][a-zA-Z0-9.-]*$/.test(host)) {
    return { valid: false, message: "裝置位址只能使用 IPv4 或 mDNS 主機名稱，例如 192.168.1.80。" };
  }

  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    return { valid: false, message: "連接埠必須介於 1 與 65535 之間。" };
  }

  return {
    valid: true,
    value: {
      name,
      host,
      port,
      baseUrl: `http://${host}:${port}`,
    },
  };
}

export function clampBrightness(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.round(Math.max(0, Math.min(MAX_LED_BRIGHTNESS, value)));
}

export function createLedCommand(on: boolean, brightness: number): LedCommand {
  return {
    action: "set_led",
    on,
    brightness: on ? Math.max(1, clampBrightness(brightness)) : 0,
  };
}

export function formatDeviceEndpoint(config: DeviceConfig): string {
  return `${config.host}:${config.port}`;
}
