#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include <agnes_messages.h>

static constexpr const char* NODE_ID = "hub";
static constexpr const char* FW_VERSION = "hub-0.1.0";
static constexpr uint64_t BASE_EPOCH_MS = 1700000000000ULL;
static constexpr uint32_t HEARTBEAT_INTERVAL_MS = 2000;

static uint32_t seqCounter = 1;
static uint32_t lastHeartbeatMs = 0;
static bool espNowReady = false;
static bool nextionUartReady = false;

static uint64_t nowTsMs() {
	return BASE_EPOCH_MS + static_cast<uint64_t>(millis());
}

static const char* statusText(bool ready) {
	return ready ? "ok" : "error";
}

static void emitHeartbeat() {
	uint64_t tsMs = nowTsMs();
	String msgId = agnes::makeMsgId(NODE_ID, tsMs, seqCounter);
	agnes::Envelope env{"heartbeat", msgId.c_str(), tsMs, NODE_ID, seqCounter++};

	String sensorStatus;
	sensorStatus.reserve(120);
	sensorStatus += "{\"esp_now\":\"";
	sensorStatus += statusText(espNowReady);
	sensorStatus += "\",\"uart_nextion\":\"";
	sensorStatus += statusText(nextionUartReady);
	sensorStatus += "\",\"wifi_mode\":\"sta\"}";

	agnes::HeartbeatPayload heartbeat{
		millis(),
		WiFi.RSSI(),
		100,
		FW_VERSION,
		sensorStatus.c_str()};

	Serial.println(agnes::makeHeartbeatMessage(env, heartbeat));
}

void setup() {
	Serial.begin(115200);
	delay(300);
	Serial.println("[hub] boot start");

	Serial2.begin(115200);
	nextionUartReady = true;

	WiFi.mode(WIFI_STA);
	WiFi.disconnect();
	espNowReady = (esp_now_init() == ESP_OK);

	Serial.print("[hub] uart_nextion=");
	Serial.println(statusText(nextionUartReady));
	Serial.print("[hub] esp_now=");
	Serial.println(statusText(espNowReady));

	emitHeartbeat();
	lastHeartbeatMs = millis();
}

void loop() {
	if (millis() - lastHeartbeatMs < HEARTBEAT_INTERVAL_MS) {
		delay(50);
		return;
	}

	lastHeartbeatMs = millis();
	emitHeartbeat();
}
