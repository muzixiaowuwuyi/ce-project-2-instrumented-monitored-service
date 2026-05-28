# Unified Monitoring & Observability Framework

This document provides a high-level overview of the full-stack monitoring architecture designed for the Flask microservice. Our observability strategy consolidates logs, native cloud metrics, custom metric filters, and interactive visualizations into a single operational plane.

---

## 🏛️ The Four Pillars of Our Monitoring Strategy

We monitor the microservice across four distinct operational layers to ensure zero blind spots:

### 1. 🪵 Infrastructure & Application Logging (The Source)
We capture continuous execution streams to ensure post-incident auditability:
* **`/aws/system/syslog`**: Tracks host-level OS health, security events, and Nginx proxy actions.
* **`/aws/application/api`**: Captures raw Python Flask runtime outputs, database connection logs, and unhandled tracebacks.
* *Standard Retention*: Configured strictly to **5 days** for optimal FinOps cost efficiency.

### 2. 📈 Standard Cloud Metrics (The Pulse)
Automated infrastructure counters sampled at 1-minute intervals to evaluate core stability:
* **Compute (EC2 Tier)**: Tracking `CPUUtilization` to catch host-level exhaustion.
* **Ingress (ALB Tier)**: Monitoring `TargetResponseTime` (p90 latency) and native `HTTPCode_Target_5XX_Count` to track real-time user experience.

### 3. 🎯 Log-Derived Custom Metrics (The Target Filters)
Asynchronous parsing patterns that transform raw log text into actionable cloud counters without editing backend source code:
* **`LogCriticalErrorCount`**: Listens for the `CRITICAL` keyword in application logs.
* **`BruteForceCredentialSprayingCount`**: Listens for failed authentication patterns on the secure login paths.

### 4. 📊 Centralized Observability Dashboard (The Single Pane of Glass)
All streams—logs, standard metrics, and custom filters—converge dynamically into the **Flask-Application-Observability Dashboard** (`dashboard.json`). 
* Designed for **rapid correlation analysis**, allowing engineers to visually tie a spike in error logs directly to CPU exhaustion or latency shifts on a single timeline.

---

