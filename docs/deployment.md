# Production Deployment Playbook: Observability Infrastructure

This document provides a concise, step-by-step guide to deploying the complete observability infrastructure—including CloudWatch Alarms, Metric Filters, and Composite Alarms—from a local DevOps workstation to AWS CloudWatch (`eu-central-1`).

---

## 🏗️ Architecture Overview

The deployment framework follows **Infrastructure as Code (IaC)** principles using automated Bash and `jq` scripting to eliminate manual configuration errors in the AWS Console.

The stack consists of:
1. **Metric Alarms**: 5 baseline threshold monitors (Latency, Traffic, 5xx/4xx Errors, Host CPU).
2. **Metric Filters**: 1 log-scanning pattern matching filter targeting `CRITICAL` keywords.
3. **Composite Alarms**: 1 multi-condition logical alarm reduction rule (`AND` logic).

---

## 🛠️ Prerequisites

Before executing the deployment scripts on your local terminal, ensure the following tools are ready:
* **AWS CLI v2**: Installed and authenticated via `aws configure`.
* **IAM Permissions**: Active credentials with policy rights for `cloudwatch:*` and `logs:*`.
* **Target Region**: Configured strictly to `eu-central-1` (Frankfurt).
* **System Utilities**: `jq` installed for parsing JSON definitions.

---