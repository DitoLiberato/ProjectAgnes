#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include <agnes_messages.h>

static constexpr const char* NODE_ID = "hub";
static constexpr const char* FW_VERSION = "hub-0.1.0";
static constexpr uint64_t BASE_EPOCH_MS = 1700000000000ULL;
static constexpr uint32_t HEARTBEAT_INTERVAL_MS = 2000;
static constexpr uint32_t NEXTION_BAUD = 115200;
static constexpr const char* UART_PROTO_VERSION = "0.1";

static uint32_t seqCounter = 1;
static uint32_t lastHeartbeatMs = 0;
static bool espNowReady = false;
static bool nextionUartReady = false;
static uint32_t currentPageId = 0;
static uint32_t inboundCommandCount = 0;
static String nextionRxBuffer;

static uint64_t nowTsMs() {
	return BASE_EPOCH_MS + static_cast<uint64_t>(millis());
}

static const char* statusText(bool ready) {
	return ready ? "ok" : "error";
}

static void sendNextionRaw(const String& cmd) {
	if (!nextionUartReady) {
		return;
	}
	Serial2.print(cmd);
	Serial2.write(0xFF);
	Serial2.write(0xFF);
	Serial2.write(0xFF);
}

static void sendNextionText(const char* component, const String& value) {
	String cmd;
	cmd.reserve(32 + value.length());
	cmd += component;
	cmd += ".txt=\"";
	cmd += value;
	cmd += "\"";
	sendNextionRaw(cmd);
}

static void sendNextionNumber(const char* component, uint32_t value) {
	String cmd;
	cmd.reserve(32);
	cmd += component;
	cmd += ".val=";
	cmd += value;
	sendNextionRaw(cmd);
}

static void renderNextionHeartbeat(uint64_t tsMs) {
	String state = espNowReady ? "CALM" : "DEGRADED";
	String reason = espNowReady ? "esp_now_ok" : "esp_now_init_failed";
	uint32_t confidence = espNowReady ? 90 : 40;
	uint32_t latencyMs = millis() - lastHeartbeatMs;

	sendNextionText("proto", UART_PROTO_VERSION);
	sendNextionText("state", state);
	sendNextionText("reason", reason);
	sendNextionNumber("confidence", confidence);
	sendNextionNumber("latency", latencyMs);
	sendNextionText("node_wear", "UNKNOWN");
	sendNextionText("node_env", "UNKNOWN");
	sendNextionText("link", espNowReady ? "ESP-NOW" : "DEGRADED");
	sendNextionNumber("uptime", millis());
	sendNextionNumber("page_id", currentPageId);
	sendNextionNumber("cmd_count", inboundCommandCount);
	sendNextionNumber("ts_lsb", static_cast<uint32_t>(tsMs & 0xFFFFFFFFULL));
}

static void logInboundCommand(const char* cmd, const String& value) {
	inboundCommandCount++;
	String log;
	log.reserve(200);
	log += "{\"hmi_cmd\":\"";
	log += cmd;
	log += "\",\"value\":\"";
	log += value;
	log += "\",\"ts_ms\":";
	log += nowTsMs();
	log += ",\"source_page\":";
	log += currentPageId;
	log += ",\"count\":";
	log += inboundCommandCount;
	log += "}";
	Serial.println(log);
}

static void handleNextionCommand(const String& rawLine) {
	String line = rawLine;
	line.trim();
	if (line.isEmpty()) {
		return;
	}

	if (line == "ack_event") {
		logInboundCommand("ack_event", "");
		return;
	}

	if (line == "mute_request") {
		logInboundCommand("mute_request", "");
		return;
	}

	if (line == "tech_check_request") {
		logInboundCommand("tech_check_request", "");
		return;
	}

	if (line.startsWith("page_change:")) {
		String pageValue = line.substring(strlen("page_change:"));
		currentPageId = static_cast<uint32_t>(pageValue.toInt());
		logInboundCommand("page_change", pageValue);
		return;
	}

	logInboundCommand("unknown", line);
}

static void pollNextionInput() {
	while (Serial2.available() > 0) {
		char ch = static_cast<char>(Serial2.read());
		if (ch == '\n' || ch == '\r') {
			if (!nextionRxBuffer.isEmpty()) {
				handleNextionCommand(nextionRxBuffer);
				nextionRxBuffer = "";
			}
			continue;
		}

		if (nextionRxBuffer.length() < 120) {
			nextionRxBuffer += ch;
		}
	}
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
	renderNextionHeartbeat(tsMs);
}

void setup() {
	Serial.begin(115200);
	delay(300);
	Serial.println("[hub] boot start");

	nextionRxBuffer.reserve(128);
	Serial2.begin(NEXTION_BAUD);
	nextionUartReady = true;

	WiFi.mode(WIFI_STA);
	WiFi.disconnect();
	espNowReady = (esp_now_init() == ESP_OK);

	Serial.print("[hub] uart_nextion=");
	Serial.println(statusText(nextionUartReady));
	Serial.print("[hub] esp_now=");
	Serial.println(statusText(espNowReady));

	sendNextionText("boot", "hub_boot_ok");
	sendNextionText("fw", FW_VERSION);
	sendNextionText("proto", UART_PROTO_VERSION);

	emitHeartbeat();
	lastHeartbeatMs = millis();
}

void loop() {
	pollNextionInput();

	if (millis() - lastHeartbeatMs < HEARTBEAT_INTERVAL_MS) {
		delay(50);
		return;
	}

	lastHeartbeatMs = millis();
	emitHeartbeat();
}
