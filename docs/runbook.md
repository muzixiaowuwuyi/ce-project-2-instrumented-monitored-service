# Incident Response Runbook: Flask Microservice Triage

This Runbook defines the Standard Operating Procedures (SOP) for responding to critical production alarms in the `eu-central-1` environment. Follow these steps sequentially during an active incident.

---

## 🚨 Incident 1: High Latency & 5xx Cascading Failure
**Triggering Alarms:** `AppLatencyWarningAlarm` AND `Http5xxCriticalAlarm` (Triggers `CombinedSystemOutageCriticalAlarm`)

### Step 1: Identify the Blast Radius (Dashboard)
1. Open the **Flask-Application-Observability** CloudWatch Dashboard.
2. Correlate the **p90 Latency** spike with the **Host CPU Utilization** widget.
   * **Scenario A (CPU at 100%)**: The host is hardware-starved. Proceed to Resource Exhaustion protocol.
   * **Scenario B (CPU normal, 5xx high)**: Application-level crash or database issue. Proceed to Step 2.

### Step 2: Query the Logs (CloudWatch Logs Insights)
Navigate to CloudWatch Logs Insights, select `/aws/application/api`, and run the following query to extract the top error stack traces:

```query
fields @timestamp, @message, @logStream
| filter @message like /ERROR/ or @message like /CRITICAL/
| sort @timestamp desc
| limit 20