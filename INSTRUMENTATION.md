# Application Instrumentation & Telemetry Metrics Reference

This document provides a concise reference for all code-level instrumentation and operational metrics tracked within the microservice. It defines exactly what is being measured and exposed to AWS CloudWatch.

---

## 🛑 1. HTTP Ingress & Golden Signals (ALB Tier)

These metrics are automatically collected at the Application Load Balancer boundary to track user-facing service health.

* **`HTTPCode_Target_5XX_Count`**
  * **What it measures**: Total count of server-side error responses (HTTP 500, 502, 504).
  * **Significance**: Immediate indicator of backend crashes or Nginx routing failure.
* **`HTTPCode_Target_4XX_Count`**
  * **What it measures**: Total count of client-side error responses (HTTP 400, 401, 403, 404).
  * **Significance**: Flags broken client links, unauthorized access attempts, or API abuse.
* **`TargetResponseTime`**
  * **What it measures**: Application latency (evaluated at the **p90** percentile).
  * **Significance**: Tracks performance degradation before it impacts the general user base.

---

## 🖥️ 2. Host Infrastructure Metrics (EC2 Tier)

System-level resource utilization metrics streamed continuously via the local hardware hypervisor.

* **`CPUUtilization`**
  * **What it measures**: Percentage of allocated compute units actively consumed on the `t3.micro` host.
  * **Significance**: Identifies CPU starvation or infinite loops causing application hangs.

---

## 📝 3. Log-Derived Custom Metrics (Application Tier)

Custom counters generated asynchronously by CloudWatch Metric Filters scanning row text in the `/aws/application/api` log group.

* **`LogCriticalErrorCount`**
  * **Pattern Matched**: `CRITICAL`
  * **What it measures**: Frequency of critical runtime exceptions or database disconnects bypassed by HTTP trackers.
* **`BruteForceCredentialSprayingCount`**
  * **Pattern Matched**: `[SECURITY] Failed login attempt`
  * **What it measures**: Volume of unauthorized authentication attempts hitting the `/login` route.

---

## 🛒 4. Business Funnel Metrics (Application KPI Tier)

Application-level custom counters tracking high-level product conversion and business platform health.

* **`CheckoutSuccessCount`**
  * **What it measures**: Total number of successfully completed checkout orders over time.
  * **Significance**: Cross-checks technical health against business reality. If technical metrics are green but checkout drops to 0, a silent business logic failure is occurring.