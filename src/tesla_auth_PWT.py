#!/usr/bin/env python3
r"""tesla_auth_PWT.py — Tesla Fleet API onboarding, scripted (no extra deps).

Walks the one-time + per-session auth so you don't hand-craft HTTP calls:

    register   one-time: tell Tesla to fetch your hosted public key (partner account)
    login      OAuth: open the browser, capture the code on localhost, save tokens
    refresh    renew the access token from the saved refresh token
    vehicles   list your cars (get the vehicle tag for TESLA_VEHICLE_TAG)
    envhint    print the exact env vars to set for gesture_control_PWT.py

Reads these env vars (set them in your shell first; NEVER paste secrets in chat):
    TESLA_CLIENT_ID       from your Fleet API app
    TESLA_CLIENT_SECRET   from your Fleet API app
    TESLA_DOMAIN          hamza-khan-algonquin.github.io   (where the key is hosted)
    TESLA_REDIRECT_URI    http://localhost:3000/callback   (default)
    TESLA_REGION_BASE     https://fleet-api.prd.na.vn.cloud.tesla.com (NA default)

Tokens are saved to ../secrets/tesla_tokens_PWT.json (gitignored). The access token
lasts ~8h; use `refresh` after that.
"""
import argparse
import http.server
import json
import os
import secrets as pysecrets
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

AUTH = "https://auth.tesla.com/oauth2/v3"
SCOPES = "openid offline_access vehicle_device_data vehicle_cmds vehicle_charging_cmds"
TOKENS = Path(__file__).resolve().parent.parent / "secrets" / "tesla_tokens_PWT.json"


def _env(name, default=None, required=False):
    v = os.environ.get(name, default)
    if required and not v:
        raise SystemExit(f"set {name} first (see the header of this script)")
    return v


def _post_form(url, fields, token=None):
    data = urllib.parse.urlencode(fields).encode()
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, method="POST", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def _post_json(url, body, token):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "{}")


def _get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def _save(tok):
    TOKENS.parent.mkdir(exist_ok=True)
    TOKENS.write_text(json.dumps(tok, indent=2))
    print(f"saved tokens -> {TOKENS}")


def _load():
    if not TOKENS.exists():
        raise SystemExit("no saved tokens — run `login` first")
    return json.loads(TOKENS.read_text())


def partner_token():
    """client_credentials grant -> a token for partner-account calls."""
    base = _env("TESLA_REGION_BASE", "https://fleet-api.prd.na.vn.cloud.tesla.com")
    tok = _post_form(f"{AUTH}/token", {
        "grant_type": "client_credentials",
        "client_id": _env("TESLA_CLIENT_ID", required=True),
        "client_secret": _env("TESLA_CLIENT_SECRET", required=True),
        "scope": SCOPES, "audience": base,
    })
    return tok["access_token"], base


def cmd_register(_):
    token, base = partner_token()
    domain = _env("TESLA_DOMAIN", required=True)
    out = _post_json(f"{base}/api/1/partner_accounts", {"domain": domain}, token)
    print("partner registration response:")
    print(json.dumps(out, indent=2))
    print(f"\nTesla will now fetch https://{domain}/.well-known/appspecific/"
          "com.tesla.3p.public-key.pem . If 'public_key' appears above, it worked.")


def cmd_login(_):
    cid = _env("TESLA_CLIENT_ID", required=True)
    redirect = _env("TESLA_REDIRECT_URI", "http://localhost:3000/callback")
    state = pysecrets.token_urlsafe(16)
    q = urllib.parse.urlencode({
        "response_type": "code", "client_id": cid, "redirect_uri": redirect,
        "scope": SCOPES, "state": state})
    url = f"{AUTH}/authorize?{q}"
    code_box = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            p = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(p.query)
            if "code" in qs:
                code_box["code"] = qs["code"][0]
                code_box["state"] = qs.get("state", [""])[0]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ProjWT: authorization received. You can close this tab.")
            else:
                self.send_response(400)
                self.end_headers()

    port = int(urllib.parse.urlparse(redirect).port or 3000)
    print(f"Opening browser to Tesla login...\nIf it doesn't open, paste this URL:\n{url}\n")
    try:
        webbrowser.open(url)
    except Exception:  # noqa: BLE001
        pass
    srv = http.server.HTTPServer(("localhost", port), Handler)
    print(f"Waiting for the redirect on {redirect} ...")
    while "code" not in code_box:
        srv.handle_request()
    if code_box.get("state") != state:
        raise SystemExit("state mismatch — aborting (possible CSRF)")

    tok = _post_form(f"{AUTH}/token", {
        "grant_type": "authorization_code",
        "client_id": cid, "client_secret": _env("TESLA_CLIENT_SECRET", required=True),
        "code": code_box["code"], "redirect_uri": redirect,
        "audience": _env("TESLA_REGION_BASE", "https://fleet-api.prd.na.vn.cloud.tesla.com"),
    })
    _save(tok)
    print("Login OK. Access token valid ~8h; run `refresh` later to renew.")


def cmd_refresh(_):
    tok = _load()
    new = _post_form(f"{AUTH}/token", {
        "grant_type": "refresh_token", "client_id": _env("TESLA_CLIENT_ID", required=True),
        "refresh_token": tok["refresh_token"], "scope": SCOPES})
    # keep the refresh token if the response omits a new one
    new.setdefault("refresh_token", tok["refresh_token"])
    _save(new)
    print("access token refreshed.")


def cmd_vehicles(_):
    tok = _load()
    base = _env("TESLA_REGION_BASE", "https://fleet-api.prd.na.vn.cloud.tesla.com")
    out = _get(f"{base}/api/1/vehicles", tok["access_token"])
    vs = out.get("response", [])
    if not vs:
        print("no vehicles returned (is the car on this Tesla account?)")
        return
    print(f"{len(vs)} vehicle(s):")
    for v in vs:
        print(f"  name={v.get('display_name')!r}  id={v.get('id')}  "
              f"vin={v.get('vin')}  state={v.get('state')}")
    print("\nUse the `id` (or VIN) as TESLA_VEHICLE_TAG.")


def cmd_envhint(_):
    base = _env("TESLA_REGION_BASE", "https://fleet-api.prd.na.vn.cloud.tesla.com")
    tok = _load() if TOKENS.exists() else {}
    print("# add to your shell (PowerShell uses $env:NAME=\"...\"):")
    print(f'export TESLA_FLEET_TOKEN="{tok.get("access_token", "<run login first>")}"')
    print('export TESLA_VEHICLE_TAG="<id from `vehicles`>"')
    print('# point BASE at your signing proxy for commands that need signing:')
    print('export TESLA_FLEET_BASE="https://localhost:4443"')
    print(f'# (direct, unsigned test only — older cars): TESLA_FLEET_BASE="{base}"')


def main():
    ap = argparse.ArgumentParser(description="Tesla Fleet API onboarding (ProjWT).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in [("register", cmd_register), ("login", cmd_login),
                     ("refresh", cmd_refresh), ("vehicles", cmd_vehicles),
                     ("envhint", cmd_envhint)]:
        sub.add_parser(name).set_defaults(fn=fn)
    args = ap.parse_args()
    try:
        args.fn(args)
    except urllib.error.HTTPError as e:  # noqa: BLE001
        print(f"HTTP {e.code}: {e.read().decode(errors='ignore')[:500]}")


if __name__ == "__main__":
    main()
