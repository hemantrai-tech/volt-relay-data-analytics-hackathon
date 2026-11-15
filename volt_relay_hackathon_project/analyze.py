import csv
import json
import math
import os
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)

def rows(name):
    with (RAW / name).open("r", newline="", encoding="utf-8-sig") as f:
        yield from csv.DictReader(f)

def num(x, default=0.0):
    try:
        return float(x) if x not in (None, "") else default
    except (TypeError, ValueError):
        return default

def safe_div(a, b):
    return a / b if b else None

stations = {}
for r in rows("stations.csv"):
    stations[r["station_id"]] = {
        "city": r["city"], "zone": r["zone"], "location_type": r["location_type"],
        "host_type": r["host_type"], "expansion_wave": r["expansion_wave"],
        "charger_generation": r["charger_generation"], "connectivity_tier": r["connectivity_tier"],
        "tariff": num(r["grid_tariff_inr_kwh"]),
        "fixed_monthly": num(r["monthly_rent_inr"]) + num(r["monthly_maintenance_inr"]),
        "commissioned": r["commissioned_date"], "decommissioned": r["decommissioned_date"]
    }

riders = {}
for r in rows("riders.csv"):
    riders[r["rider_id"]] = {"partner_id": r["partner_id"], "vehicle_class": r["vehicle_class"],
        "home_city": r["home_city"], "signup_channel": r["signup_channel"], "plan_type": r["plan_type"],
        "signup_date": r["signup_date"]}

partners = {r["partner_id"]: {"name": r["partner_name"], "segment": r["partner_segment"]}
            for r in rows("fleet_partners.csv")}

context = {}
for r in rows("city_daily_context.csv"):
    context[(r["city"], r["date"])] = {
        "heat": r["heat_alert"].lower() == "true",
        "flood": r["flood_disruption"].lower() == "true",
        "holiday": r["is_public_holiday"].lower() == "true",
        "promo": r["competitor_promo_active"].lower() == "true",
        "rain": num(r["rainfall_mm"])
    }

event_types = Counter()
monthly = defaultdict(lambda: {"events": 0, "completed": 0, "tech_fail": 0,
    "abandoned": 0, "cancelled": 0, "revenue": 0.0, "energy_kwh": 0.0,
    "energy_cost": 0.0, "discount": 0.0, "queue_sum": 0.0, "queue_n": 0, "long_queue": 0})
city_totals = defaultdict(lambda: Counter())
station_totals = defaultdict(lambda: Counter())
segment_totals = defaultdict(lambda: Counter())
partner_totals = defaultdict(lambda: Counter())
vehicle_totals = defaultdict(lambda: Counter())
tariff_totals = defaultdict(lambda: Counter())
hour_totals = defaultdict(lambda: Counter())
weather_totals = defaultdict(lambda: Counter())
weather_city_totals = defaultdict(lambda: Counter())
health_totals = defaultdict(lambda: Counter())
failure_stations = defaultdict(lambda: Counter())
rider_successes = {}
quality = Counter()
event_ids = set()
max_ts = ""
min_ts = "9999"
overall_financial = Counter()

with (RAW / "swap_events.csv").open("r", newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        quality["rows"] += 1
        ts = row.get("event_ts", "")
        typ = row.get("event_type", "unknown")
        event_types[typ] += 1
        sid = row.get("station_id", "")
        rid = row.get("rider_id", "")
        st = stations.get(sid)
        city = st["city"] if st else "Unknown"
        month = ts[:7] if len(ts) >= 7 else "Unknown"
        day = ts[:10] if len(ts) >= 10 else "Unknown"
        hour = ts[11:13] if len(ts) >= 13 else "Unknown"
        key = (month, city)
        m = monthly[key]
        m["events"] += 1
        ct = city_totals[city]
        ct["events"] += 1
        stc = station_totals[sid]
        stc["events"] += 1
        if not row.get("event_id") or not ts or not rid or not sid:
            quality["missing_key_fields"] += 1
        elif row["event_id"] in event_ids:
            quality["duplicate_event_ids"] += 1
        else:
            event_ids.add(row["event_id"])
        if ts:
            min_ts = min(min_ts, ts)
            max_ts = max(max_ts, ts)
        else:
            quality["missing_timestamp"] += 1
        if typ == "swap_completed":
            m["completed"] += 1; ct["completed"] += 1; stc["completed"] += 1
            rev = num(row.get("amount_charged_inr"))
            energy = num(row.get("energy_to_recharge_kwh"))
            discount = num(row.get("discount_inr"))
            e_cost = energy * (st["tariff"] if st else 0)
            m["revenue"] += rev; m["energy_kwh"] += energy; m["discount"] += discount
            m["energy_cost"] += e_cost
            overall_financial["revenue"] += rev
            overall_financial["energy_cost"] += e_cost
            overall_financial["energy_kwh"] += energy
            overall_financial["discount"] += discount
            if not row.get("energy_to_recharge_kwh"):
                quality["completed_missing_energy"] += 1
            if not row.get("amount_charged_inr"):
                quality["completed_missing_revenue"] += 1
            if rev < 0 or energy < 0:
                quality["negative_financial_or_energy"] += 1
            q = num(row.get("queue_wait_sec"))
            m["queue_sum"] += q; m["queue_n"] += 1
            if q >= 300: m["long_queue"] += 1
            seen = rider_successes.get(rid)
            if seen is None:
                rider_successes[rid] = [ts, None]
            elif ts < seen[0]:
                rider_successes[rid] = [ts, seen[0]]
            elif seen[1] is None or ts < seen[1]:
                seen[1] = ts
        elif typ.startswith("failed_"):
            m["tech_fail"] += 1; ct["tech_fail"] += 1; stc["tech_fail"] += 1
            failure_stations[sid][typ] += 1
        elif typ == "abandoned_queue":
            m["abandoned"] += 1; ct["abandoned"] += 1; stc["abandoned"] += 1
        elif typ == "cancelled_by_rider":
            m["cancelled"] += 1; ct["cancelled"] += 1; stc["cancelled"] += 1
        if st:
            stg = st["expansion_wave"] or "Unknown"
            seg = segment_totals[stg]; seg["events"] += 1
            if typ == "swap_completed": seg["completed"] += 1
            elif typ.startswith("failed_"): seg["tech_fail"] += 1
        rider_meta = riders.get(rid, {})
        partner_id = rider_meta.get("partner_id", "Unknown")
        partner_segment = partners.get(partner_id, {}).get("segment", "Unknown")
        for dim, value in (("partner_segment", partner_segment),
                           ("vehicle_class", rider_meta.get("vehicle_class", "Unknown"))):
            g = partner_totals[(dim, value)] if dim == "partner_segment" else vehicle_totals[value]
            g["events"] += 1
            if typ == "swap_completed": g["completed"] += 1
            elif typ.startswith("failed_"): g["tech_fail"] += 1
        tariff = row.get("tariff_code") or "Unknown"
        tg = tariff_totals[tariff]; tg["events"] += 1
        if typ == "swap_completed":
            tg["completed"] += 1
            tg["revenue"] += num(row.get("amount_charged_inr"))
            tg["discount"] += num(row.get("discount_inr"))
        elif typ.startswith("failed_"):
            tg["tech_fail"] += 1
        soh = num(row.get("soh_in_pct"), -1)
        health = "missing" if soh < 0 else ("low_<80" if soh < 80 else ("mid_80_90" if soh < 90 else "high_>=90"))
        hg = health_totals[health]; hg["events"] += 1
        if typ == "swap_completed": hg["completed"] += 1
        elif typ.startswith("failed_"): hg["tech_fail"] += 1
        hour_totals[hour]["events"] += 1
        if typ == "swap_completed": hour_totals[hour]["completed"] += 1
        elif typ.startswith("failed_"): hour_totals[hour]["tech_fail"] += 1
        wx = context.get((city, day))
        if wx:
            for label, enabled in (("heat", wx["heat"]), ("flood", wx["flood"]), ("holiday", wx["holiday"]), ("promo", wx["promo"])):
                state = "yes" if enabled else "no"
                bucket = weather_totals[label + "_" + state]
                bucket["events"] += 1
                if typ == "swap_completed": bucket["completed"] += 1
                elif typ.startswith("failed_"): bucket["tech_fail"] += 1
                cb = weather_city_totals[(label, city, state)]
                cb["events"] += 1
                if typ == "swap_completed": cb["completed"] += 1
                elif typ.startswith("failed_"): cb["tech_fail"] += 1

last_date = datetime.strptime(max_ts[:10], "%Y-%m-%d").date()
cutoff = last_date - timedelta(days=30)
retention_groups = defaultdict(lambda: Counter())
retention = Counter()
retention["eligible_signups"] = 0
retention["activated_30d"] = 0
retention["repeated_30d"] = 0
for rid, meta in riders.items():
    signup_text = meta.get("signup_date", "")
    try:
        signup = date.fromisoformat(signup_text)
    except ValueError:
        continue
    if signup < date.fromisoformat(min_ts[:10]) or signup > cutoff:
        continue
    retention["eligible_signups"] += 1
    first_ts, second_ts = rider_successes.get(rid, [None, None])
    window_end = signup + timedelta(days=30)
    first_day = datetime.strptime(first_ts[:10], "%Y-%m-%d").date() if first_ts else None
    second_day = datetime.strptime(second_ts[:10], "%Y-%m-%d").date() if second_ts else None
    activated = first_day is not None and signup <= first_day <= window_end
    repeated = activated and second_day is not None and first_day <= second_day <= window_end
    retention["activated_30d"] += int(activated)
    retention["repeated_30d"] += int(repeated)
    for dim, val in (("signup_month", signup_text[:7]),
                     ("city", meta.get("home_city", "Unknown")),
                     ("signup_channel", meta.get("signup_channel", "Unknown")),
                     ("plan_type", meta.get("plan_type", "Unknown"))):
        g = retention_groups[(dim, val)]
        g["eligible"] += 1; g["activated"] += int(activated); g["repeated"] += int(repeated)

# Active station fixed cost by calendar month (rent + maintenance).
months = sorted({m for m, _ in monthly if m != "Unknown"})
fixed_by_month_city = defaultdict(float)
for month in months:
    y, mo = map(int, month.split("-"))
    start = date(y, mo, 1)
    end = date(y + (mo == 12), 1 if mo == 12 else mo + 1, 1)
    for sid, st in stations.items():
        commissioned = date.fromisoformat(st["commissioned"]) if st["commissioned"] else date.min
        decommissioned = date.fromisoformat(st["decommissioned"]) if st["decommissioned"] else None
        if commissioned < end and (decommissioned is None or decommissioned >= start):
            fixed_by_month_city[(month, st["city"])] += st["fixed_monthly"]

def write_csv(path, header, data):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(data)

monthly_rows = []
for (month, city), d in sorted(monthly.items()):
    if month == "Unknown": continue
    n = d["events"]
    completed = d["completed"]
    tech_rate = safe_div(d["tech_fail"], n)
    abandon_rate = safe_div(d["abandoned"], n)
    rev_per = safe_div(d["revenue"], completed)
    kwh_per = safe_div(d["energy_kwh"], completed)
    fixed = fixed_by_month_city[(month, city)]
    contribution = d["revenue"] - d["energy_cost"] - fixed
    monthly_rows.append([month, city, n, completed, d["tech_fail"], tech_rate,
        d["abandoned"], abandon_rate, d["cancelled"], rev_per, kwh_per,
        safe_div(d["queue_sum"], d["queue_n"]), safe_div(d["long_queue"], completed),
        d["revenue"], d["energy_cost"], fixed, contribution,
        safe_div(contribution, completed), d["discount"]])
write_csv(OUT / "monthly_city.csv", ["month","city","events","completed","technical_failures","technical_failure_rate","abandoned_queue","abandonment_rate","cancelled","revenue_per_completed_inr","energy_kwh_per_completed","mean_queue_seconds_completed","completed_queue_ge_300s_share","revenue_inr","grid_energy_cost_inr","rent_maintenance_inr","contribution_proxy_inr","contribution_proxy_per_completed_inr","discount_inr"], monthly_rows)

city_rows = []
for city, d in sorted(city_totals.items()):
    n, done = d["events"], d["completed"]
    city_rows.append([city,n,done,safe_div(done,n),d["tech_fail"],safe_div(d["tech_fail"],n),
        d["abandoned"],safe_div(d["abandoned"],n),d["cancelled"],safe_div(d["cancelled"],n)])
write_csv(OUT / "city_performance.csv", ["city","events","completed","completion_rate","technical_failures","technical_failure_rate","abandoned_queue","abandonment_rate","cancelled","cancellation_rate"], city_rows)

station_rows=[]
for sid,d in station_totals.items():
    n=d["events"]; done=d["completed"]; st=stations.get(sid,{})
    station_rows.append([sid,st.get("city"),st.get("zone"),st.get("location_type"),st.get("expansion_wave"),st.get("charger_generation"),st.get("connectivity_tier"),n,done,safe_div(d["tech_fail"],n),safe_div(d["abandoned"],n)])
station_rows.sort(key=lambda x: (x[9] or 0), reverse=True)
write_csv(OUT / "station_performance.csv", ["station_id","city","zone","location_type","expansion_wave","charger_generation","connectivity_tier","events","completed","technical_failure_rate","abandonment_rate"], station_rows)

segment_rows=[]
for wave,d in sorted(segment_totals.items()):
    segment_rows.append([wave,d["events"],d["completed"],safe_div(d["tech_fail"],d["events"])])
write_csv(OUT / "station_wave_performance.csv", ["expansion_wave","events","completed","technical_failure_rate"], segment_rows)

partner_rows=[]
for (dim,val),d in sorted(partner_totals.items()): partner_rows.append([dim,val,d["events"],d["completed"],d["tech_fail"],safe_div(d["tech_fail"],d["events"])])
for val,d in sorted(vehicle_totals.items()): partner_rows.append(["vehicle_class",val,d["events"],d["completed"],d["tech_fail"],safe_div(d["tech_fail"],d["events"])])
write_csv(OUT / "partner_vehicle_performance.csv", ["dimension","group","events","completed","technical_failures","technical_failure_rate"], partner_rows)

tariff_rows=[]
for val,d in sorted(tariff_totals.items()): tariff_rows.append([val,d["events"],d["completed"],safe_div(d["tech_fail"],d["events"]),safe_div(d["revenue"],d["completed"]),d["discount"]])
write_csv(OUT / "pricing_performance.csv", ["tariff_code","events","completed","technical_failure_rate","revenue_per_completed_inr","discount_inr"],tariff_rows)

hour_rows=[]
for hour,d in sorted(hour_totals.items()): hour_rows.append([hour,d["events"],d["completed"],d["tech_fail"],safe_div(d["tech_fail"],d["events"])])
write_csv(OUT / "hourly_performance.csv", ["hour","events","completed","technical_failures","technical_failure_rate"], hour_rows)

ret_rows=[["overall",retention["eligible_signups"],retention["activated_30d"],safe_div(retention["activated_30d"],retention["eligible_signups"]),retention["repeated_30d"],safe_div(retention["repeated_30d"],retention["activated_30d"])]]
for (dim,val),d in sorted(retention_groups.items()): ret_rows.append([f"{dim}: {val}",d["eligible"],d["activated"],safe_div(d["activated"],d["eligible"]),d["repeated"],safe_div(d["repeated"],d["activated"])])
write_csv(OUT / "retention_30d.csv", ["group","eligible_signups","activated_within_30d","activation_rate_30d","two_or_more_swaps_within_30d","repeat_rate_among_activated_30d"], ret_rows)

weather_rows=[]
for label,d in sorted(weather_totals.items()): weather_rows.append([label,d["events"],d["completed"],d["tech_fail"],safe_div(d["tech_fail"],d["events"])])
write_csv(OUT / "weather_context.csv", ["condition","events","completed","technical_failures","technical_failure_rate"], weather_rows)

weather_city_rows=[]
for (condition,city,state),d in sorted(weather_city_totals.items()): weather_city_rows.append([condition,city,state,d["events"],d["tech_fail"],safe_div(d["tech_fail"],d["events"])])
write_csv(OUT / "weather_by_city.csv", ["condition","city","condition_active","events","technical_failures","technical_failure_rate"], weather_city_rows)

health_rows=[]
for group,d in sorted(health_totals.items()): health_rows.append([group,d["events"],d["completed"],d["tech_fail"],safe_div(d["tech_fail"],d["events"])])
write_csv(OUT / "battery_health_outcomes.csv", ["incoming_battery_soh_band","events","completed","technical_failures","technical_failure_rate"], health_rows)

# Supporting dataset audits and operational summaries.
support=Counter(); support_csat=defaultdict(lambda: [0.0,0]); support_res=defaultdict(lambda: [0.0,0])
for r in rows("support_tickets.csv"):
    cat=r["category"] or "Unknown"; support[cat]+=1
    if r["csat_score"]:
        support_csat[cat][0]+=num(r["csat_score"]); support_csat[cat][1]+=1
    if r["resolution_hours"]:
        support_res[cat][0]+=num(r["resolution_hours"]); support_res[cat][1]+=1
support_rows=[[k,v,safe_div(*support_csat[k]),safe_div(*support_res[k])] for k,v in support.most_common()]
write_csv(OUT / "support_categories.csv", ["category","tickets","mean_csat","mean_resolution_hours"],support_rows)

hourly=defaultdict(lambda: [0,0,0.0,0.0,0.0])
for r in rows("station_hourly_status.csv"):
    st=stations.get(r["station_id"]); city=st["city"] if st else "Unknown"
    d=hourly[city]; d[0]+=1
    if num(r["charged_2w_min"])<=0 or num(r["charged_3w_min"])<=0: d[1]+=1
    d[2]+=num(r["outage_minutes"]); d[3]+=num(r["avg_charge_minutes"]); d[4]+=1
hourly_rows=[[city,d[0],d[1],safe_div(d[1],d[0]),safe_div(d[2],d[0]),safe_div(d[3],d[4])] for city,d in sorted(hourly.items())]
write_csv(OUT / "hourly_station_status.csv", ["city","station_hours","any_vehicle_min_stockout_hours","stockout_station_hour_rate","mean_outage_minutes_per_station_hour","mean_charge_minutes"],hourly_rows)

type_rows=[[k,v,safe_div(v,quality["rows"])] for k,v in event_types.most_common()]
write_csv(OUT / "event_types.csv", ["event_type","count","share_of_rows"], type_rows)

# Machine-readable summary. Fixed station costs and grid energy are deliberately
# labeled as a contribution proxy; this excludes battery depreciation and central overhead.
summary={
  "business":"VoltRelay Energy synthetic EV battery-swapping network",
  "date_min":min_ts[:10],"date_max":max_ts[:10],"cities":sorted(city_totals),
  "station_count":len(stations),"rider_count":len(riders),"event_rows":quality["rows"],
  "event_types":dict(event_types),"technical_failure_rate":safe_div(sum(d["tech_fail"] for d in city_totals.values()),quality["rows"]),
  "abandonment_rate":safe_div(sum(d["abandoned"] for d in city_totals.values()),quality["rows"]),
  "cancellation_rate":safe_div(sum(d["cancelled"] for d in city_totals.values()),quality["rows"]),
  "completion_rate":safe_div(sum(d["completed"] for d in city_totals.values()),quality["rows"]),
  "revenue_inr":overall_financial["revenue"],"grid_energy_cost_inr":overall_financial["energy_cost"],
    "rent_maintenance_inr":sum(fixed_by_month_city.values()),
    "contribution_proxy_inr":overall_financial["revenue"]-overall_financial["energy_cost"]-sum(fixed_by_month_city.values()),
    "contribution_proxy_per_completed_swap_inr":safe_div(overall_financial["revenue"]-overall_financial["energy_cost"]-sum(fixed_by_month_city.values()),sum(d["completed"] for d in city_totals.values())),
  "energy_kwh":overall_financial["energy_kwh"],"discount_inr":overall_financial["discount"],
  "mean_revenue_per_completed_swap_inr":safe_div(overall_financial["revenue"],sum(d["completed"] for d in city_totals.values())),
  "mean_grid_cost_per_completed_swap_inr":safe_div(overall_financial["energy_cost"],sum(d["completed"] for d in city_totals.values())),
  "retention_eligible_signups":retention["eligible_signups"],"activated_within_30d":retention["activated_30d"],
  "activation_rate_30d":safe_div(retention["activated_30d"],retention["eligible_signups"]),
  "repeated_within_30d":retention["repeated_30d"],
  "repeat_rate_among_activated_30d":safe_div(retention["repeated_30d"],retention["activated_30d"]),
    "data_quality":{"rows":quality["rows"],"unique_event_ids":len(event_ids),"duplicate_event_ids":quality["duplicate_event_ids"],"missing_key_fields":quality["missing_key_fields"],"completed_missing_energy":quality["completed_missing_energy"],"completed_missing_revenue":quality["completed_missing_revenue"],"negative_financial_or_energy":quality["negative_financial_or_energy"]},"weather_association":weather_rows,
  "unit_economics_definition":"revenue less station-level grid energy cost; fixed rent/maintenance are summarized separately and may be allocated per completed swap. Excludes battery depreciation, labor, financing, taxes, central overhead.",
  "data_note":"Synthetic seeded simulation; observed associations are not causal estimates."
}
(OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
