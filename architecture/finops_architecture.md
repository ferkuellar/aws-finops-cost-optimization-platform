# Cloud FinOps Cost Optimization Platform — Architecture (MVP)

## High-level flow

Cost dataset (simulated CUR-like CSV)
  -> Amazon S3 (data lake / single source of truth)
  -> Amazon Athena (SQL analytics)
  -> Python Cost Analysis (business logic / waste signals)
  -> Streamlit Dashboard (executive visibility)
  -> Deployed on Amazon EC2 (demo-ready for interviews)

## AWS services used (and why)

- S3: durable storage for cost data, versioning-ready, low cost.
- Athena: serverless SQL over S3; avoids managing databases for analytics.
- EC2: simplest deployment target for an interview demo (no Docker/ECS yet).
- CloudWatch (next): logs/metrics for operability and production mindset.
- AWS Budgets (next): budget thresholds and cost control guardrails.

## FinOps outcomes (what this enables)

- Spend visibility: total cost, cost by service/region/env.
- Cost allocation signals: prod vs dev, top cost drivers.
- Waste signals (baseline): NAT Gateway spikes, EC2 dominance, dev anomalies.

## Assumptions (MVP)

- Data is simulated but structured to resemble billing exports.
- Single region for simplicity; multi-region is a v2 enhancement.
