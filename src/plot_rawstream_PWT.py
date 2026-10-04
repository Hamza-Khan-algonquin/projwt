#!/usr/bin/env python3
r"""plot_rawstream_PWT.py — render a decoded rawstream CSV into a standalone HTML dashboard.

Reads a logs/rawstream_*_PWT.csv (from decode_rawstream_PWT.py) and writes a single
self-contained .html file next to it: the biometric + orientation feed drawn with
inline <canvas> and zero external requests, so it opens offline in any browser and
nothing leaves your machine. This is the seed of the ProjWT biometric dashboard.

Usage:
    python plot_rawstream_PWT.py                      # newest rawstream CSV
    python plot_rawstream_PWT.py ..\logs\rawstream_20261004_183000_PWT.csv
"""
import argparse
import csv
import json
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ProjWT Biometrics</title>
<style>
  :root{color-scheme:dark;--bg:#0c0f17;--panel:#151a28;--ink:#e8edf7;--mut:#8894ad;
        --hr:#ff5d73;--gx:#4cc9f0;--gy:#80ffdb;--gz:#ffd166;--mag:#b8c0d9;--grid:#232a3d}
  *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);
    font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;padding:24px}
  h1{font-size:19px;margin:0 0 2px} .sub{color:var(--mut);font-size:13px;margin-bottom:18px}
  .tiles{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:20px}
  .tile{background:var(--panel);border:1px solid var(--grid);border-radius:12px;
        padding:12px 16px;min-width:120px} .tile .k{color:var(--mut);font-size:12px}
  .tile .v{font-size:22px;font-weight:600;margin-top:2px} .tile .u{font-size:12px;color:var(--mut)}
  .card{background:var(--panel);border:1px solid var(--grid);border-radius:12px;padding:14px 16px;margin-bottom:16px}
  .card h2{font-size:14px;margin:0 0 10px;font-weight:600} .card h2 small{color:var(--mut);font-weight:400}
  canvas{width:100%;height:220px;display:block}
  .legend{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--mut);margin-top:8px}
  .legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:middle}
  footer{color:var(--mut);font-size:12px;margin-top:8px}
</style></head><body>
<h1>ProjWT — WHOOP 4.0 biometric capture</h1>
<div class="sub" id="sub"></div>
<div class="tiles" id="tiles"></div>
<div class="card"><h2>Heart rate <small>bpm, per second</small></h2><canvas id="hr"></canvas></div>
<div class="card"><h2>Orientation <small>gravity vector, g</small></h2><canvas id="g"></canvas>
  <div class="legend"><span><i style="background:var(--gx)"></i>gx</span>
  <span><i style="background:var(--gy)"></i>gy</span><span><i style="background:var(--gz)"></i>gz</span>
  <span><i style="background:var(--mag)"></i>|g|</span></div></div>
<footer>Decoded locally from banked HISTORICAL_DATA (v12) over the reverse-engineered BLE offload path. Private — not for sharing.</footer>
<script>
const DATA = __DATA__;
const css = k => getComputedStyle(document.documentElement).getPropertyValue(k).trim();
function draw(id, series, ylabel, fmt){
  const c=document.getElementById(id), dpr=devicePixelRatio||1;
  const w=c.clientWidth, h=c.clientHeight; c.width=w*dpr; c.height=h*dpr;
  const x=c.getContext('2d'); x.scale(dpr,dpr);
  const padL=44, padB=20, padT=8, padR=8, n=DATA.t.length;
  const all=series.flatMap(s=>s.v.filter(v=>v!=null));
  let lo=Math.min(...all), hi=Math.max(...all); if(lo===hi){lo-=1;hi+=1;}
  const pad=(hi-lo)*0.08; lo-=pad; hi+=pad;
  const X=i=>padL+(w-padL-padR)*(n<2?0:i/(n-1));
  const Y=v=>padT+(h-padT-padB)*(1-(v-lo)/(hi-lo));
  x.strokeStyle=css('--grid'); x.fillStyle=css('--mut'); x.font='11px sans-serif'; x.lineWidth=1;
  for(let g=0;g<=4;g++){const v=lo+(hi-lo)*g/4, yy=Y(v);
    x.beginPath();x.moveTo(padL,yy);x.lineTo(w-padR,yy);x.stroke();
    x.fillText(fmt(v), 4, yy+3);}
  for(const s of series){x.strokeStyle=css(s.c);x.lineWidth=1.6;x.beginPath();let st=false;
    for(let i=0;i<n;i++){const v=s.v[i]; if(v==null){st=false;continue;}
      const px=X(i),py=Y(v); if(!st){x.moveTo(px,py);st=true;}else x.lineTo(px,py);} x.stroke();}
}
const sub=document.getElementById('sub');
sub.textContent=`${DATA.n} records · ${DATA.span} · HR ${DATA.hrmin}–${DATA.hrmax} (mean ${DATA.hrmean}) bpm`;
const tiles=[['Records',DATA.n,''],['Duration',DATA.mins+' min',''],
  ['HR mean',DATA.hrmean,'bpm'],['HR range',DATA.hrmin+'–'+DATA.hrmax,'bpm'],
  ['Skin temp',DATA.temp,'°C'],['|g| mean',DATA.gmean,'g']];
document.getElementById('tiles').innerHTML=tiles.map(t=>
  `<div class="tile"><div class="k">${t[0]}</div><div class="v">${t[1]} <span class="u">${t[2]}</span></div></div>`).join('');
addEventListener('resize',render);
function render(){
  draw('hr',[{v:DATA.hr,c:'--hr'}],'bpm',v=>v.toFixed(0));
  draw('g',[{v:DATA.gx,c:'--gx'},{v:DATA.gy,c:'--gy'},{v:DATA.gz,c:'--gz'},{v:DATA.gmag,c:'--mag'}],'g',v=>v.toFixed(2));
}
render();
</script></body></html>
"""


def fnum(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def main() -> None:
    ap = argparse.ArgumentParser(description="Render a rawstream CSV to a standalone HTML dashboard.")
    ap.add_argument("csvfile", nargs="?", default=None)
    args = ap.parse_args()
    if args.csvfile:
        path = Path(args.csvfile)
    else:
        csvs = sorted(LOG_DIR.glob("rawstream_*_PWT.csv"))
        if not csvs:
            raise SystemExit(f"no rawstream_*_PWT.csv in {LOG_DIR} (run decode_rawstream_PWT.py first)")
        path = csvs[-1]
    if not path.exists():
        raise SystemExit(f"not found: {path}")

    t, hr, gx, gy, gz, gmag, temps = [], [], [], [], [], [], []
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            t.append(row["unix"])
            hr.append(fnum(row["hr"]))
            gx.append(fnum(row["gx"])); gy.append(fnum(row["gy"]))
            gz.append(fnum(row["gz"])); gmag.append(fnum(row["gmag"]))
            tr = fnum(row.get("skin_temp_raw"))
            if tr:
                c = tr * 0.04
                if 20 <= c <= 45:
                    temps.append(c)
    if not t:
        raise SystemExit("empty CSV")

    hrv = [v for v in hr if v is not None]
    gm = [v for v in gmag if v is not None]
    span = int(float(t[-1]) - float(t[0])) if len(t) > 1 else 0
    data = {
        "n": len(t), "t": t, "hr": hr, "gx": gx, "gy": gy, "gz": gz, "gmag": gmag,
        "hrmin": int(min(hrv)) if hrv else 0, "hrmax": int(max(hrv)) if hrv else 0,
        "hrmean": round(sum(hrv) / len(hrv)) if hrv else 0,
        "gmean": round(sum(gm) / len(gm), 3) if gm else 0,
        "temp": round(sum(temps) / len(temps), 1) if temps else "--",
        "span": f"{span}s (~{span/60:.1f} min)", "mins": round(span / 60, 1),
    }
    out = path.with_suffix(".html")
    out.write_text(HTML.replace("__DATA__", json.dumps(data)), encoding="utf-8")
    print(f"Dashboard written: {out}")
    print("Open it in any browser — fully offline, no data leaves your machine.")


if __name__ == "__main__":
    main()
