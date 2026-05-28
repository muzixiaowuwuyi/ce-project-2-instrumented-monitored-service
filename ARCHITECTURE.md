# Observability Architecture Specification: Telemetry Pipeline

This document details the architecture of the end-to-end telemetry pipeline, mapping how system data transforms from raw execution logs into real-time metrics, dynamic dashboards, and high-signal alerts within AWS CloudWatch (`eu-central-1`).

---

## 🔄 End-to-End Telemetry Architecture

The architecture functions as an automated data processing factory, split into three clear operational layers: Ingestion, Processing, and Action.


### 1. Ingestion Layer (The Telemetry Edge)
* **Dual Log Streams**: The underlying host captures telemetry at two distinct layers:
  * **System Layer**: Internal OS mechanics are mapped directly via `/var/log/syslog`.
  * **Application Layer**: Custom runtime business/framework flows are outputted straight to `application.log`.
* **CloudWatch Agent (Daemon)**: An administrative sidecar runner that continuously watches these active log files, aggregates the text lines into secure chunks, and ships them outbound to the CloudWatch endpoint over port `443`.

### 2. Processing Layer (Data Transformation & Visualization)
* **Metric Filters (Structured Parsing)**: Once raw unstructured logs land in `/aws/application/api`, a regex metric parser (`CriticalErrorFilter`) scans the stream. It automatically generates a structured custom metric (`LogCriticalErrorCount`) whenever a `CRITICAL` pattern occurs, successfully changing text into numbers.
* **Unified Dashboard Matrix**: All telemetry vectors—whether native cloud infra metrics (CPU), application ingress traffic (ALB), or log-parsed exceptions—converge onto a single dashboard matrix (`dashboard.json`) for effortless multi-dimensional correlation tracking.

### 3. Action Layer (The Alerting Topology)
* **Threshold Evaluators (Metric Alarms)**: Five tailored operational alarms poll individual metrics at 1-minute intervals, providing immediate isolation of specific failures (such as high load, latency spikes, or application drops).
* **Cross-Alarm Reducer (Composite Alarm)**: To avoid noise and notification storms, individual metrics are funneled through a logical circuit wrapper (`CombinedSystemOutageCriticalAlarm`). This alarm evaluates multi-fault scenarios (`AppLatency` **AND** `Http5xx`) before executing a notification dispatch to Amazon SNS.

---

## 💸 FinOps Structural Decisions

* **Log Retention Capping**: To prevent unchecked storage cost inflation, a global retention policy forces log expiry after **5 days**, keeping storage bills minimal and clean.
* **Standard Resolution Polling**: We utilize standard 1-minute metric evaluation resolutions rather than high-resolution 1-second loops, ensuring thorough SRE protection while remaining fully within the AWS Free Tier threshold limits.