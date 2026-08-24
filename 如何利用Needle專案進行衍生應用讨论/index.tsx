import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, Platform, ScrollView, Switch, Text, TouchableOpacity, View } from "react-native";

import { ScreenContainer } from "@/components/screen-container";
import { StatusChip } from "@/components/status-chip";
import { useDevice } from "@/lib/device-context";
import { formatDeviceEndpoint, MAX_LED_BRIGHTNESS } from "@/lib/esp32/types";

function formatCheckedAt(value: string | null) {
  if (!value) return "尚未更新";
  return new Intl.DateTimeFormat("zh-TW", { hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}

export default function DashboardScreen() {
  const { device, isReady, ledState, health, pendingOperation, refreshState, applyLed } = useDevice();
  const [ledOn, setLedOn] = useState(false);
  const [brightness, setBrightness] = useState(128);
  const isSending = pendingOperation === "command";
  const isRefreshing = pendingOperation === "state";

  useEffect(() => {
    setLedOn(ledState.on);
    setBrightness(ledState.brightness || 128);
  }, [ledState.brightness, ledState.on]);

  const pulse = () => {
    if (Platform.OS !== "web") void Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const changeBrightness = (next: number) => {
    pulse();
    setBrightness(Math.max(1, Math.min(MAX_LED_BRIGHTNESS, next)));
  };

  const handleApply = async () => {
    pulse();
    await applyLed(ledOn, brightness);
    if (Platform.OS !== "web") void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
  };

  if (!isReady) {
    return (
      <ScreenContainer className="items-center justify-center px-6">
        <ActivityIndicator size="large" />
        <Text className="mt-4 text-sm text-muted">正在讀取本機裝置設定…</Text>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer className="px-5" safeAreaClassName="pt-2">
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 28 }}>
        <View className="mb-6 mt-3 flex-row items-start justify-between">
          <View className="flex-1 pr-4">
            <Text className="text-sm font-semibold tracking-widest text-primary">ESP32 POCKET CONTROL</Text>
            <Text className="mt-2 text-3xl font-bold tracking-tight text-foreground">控制台</Text>
            <Text className="mt-2 text-sm leading-5 text-muted">在同一個 Wi-Fi 下查看狀態並安全控制你的裝置。</Text>
          </View>
          <StatusChip status={health.status} />
        </View>

        {!device ? (
          <View className="rounded-3xl border border-warning bg-surface p-5">
            <Text className="text-lg font-bold text-foreground">尚未設定 ESP32</Text>
            <Text className="mt-2 text-sm leading-5 text-muted">先輸入 ESP32 的區域網路 IP，App 才能讀取狀態與送出 LED 命令。</Text>
            <TouchableOpacity className="mt-5 items-center rounded-2xl bg-primary px-5 py-4" activeOpacity={0.82} onPress={() => router.push("/(tabs)/devices")}>
              <Text className="text-sm font-bold text-white">設定第一台裝置</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <>
            <View className="rounded-3xl border border-border bg-surface p-5">
              <View className="flex-row items-center justify-between">
                <View>
                  <Text className="text-base font-bold text-foreground">{device.name}</Text>
                  <Text className="mt-1 text-sm text-muted">{formatDeviceEndpoint(device)}</Text>
                </View>
                <TouchableOpacity disabled={isRefreshing || isSending} activeOpacity={0.75} onPress={() => void refreshState()} className="rounded-xl border border-border px-3 py-2 disabled:opacity-50">
                  <Text className="text-xs font-bold text-primary">{isRefreshing ? "更新中…" : "重新整理"}</Text>
                </TouchableOpacity>
              </View>
              <View className="mt-5 rounded-2xl bg-background p-4">
                <Text className="text-xs font-semibold text-muted">裝置回應</Text>
                <Text className="mt-1 text-sm leading-5 text-foreground">{health.message}</Text>
                <Text className="mt-2 text-xs text-muted">最後檢查：{formatCheckedAt(health.checkedAt)}</Text>
              </View>
            </View>

            <View className="mt-4 rounded-3xl border border-border bg-surface p-5">
              <View className="flex-row items-center justify-between">
                <View>
                  <Text className="text-lg font-bold text-foreground">LED 控制</Text>
                  <Text className="mt-1 text-sm text-muted">命令會先由 App 驗證，再送至 ESP32。</Text>
                </View>
                <Switch
                  value={ledOn}
                  disabled={isSending}
                  trackColor={{ false: "#CBD5E1", true: "#087E8B" }}
                  thumbColor="#FFFFFF"
                  onValueChange={(value) => {
                    pulse();
                    setLedOn(value);
                  }}
                />
              </View>

              <View className="mt-6 rounded-2xl bg-background p-4">
                <View className="flex-row items-end justify-between">
                  <View>
                    <Text className="text-xs font-semibold text-muted">亮度</Text>
                    <Text className="mt-1 text-4xl font-bold text-foreground">{ledOn ? brightness : 0}</Text>
                  </View>
                  <Text className="mb-1 text-sm text-muted">/ {MAX_LED_BRIGHTNESS}</Text>
                </View>
                <View className="mt-4 flex-row justify-between">
                  <TouchableOpacity className="rounded-xl border border-border px-4 py-3" activeOpacity={0.75} disabled={!ledOn || isSending} onPress={() => changeBrightness(brightness - 25)}>
                    <Text className="text-base font-bold text-foreground">−</Text>
                  </TouchableOpacity>
                  <TouchableOpacity className="rounded-xl border border-border px-4 py-3" activeOpacity={0.75} disabled={!ledOn || isSending} onPress={() => changeBrightness(64)}>
                    <Text className="text-xs font-bold text-foreground">25%</Text>
                  </TouchableOpacity>
                  <TouchableOpacity className="rounded-xl border border-border px-4 py-3" activeOpacity={0.75} disabled={!ledOn || isSending} onPress={() => changeBrightness(128)}>
                    <Text className="text-xs font-bold text-foreground">50%</Text>
                  </TouchableOpacity>
                  <TouchableOpacity className="rounded-xl border border-border px-4 py-3" activeOpacity={0.75} disabled={!ledOn || isSending} onPress={() => changeBrightness(255)}>
                    <Text className="text-xs font-bold text-foreground">100%</Text>
                  </TouchableOpacity>
                  <TouchableOpacity className="rounded-xl border border-border px-4 py-3" activeOpacity={0.75} disabled={!ledOn || isSending} onPress={() => changeBrightness(brightness + 25)}>
                    <Text className="text-base font-bold text-foreground">＋</Text>
                  </TouchableOpacity>
                </View>
              </View>

              <TouchableOpacity className="mt-5 items-center rounded-2xl bg-primary px-5 py-4 disabled:opacity-60" disabled={isSending} activeOpacity={0.82} onPress={() => void handleApply()}>
                <Text className="text-sm font-bold text-white">{isSending ? "正在送出命令…" : "套用至 ESP32"}</Text>
              </TouchableOpacity>
            </View>
          </>
        )}

        <View className="mt-4 rounded-3xl border border-border bg-surface p-5">
          <Text className="text-base font-bold text-foreground">準備接入 Needle</Text>
          <Text className="mt-2 text-sm leading-5 text-muted">後續可把「把燈調成 30%」轉換為相同的 set_led 結構化命令；但仍會先經過 App 的數值與裝置驗證。</Text>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}
