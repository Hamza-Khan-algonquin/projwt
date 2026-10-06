#!/usr/bin/env python3
r"""dashboard_PWT.py — one-page ProjWT dashboard: your biometrics + your car.

Pulls the car's live state from the Fleet API (battery, range, cabin/outside temp,
lock, odometer, location) and your latest biometrics from the newest rawstream CSV,
and writes a single self-contained offline HTML page. Also shows the smart-climate
recommendation (body + weather -> suggested cabin temp).

Needs the proxy running + TESLA_VEHICLE_TAG / TESLA_FLEET_BASE set for live car data;
without them it still renders the biometrics.

Usage:
    python dashboard_PWT.py
    python dashboard_PWT.py --open      # also open it in the browser
"""
import argparse
import csv
import json
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

from vehicle_actuator_PWT import TeslaFleetActuator

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def latest_biometrics():
    # try live rolling offload first (near-real-time ~1 Hz, 1–2s lag)
    rolling = LOG_DIR / "rolling_biometrics_PWT.json"
    if rolling.exists():
        try:
            data = json.loads(rolling.read_text(encoding="utf-8"))
            recs = data.get("records", [])
            if recs:
                hr = [r["hr"] for r in recs if r.get("hr") is not None]
                temps = []
                for r in recs:
                    sr = r.get("skin_raw")
                    if sr is not None:
                        c = sr * 0.04
                        if 20 <= c <= 45:
                            temps.append(round(c, 1))
                gmag = [r["gmag"] for r in recs if r.get("gmag") is not None]
                return {
                    "source": "rolling (live)",
                    "hr": hr[-600:], "skin": temps[-1] if temps else None,
                    "hr_now": hr[-1] if hr else None,
                    "hr_min": min(hr) if hr else None, "hr_max": max(hr) if hr else None,
                    "gmag": gmag,
                }
        except Exception:  # noqa: BLE001
            pass
    # fallback: latest CSV capture
    csvs = sorted(LOG_DIR.glob("rawstream_*_PWT.csv"))
    if not csvs:
        return None
    hr, temps, gmag = [], [], []
    with csvs[-1].open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("hr") and row["hr"].isdigit():
                hr.append(int(row["hr"]))
            tr = row.get("skin_temp_raw")
            if tr and tr.isdigit():
                c = int(tr) * 0.04
                if 20 <= c <= 45:
                    temps.append(round(c, 1))
            if row.get("gmag"):
                try:
                    gmag.append(float(row["gmag"]))
                except ValueError:
                    pass
    return {
        "source": f"CSV ({csvs[-1].name})",
        "hr": hr[-600:], "skin": temps[-1] if temps else None,
        "hr_now": hr[-1] if hr else None,
        "hr_min": min(hr) if hr else None, "hr_max": max(hr) if hr else None,
        "gmag": gmag,
    }


def car_snapshot():
    act = TeslaFleetActuator()
    vd = act.get_vehicle_data()
    if not vd.get("ok"):
        return {"ok": False, "error": vd.get("error")}
    d = vd["data"]
    ch, cl, dr, vs = (d.get(k) or {} for k in ("charge_state", "climate_state", "drive_state", "vehicle_state"))
    return {
        "ok": True,
        "name": d.get("display_name"),
        "battery": ch.get("battery_level"),
        "range_km": round(ch.get("battery_range", 0) * 1.609, 0) if ch.get("battery_range") else None,
        "charging": ch.get("charging_state"),
        "inside_c": cl.get("inside_temp"), "outside_c": cl.get("outside_temp"),
        "set_c": cl.get("driver_temp_setting"),
        "locked": vs.get("locked"), "odometer_km": round(vs.get("odometer", 0) * 1.609) if vs.get("odometer") else None,
        "lat": dr.get("latitude"), "lon": dr.get("longitude"), "speed": dr.get("speed"),
    }


HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>ProjWT Dashboard</title>
<style>
 :root{color-scheme:dark;--bg:#0b0e16;--panel:#151a28;--ink:#e8edf7;--mut:#8894ad;
   --ok:#80ffdb;--warn:#ffd166;--bad:#ff5d73;--hr:#ff5d73;--acc:#4cc9f0;--grid:#232a3d}
 *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
   font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;padding:22px;max-width:900px;margin:auto}
 h1{font-size:20px;margin:0 0 2px}.sub{color:var(--mut);font-size:13px;margin-bottom:18px}
 .live-indicator{display:inline-block;width:8px;height:8px;border-radius:50%;background:#80ffdb;margin-right:6px;animation:pulse 1s infinite}
 @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.3}}
 h2{font-size:13px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em;margin:22px 0 10px}
 .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
 .tile{background:var(--panel);border:1px solid var(--grid);border-radius:12px;padding:14px 16px}
 .tile .k{color:var(--mut);font-size:12px}.tile .v{font-size:26px;font-weight:600;margin-top:4px}
 .tile .u{font-size:13px;color:var(--mut);font-weight:400}
 .pill{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:600}
 .card{background:var(--panel);border:1px solid var(--grid);border-radius:12px;padding:14px 16px;margin-top:12px}
 canvas{width:100%;height:150px;display:block}.err{color:var(--warn)}
 footer{color:var(--mut);font-size:12px;margin-top:22px}
</style></head><body>
<h1>ProjWT Dashboard</h1><div class="sub" id="asof"></div><div id="live-badge"></div>
<h2>Vehicle</h2><div class="grid" id="car"></div>
<h2>Smart climate</h2><div class="card" id="climate"></div>
<h2>Biometrics</h2><div class="grid" id="bio"></div>
<div class="card"><div class="k" style="color:var(--mut);font-size:12px">Heart rate (recent)</div>
<canvas id="hr"></canvas></div>
<footer>Car data: Tesla Fleet API (signed). Biometrics: decoded from the WHOOP band. Private - not for sharing.</footer>
<script>
const D = __DATA__;
const css=k=>getComputedStyle(document.documentElement).getPropertyValue(k).trim();
document.getElementById('asof').textContent = "as of " + D.asof;
const isLive = D.bio && D.bio.source && D.bio.source.includes('rolling');
if(isLive){
  document.getElementById('live-badge').innerHTML = '<div style="color:var(--ok);font-size:12px;margin-bottom:12px"><span class="live-indicator"></span>Live (auto-refresh)</div>';
  setTimeout(()=>location.reload(), 3000);  // refresh every 3s when rolling
}
function tiles(el, items){document.getElementById(el).innerHTML = items.map(t=>
  `<div class="tile"><div class="k">${t[0]}</div><div class="v">${t[1]}<span class="u"> ${t[2]||''}</span></div></div>`).join('');}
if(D.car && D.car.ok){
  const c=D.car, lock = c.locked? '<span class="pill" style="background:#16351f;color:var(--ok)">LOCKED</span>'
                               : '<span class="pill" style="background:#3a1620;color:var(--bad)">UNLOCKED</span>';
  tiles('car',[['Battery', c.battery??'--','%'],['Range', c.range_km??'--','km'],
    ['Inside', c.inside_c??'--','C'],['Outside', c.outside_c??'--','C'],
    ['Set to', c.set_c??'--','C'],['Charging', c.charging||'--','']]);
  document.getElementById('car').insertAdjacentHTML('beforeend',
    `<div class="tile"><div class="k">Doors</div><div class="v" style="font-size:16px;margin-top:8px">${lock}</div></div>`);
} else {
  document.getElementById('car').innerHTML = `<div class="tile err">No live car data (${(D.car&&D.car.error)||'proxy/env not set'}). Start the proxy + set TESLA_VEHICLE_TAG/BASE.</div>`;
}
const cl=D.climate;
document.getElementById('climate').innerHTML = cl
  ? `Body <b>${cl.skin}C</b> + outside <b>${cl.outside}C</b> &rarr; suggested cabin <b style="color:var(--acc)">${cl.target}C</b>`
  : `<span class="err">Need a biometrics capture (skin temp) for a recommendation.</span>`;
if(D.bio){
  tiles('bio',[['Heart rate', D.bio.hr_now??'--','bpm'],['HR range', (D.bio.hr_min??'--')+'-'+(D.bio.hr_max??'--'),'bpm'],
    ['Skin temp', D.bio.skin??'--','C']]);
}
function sparkline(id, data, color){
  if(!data||!data.length) return;
  const c=document.getElementById(id),dpr=devicePixelRatio||1,w=c.clientWidth,h=c.clientHeight;
  c.width=w*dpr;c.height=h*dpr;const x=c.getContext('2d');x.scale(dpr,dpr);
  let lo=Math.min(...data),hi=Math.max(...data);if(lo===hi){lo--;hi++;}
  x.strokeStyle=css(color);x.lineWidth=1.8;x.beginPath();
  data.forEach((v,i)=>{const px=w*i/(data.length-1),py=8+(h-16)*(1-(v-lo)/(hi-lo));i?x.lineTo(px,py):x.moveTo(px,py);});
  x.stroke();
}
addEventListener('resize',()=>sparkline('hr',D.bio&&D.bio.hr,'--hr'));
sparkline('hr',D.bio&&D.bio.hr,'--hr');
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser(description="ProjWT biometric + vehicle dashboard.")
    ap.add_argument("--open", action="store_true", help="open the HTML in the browser")
    args = ap.parse_args()

    bio = latest_biometrics()
    car = car_snapshot()
    climate = None
    if bio and bio.get("skin") is not None:
        from smart_climate_PWT import comfort_target
        outside = car.get("outside_c") if car.get("ok") else 20.0
        target, _, _ = comfort_target(bio["skin"], outside if outside is not None else 20.0)
        climate = {"skin": bio["skin"], "outside": outside if outside is not None else 20.0, "target": target}

    data = {"asof": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "car": car, "bio": bio, "climate": climate}
    out = LOG_DIR / "dashboard_PWT.html"
    out.write_text(HTML.replace("__DATA__", json.dumps(data)), encoding="utf-8")
    print(f"Dashboard -> {out}")
    if car.get("ok"):
        print(f"  car: {car.get('name')}  battery {car.get('battery')}%  "
              f"inside {car.get('inside_c')}C / outside {car.get('outside_c')}C  "
              f"{'LOCKED' if car.get('locked') else 'UNLOCKED'}")
    else:
        print(f"  (no live car data: {car.get('error')})")
    if climate:
        print(f"  smart climate: body {climate['skin']}C + outside {climate['outside']}C -> {climate['target']}C")
    if args.open:
        webbrowser.open(out.as_uri())


if __name__ == "__main__":
    main()
