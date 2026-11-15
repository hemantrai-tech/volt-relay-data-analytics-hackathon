# VoltRelay Energy | Data Analytics Hackathon

**Where does the swap network break?** This project analyses a synthetic electric-vehicle battery-swapping network and turns reliability patterns into operational tests for the Gradient Learning Data Analytics Hackathon.

## Project showcase

- [Interactive dashboard](volt_relay_hackathon_project/index.html)
- [Analysis report](volt_relay_hackathon_project/project_report.md)
- [Colab-ready notebook](volt_relay_hackathon_project/volt_relay_analysis.ipynb)
- [Reproducible Python analysis](volt_relay_hackathon_project/analyze.py)
- [Aggregated analysis outputs](volt_relay_hackathon_project/aggregated_results/)
- [Video demo narration](volt_relay_hackathon_project/demo_video_script.md)
- [LinkedIn post draft](volt_relay_hackathon_project/linkedin_post.txt)
- [Download the complete project ZIP](volt_relay_hackathon_project.zip)

## Key findings

The simulation covers 3,877,013 swap events across Bengaluru, Delhi NCR, Hyderabad, Jaipur, Mumbai and Pune, from January 2024 through June 2025. Completion was 94.04%; technical failures were 3.76%; queue abandonment was 1.77%. No charged battery accounted for 92.1% of technical failures. Jaipur and Delhi NCR had the highest observed technical-failure rates.

Heat-alert days showed 9.89% technical failure versus 3.45% without alerts. This is a descriptive association, not proof of cause. The simplified contribution proxy was ₹31.08 per completed swap, but excludes battery depreciation, labour, financing, taxes and central overhead. The constructed 30-day repeat measure is saturated and cannot establish retention health.

## Run the analysis

1. Download the dataset ZIP from the Gradient Learning dataset folder and keep it in your private Drive.
2. Open the notebook in Google Colab and follow its setup cells; upload analyze.py to the Colab Files panel and set the ZIP path.
3. The notebook extracts the CSVs, runs the analyzer, and writes summarized CSV/JSON outputs. The raw dataset is intentionally not committed here.

## Scope and limits

The dataset is synthetic, seeded simulation data. City, weather, battery, wave and tariff comparisons are descriptive and may reflect confounding or simulation rules. The station-hour minimum-stock signal is not proof that a rider encountered a stockout. Support tickets and swap events use separate denominators.

This is an analytics case project, not a real airline booking system or a production transport service. All recommendations should be tested against station-level operational evidence before decisions are made.
