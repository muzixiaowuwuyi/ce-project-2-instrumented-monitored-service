# CloudWatch Dashboard Guide: Microservice Observability

This guide provides a concise overview of the deployed CloudWatch Dashboard (`dashboard.json`). This dashboard is designed to monitor the health, performance, traffic, and cost governance of the instrumented Flask application deployed in the `eu-central-1` region.

---

## 📊 Dashboard Architecture & Layout

The dashboard is organized into a single-pane 24-column grid layout, grouping core Golden Signals, infrastructure metrics, and financial safeguards together for rapid correlation analysis.

### 1. Application Performance & Golden Signals
* **Traffic & Request Volume**: Tracks the total influx of API requests to evaluate workload and system demand.
* **p90 Latency**: Measures application response times at the 90th percentile, isolating performance degradation before it impacts the general user base.
* **Error Rates (HTTP 5xx / 4xx)**: Monitors server-side and client-side error volumes to immediately flag service availability drops.

### 2. Host Infrastructure Health
* **Host CPU Utilization**: Displays CPU consumption on the underlying `t3.micro` EC2 host instance. Essential for identifying resource contention or CPU starvation that correlates with latency spikes.

### 3. Log-Derived Metrics (Metric Filters)
* **Log Critical Error Count**: Leverages a CloudWatch Metric Filter (`CriticalErrorFilter`) scanning `/aws/application/api` logs for the `CRITICAL` keyword, catching unhandled framework or database exceptions.

### 4. FinOps & Cloud Cost Governance
* **Budget & Resource Alignment**: A dedicated dashboard module tracking cost guardrails, ensuring strict compliance with AWS Free Tier constraints by explicitly monitoring `t3.micro` usage and regional thresholds.

---

## 🛠️ Infrastructure as Code (IaC) Deployment

The dashboard can be deployed instantly from your local DevOps workstation using the AWS CLI. 

### Prerequisites
* AWS CLI v2 installed and configured (`aws configure`).
* Default region set to `eu-central-1`.
* `jq` utility installed for JSON parsing.