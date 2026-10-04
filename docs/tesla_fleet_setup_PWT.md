# ProjWT — Connecting the real car (Tesla Fleet API)

This is the honest, current setup to make `gesture_control_PWT.py --backend tesla`
drive **discrete** commands (lock/unlock/lights/horn/frunk/windows/climate/charge)
on your own Tesla. There is **no** third-party API for motion/Summon — that lives
only in Tesla's own app behind its proximity + continuous-press interlocks — so
this layer is deliberately discrete-only.

> Scope: everything below is for commanding **your own vehicle**, with your own
> Tesla account, in clear line-of-sight testing. Keep it there.

## The pieces

Tesla's Fleet API is OAuth2 + REST, and most vehicle commands on recent cars must
be **signed** with the Tesla Vehicle Command Protocol (plain REST returns
`unsigned commands not allowed`). The clean way to handle signing is Tesla's
`tesla-http-proxy`, which takes the same REST calls and signs them for you.

```
 your code  --REST-->  tesla-http-proxy  --signed BLE/HTTPS-->  Tesla cloud --> car
 (actuator)            (signs w/ your key)
```

## One-time setup

1. **Developer app** — at developer.tesla.com create an application. Note the
   `client_id` and `client_secret`. Set a redirect URI you control (can be
   `https://localhost:3000/callback` for local testing).

2. **Host a public key.** Generate an EC key pair (the proxy/`tesla-keygen` does
   this) and host the public key at exactly:
   ```
   https://<your-domain>/.well-known/appspecific/com.tesla.3p.public-key.pem
   ```
   (A cheap static host or a tunnel works; the domain just has to serve that path
   over HTTPS.)

3. **Register your partner account** (once), proving you own the domain:
   ```
   POST https://fleet-api.prd.na.vn.cloud.tesla.com/api/1/partner_accounts
   body: { "domain": "<your-domain>" }      (with a partner OAuth token)
   ```

4. **Pair the virtual key with the car.** Open on the owner's phone:
   ```
   https://tesla.com/_ak/<your-domain>
   ```
   and approve adding the key. This is what lets your signed commands be accepted.

## Per-session auth (OAuth 2.0 Authorization Code)

5. Send the owner through the authorize URL with scopes you need — for this demo:
   `openid offline_access vehicle_device_data vehicle_cmds vehicle_charging_cmds`.
6. Exchange the returned `code` for an `access_token` (+ `refresh_token`). The
   access token is what our actuator uses as the Bearer token. Refresh it with the
   refresh token when it expires (~8h).

## Point the code at it

7. Run the signing proxy locally (from Tesla's `vehicle-command` repo):
   ```
   tesla-http-proxy -key-file private.pem -cert cert.pem -port 4443
   ```
8. Find your vehicle tag: `GET /api/1/vehicles` → use the `id`/VIN.
9. Export the three env vars our `TeslaFleetActuator` reads, pointing the base at
   the **proxy** (not the cloud) so commands get signed:
   ```bash
   setx TESLA_FLEET_TOKEN "<access_token>"      # PowerShell: $env:TESLA_FLEET_TOKEN=...
   setx TESLA_VEHICLE_TAG "<vehicle id or VIN>"
   setx TESLA_FLEET_BASE  "https://localhost:4443"
   ```
10. Smoke-test without moving anything, dry first then live:
    ```
    python gesture_control_PWT.py --keyboard --backend tesla --dry      # prints the POSTs
    python gesture_control_PWT.py --keyboard --backend tesla            # real: d, f->flash, d
    ```
    Wake a cold car first if needed: `POST /api/1/vehicles/<tag>/wake_up`.

## Notes / gotchas

- **Signing is the usual wall.** If live commands return `unsigned commands not
  allowed` or `403`, your base URL isn't the proxy, or the virtual key isn't
  paired (step 4).
- **Region base URL** differs (NA/EU/CN); the proxy handles forwarding, so you
  mostly point at `localhost:4443`.
- **Rate limits** apply; the gesture cooldown keeps us well under them.
- **Discrete only, by design.** `vehicle_actuator_PWT.py` has no motion method and
  rejects anything outside its command table. The drive demo uses a simulator.
