# Production Alerting Policy & Architecture Specification

This document details the design philosophy, metric thresholds, and architectural layout of the alerting system deployed for the Flask microservice in the `eu-central-1` region.

---

## 👁️ Alerting Philosophy

Our alerting strategy shifting from reactive firefighting to proactive incident management, built upon two core principles:
1. **The Four Golden Signals**: Prioritizing Latency, Traffic, and Errors to monitor user-facing impact.
2. **Alert Fatigue Reduction**: Utilizing advanced multi-condition logic (Composite Alarms) to bundle related infrastructure alerts, ensuring high-signal notifications.

---

## 📊 Alerting Matrix & Specifications

The monitoring layer consists of 5 standard Metric Alarms and 1 Advanced Composite Alarm managed via Infrastructure as Code definitions.

| Alarm Name | Targeted Metric | Condition & Threshold | Evaluation Period | Severity | Business Justification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Http5xxCriticalAlarm** | `HTTPCode_Target_5XX_Count` | $\ge 5$ requests | 1 Minute | **CRITICAL** | Immediate indicator of backend application crashes or unhandled server exceptions. |
| **AppLatencyWarningAlarm** | `TargetResponseTime` (p90) | $> 0.2\text{s}$ (200ms) | 1 Minute | **WARNING** | Detects performance degradation or downstream database blockages before total failure. |
| **HostCpuWarningAlarm** | `CPUUtilization` | $> 80\%$ | 1 Minute | **WARNING** | Flags compute resource exhaustion on the underlying `t3.micro` EC2 architecture. |
| **BruteForceCredentialSprayingAlarm** | `LogMatchCount` (via Filter) | $\ge 10$ failed logins | 1 Minute | **CRITICAL** | Identifies security anomalies and potential credential spraying attacks targeting `/login`. |
| **BusinessFunnelCheckoutDropAlarm** | `CheckoutSuccessCount` | $< 1$ order (Anomaly) | 5 Minutes | **WARNING** | Business-level metric monitoring. Flags systemic checkout drop-offs despite infrastructure health. |

---

## 🌐 Advanced Alerting Features

### 1. Log-Derived Custom Metrics (Metric Filters)
Instead of polling databases, we utilize a CloudWatch Metric Filter (`CriticalErrorFilter`) scanning the `/aws/application/api` log group. It instantly converts raw log strings matching the `CRITICAL` pattern into a numeric metric (`LogCriticalErrorCount`), capturing core crashes bypassed by standard HTTP tracking.

### 2. Composite Alarms (Incident Noise Control)
To prevent alert fatigue and redundant notifications during cascading infrastructure failure, we deployed a logical composite wrapper:

* **Alarm Name**: `CombinedSystemOutageCriticalAlarm`
* **Logical Rule**: `ALARM(AppLatencyWarningAlarm) AND ALARM(Http5xxCriticalAlarm)`



* **Behavior**: If the server experiences high latency *without* errors, or errors *without* latency, it is treated as an isolated event. However, when both triggers activate simultaneously, it escalates to a **FATAL System Outage**, triggering top-tier engineering routing via Amazon SNS.

---

## 💸 FinOps Guardrails

To strictly align with the AWS Free Tier limitations within `eu-central-1`, all alarms adhere to the following data ingestion constraints:
* **Log Retention**: Automatically capped at **5 days** across all log groups to minimize long-term CloudWatch storage costs.
* **Evaluation Windows**: Restricted to 1-minute resolutions using standard infrastructure metrics rather than high-resolution 1-second polling to control metrics processing charges.