# Cloud-Native Microservice Observability & Telemetry Framework

A production-grade observability and automated monitoring architecture deployed in the `eu-central-1` (Frankfurt) region for a Python Flask microservice. 

This project demonstrates full-stack cloud telemetry integration—incorporating structured logging, Infrastructure as Code (IaC) dashboarding, custom log-derived metric tracking, and advanced noise-controlled composite alerting strategies.

---

## 🏛️ Project Documentation Hub

To explore specific architectural decisions, deployment steps, or operational playbooks, please refer to the specialized documentation modules below:

* **[ARCHITECTURE.md](./architecture.md)**: Explains the end-to-end data processing pipeline mapping how logs and metrics flow securely into AWS CloudWatch.
* **[MONITORING.md](./monitoring.md)**: Provides a high-level bird's-eye view of our four-pillar observability strategy (Logs, Standard Metrics, Custom Filters, Dashboard).
* **[INSTRUMENTATION.md](./instrumentation.md)**: A concise technical reference cataloging every application-level and host-level metric tracker embedded in the service.
* **[ALERTING.md](./alerting.md)**: Details the design thresholds, evaluation windows, and advanced noise-reduction logic behind our Composite Alarms.
* **[RUNBOOK.md](./runbook.md)**: The standard incident response SOP providing step-by-step resolution playbooks for on-call engineers during production outages.
* **[DEPLOYMENT.md](./deployment.md)**: The production playbook hosting automated CLI and `jq` scripting to instantly spin up the entire monitoring framework.

---

## 🚀 Quick IaC Stack Deployment

To deploy the entire observability infrastructure (Dashboards, Filters, and Alarms) from your local DevOps workstation, ensure your AWS CLI v2 is configured to `eu-central-1` and run:

```bash
# Clone the repository and navigate to the config directory
cd ~/ce-project-2-instrumented-monitored-service/config

# Run the deployment playbook instructions found in DEPLOYMENT.md
# 1. Deploy baseline alarms
jq -c '.[]' alarms.json | while read -r alarm; do aws cloudwatch put-metric-alarm --cli-input-json "$alarm"; done

# 2. Deploy composite alarms
aws cloudwatch put-composite-alarm --cli-input-json file://composite_alarm.json