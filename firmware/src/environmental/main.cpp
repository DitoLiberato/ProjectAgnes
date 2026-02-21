#include <Arduino.h>
#include <agnes_messages.h>

static constexpr const char* NODE_ID = "env_node";
static constexpr const char* FW_VERSION = "environmental-0.1.0";
static constexpr uint64_t BASE_EPOCH_MS = 1700000000000ULL;

static uint32_t seqCounter = 1;
static uint32_t lastEvidenceMs = 0;
static bool psramReady = false;

static uint64_t nowTsMs() {
	return BASE_EPOCH_MS + static_cast<uint64_t>(millis());
}

void setup() {
	Serial.begin(115200);
	delay(300);
	Serial.println("[environmental] boot ok");
	psramReady = psramFound();
	Serial.print("[environmental] psram=");
	Serial.println(psramReady ? "ok" : "error");

	uint64_t tsMs = nowTsMs();
	String msgId = agnes::makeMsgId(NODE_ID, tsMs, seqCounter);
	agnes::Envelope env{"heartbeat", msgId.c_str(), tsMs, NODE_ID, seqCounter++};
	String sensorStatus;
	sensorStatus.reserve(64);
	sensorStatus += "{\"mmwave\":\"ok\",\"thermal\":\"ok\",\"psram\":\"";
	sensorStatus += psramReady ? "ok" : "error";
	sensorStatus += "\"}";
	agnes::HeartbeatPayload heartbeat{millis(), -58, 100, FW_VERSION, sensorStatus.c_str()};
	Serial.println(agnes::makeHeartbeatMessage(env, heartbeat));
}

void loop() {
	if (millis() - lastEvidenceMs < 5000) {
		delay(50);
		return;
	}

	lastEvidenceMs = millis();
	uint64_t tsMs = nowTsMs();
	String msgId = agnes::makeMsgId(NODE_ID, tsMs, seqCounter);
	agnes::Envelope env{"evidence", msgId.c_str(), tsMs, NODE_ID, seqCounter++};
	agnes::EvidencePayload evidence{
			"mmwave",
			"mechanical",
			"{\"resp_rate_bpm\":28,\"motion_index\":42}",
			0.91f,
			0.86f,
			"[\"resp_detected\",\"movement_moderate\"]"};

	Serial.println(agnes::makeEvidenceMessage(env, evidence));
}
