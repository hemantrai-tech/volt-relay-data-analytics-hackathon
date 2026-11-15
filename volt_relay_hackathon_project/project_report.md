# Where Does the Swap Network Break?
## VoltRelay Energy | Gradient Learning Data Analytics Hackathon

### Executive summary
The synthetic network completed 94.04% of 3,877,013 attempts. Technical failures were 3.76%, queue abandonment 1.77%, and rider cancellations 0.43%. Of technical failures, 92.1% were recorded as no charged battery. Jaipur (5.06%) and Delhi NCR (4.71%) had the highest technical-failure rates.

Heat-alert days had a 9.89% failure rate versus 3.45% on non-alert days. This is an association, not a causal estimate. Batteries below 80% SOH had a 5.11% failure rate versus 3.48% for batteries at or above 90% SOH.

The simplified contribution proxy is ₹31.08 per completed swap after grid energy and allocated rent/maintenance. Battery depreciation, labour, finance, taxes and overhead are missing, so the available fields do not prove margin erosion. The constructed 30-day repeat metric is near 100% and is not useful to establish retention health.

### Recommendations
1. Prioritise station-hour availability checks in Jaipur and Delhi NCR; reconcile failures with telemetry and charging queues.
2. Prepare a heat-day readiness playbook and evaluate it with matched station-hours and time controls.
3. Audit batteries below 80% SOH by model, station and tenure before changing policy.
4. Replace saturated retention with eligible signup cohorts and 30/60/90-day repeat swaps.
5. Add depreciation and labour to station contribution economics before expansion.

### Scope and data quality
Synthetic seeded data for Bengaluru, Delhi NCR, Hyderabad, Jaipur, Mumbai and Pune, Jan 2024–Jun 2025: 152 stations and 20,000 riders. The event file has 3,877,013 unique event IDs, no missing key fields, no completed events missing energy or revenue, and no negative financial/energy values. Outcomes were kept distinct: completion, technical failure, queue abandonment and rider cancellation.

### Evidence limits
City, weather, battery, expansion-wave and tariff comparisons are descriptive; mix, time, station setup and simulation rules may explain differences. Station-hour minimum stock is a warning proxy, not proof a rider experienced a stockout. Ticket counts and event counts have different denominators. This analysis does not identify causal effects of the case's business changes.
