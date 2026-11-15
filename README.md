# VoltRelay Energy — Data Analytics Hackathon

> **Live project showcase:** [Open the interactive dashboard](https://volt-relay-data-analytics-hackathon.vercel.app/)

This project analyses a synthetic EV battery-swapping network for the Gradient Learning Data Analytics Hackathon. It examines service reliability, battery availability, station telemetry, support issues, retention measurement and a bounded unit-economics proxy.

## Findings

- **3,877,013** swap events across six Indian cities, Jan 2024–Jun 2025; **94.04%** completion.
- **3.76%** technical failures; **1.77%** queue abandonment. These outcomes are kept distinct.
- **92.1%** of technical failures were recorded as no charged battery. Jaipur and Delhi NCR had the highest observed city-level technical-failure rates.
- Heat-alert days showed **9.89%** technical failure vs **3.45%** without alerts. This is an association, not a causal estimate.
- Contribution proxy: **₹31.08 per completion**, excluding battery depreciation, labour, financing, tax and overhead.

## Explore the project

- [Interactive dashboard source](volt_relay_hackathon_project/index.html) — the live version is hosted on Vercel above.
- [Full analysis report](volt_relay_hackathon_project/project_report.md)
- [Colab notebook](volt_relay_hackathon_project/volt_relay_analysis.ipynb)
- [Python analysis code](volt_relay_hackathon_project/analyze.py)
- [Aggregated CSV and JSON results](volt_relay_hackathon_project/aggregated_results/)
- [Demo narration](volt_relay_hackathon_project/demo_video_script.md)
- [LinkedIn post draft](volt_relay_hackathon_project/linkedin_post.txt)
- [Complete ZIP download](volt_relay_hackathon_project.zip)

## Reproduce

Download the source dataset ZIP from the Gradient Learning Drive folder and keep the raw data private. Open the notebook in Google Colab, upload `analyze.py`, set the Drive ZIP path, and run the cells. The analyzer writes summary CSV/JSON outputs.

## Data and interpretation limits

The records are synthetic seeded simulation data. City, weather, battery, expansion-wave and tariff comparisons are descriptive; confounding and simulation rules may explain differences. The station-hour stockout measure is a telemetry warning, not evidence of a rider encounter. The 30-day repeat metric is saturated and cannot establish retention health. The cost proxy is not full contribution margin.
