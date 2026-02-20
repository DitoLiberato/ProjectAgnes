#include <agnes_messages.h>

namespace agnes {

static String envelopeJsonPrefix(const Envelope& envelope) {
  String out;
  out.reserve(180);
  out += "{\"schema_version\":\"";
  out += SCHEMA_VERSION;
  out += "\",\"msg_type\":\"";
  out += envelope.msgType;
  out += "\",\"msg_id\":\"";
  out += envelope.msgId;
  out += "\",\"ts_ms\":";
  out += String((unsigned long long)envelope.tsMs);
  out += ",\"node_id\":\"";
  out += envelope.nodeId;
  out += "\",\"seq\":";
  out += String(envelope.seq);
  return out;
}

String makeMsgId(const char* nodeId, uint64_t tsMs, uint32_t seq) {
  String out;
  out.reserve(64);
  out += nodeId;
  out += "-";
  out += String((unsigned long long)tsMs);
  out += "-";
  out += String(seq);
  return out;
}

String makeHeartbeatMessage(const Envelope& envelope, const HeartbeatPayload& payload) {
  String out = envelopeJsonPrefix(envelope);
  out += ",\"uptime_ms\":";
  out += String(payload.uptimeMs);
  out += ",\"rssi_dbm\":";
  out += String(payload.rssiDbm);
  out += ",\"battery_pct\":";
  out += String(payload.batteryPct);
  out += ",\"firmware_version\":\"";
  out += payload.firmwareVersion;
  out += "\",\"sensor_status\":";
  out += payload.sensorStatusJson;
  out += "}";
  return out;
}

String makeEvidenceMessage(const Envelope& envelope, const EvidencePayload& payload) {
  String out = envelopeJsonPrefix(envelope);
  out += ",\"sensor_type\":\"";
  out += payload.sensorType;
  out += "\",\"signal_type\":\"";
  out += payload.signalType;
  out += "\",\"value\":";
  out += payload.valueJson;
  out += ",\"quality_score\":";
  out += String(payload.qualityScore, 2);
  out += ",\"confidence_score\":";
  out += String(payload.confidenceScore, 2);
  out += ",\"context_tags\":";
  out += payload.contextTagsJson;
  out += "}";
  return out;
}

}
