#include <Arduino.h>
#include <agnes_messages.h>

static constexpr const char* NODE_ID = "hub";
static constexpr const char* FW_VERSION = "hub-0.1.0";
static constexpr uint64_t BASE_EPOCH_MS = 1700000000000ULL;

static uint32_t seqCounter = 1;
static uint32_t lastEvidenceMs = 0;

static uint64_t nowTsMs() {
	return BASE_EPOCH_MS + static_cast<uint64_t>(millis());
}

void setup() {
	Serial.begin(115200);
	delay(300);
	Serial.println("[hub] boot ok");

	uint64_t tsMs = nowTsMs();
	String msgId = agnes::makeMsgId(NODE_ID, tsMs, seqCounter);
	agnes::Envelope env{"heartbeat", msgId.c_str(), tsMs, NODE_ID, seqCounter++};
	agnes::HeartbeatPayload heartbeat{millis(), -55, 100, FW_VERSION, "{\"esp_now\":\"ok\",\"uart_nextion\":\"ok\"}"};
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
			"fusion",
			"mechanical",
			"{\"agitation_index\":37,\"state\":\"CALM\"}",
			0.88f,
			0.82f,
			"[\"fusion_cycle\"]"};

	Serial.println(agnes::makeEvidenceMessage(env, evidence));
}
