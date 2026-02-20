#pragma once

#include <Arduino.h>
#include <stdint.h>

namespace agnes {

static constexpr const char* SCHEMA_VERSION = "0.1";

struct Envelope {
  const char* msgType;
  const char* msgId;
  uint64_t tsMs;
  const char* nodeId;
  uint32_t seq;
};

struct HeartbeatPayload {
  uint32_t uptimeMs;
  int rssiDbm;
  int batteryPct;
  const char* firmwareVersion;
  const char* sensorStatusJson;
};

struct EvidencePayload {
  const char* sensorType;
  const char* signalType;
  const char* valueJson;
  float qualityScore;
  float confidenceScore;
  const char* contextTagsJson;
};

String makeMsgId(const char* nodeId, uint64_t tsMs, uint32_t seq);
String makeHeartbeatMessage(const Envelope& envelope, const HeartbeatPayload& payload);
String makeEvidenceMessage(const Envelope& envelope, const EvidencePayload& payload);

}
