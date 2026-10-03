#!/usr/bin/env python3
r"""safety_state_machine_PWT.py — L3 fail-closed safety core (hardware-free).

This is the only component allowed to authorize physical motion. It is pure logic
over abstract inputs so it can be unit-tested with synthetic event streams (run
this file directly to execute the self-tests — no band, no actuator needed).

Inputs (feed from whatever sources exist):
  * gesture(kind, t)   — discrete gesture, e.g. "FLICK" from the WHOOP band
  * hold(active, t)    — the CONTINUOUS hold signal (e.g. phone-IMU HoldDetector);
                         must be refreshed faster than `hold_watchdog`
  * heartbeat(t)       — liveness of the continuous source link
  * tick(t)            — advance time so timeouts/watchdogs can fire

Outputs: a list of Command dicts the caller drains and sends to an actuator:
  {"cmd": "ARM"|"DISARM"|"MOVE"|"STOP", "t": <time>, "ttl": <seconds>}
MOVE commands carry a short TTL so a stale command can't be replayed.

States (fail-closed; default IDLE = stopped):
  IDLE --arm gesture (+healthy)--> ARMED --hold active--> HOLDING
  HOLDING --(hold drops | watchdog | heartbeat stale | disarm | fault)--> STOPPING
  ARMED --(arm timeout | disarm | heartbeat stale)--> IDLE
  STOPPING --(ramped to 0)--> IDLE   (cannot re-enter HOLDING without a fresh cycle)

Design ref: docs/architecture_PWT.md §5.
"""
from __future__ import annotations

from dataclasses import dataclass, field

IDLE, ARMED, HOLDING, STOPPING = "IDLE", "ARMED", "HOLDING", "STOPPING"


@dataclass
class SafetyConfig:
    arm_gesture: str = "FLICK"          # band gesture that arms / confirms
    disarm_gesture: str = "FLICK"       # same gesture while armed/holding = disarm
    hold_watchdog: float = 0.2          # s: max gap in hold-active before STOP
    heartbeat_timeout: float = 0.5      # s: max gap in continuous-source liveness
    arm_timeout: float = 10.0           # s: auto-disarm if no hold starts
    move_ttl: float = 0.2               # s: TTL stamped on each MOVE command
    stopping_ramp: float = 0.4          # s: STOPPING duration before IDLE
    move_interval: float = 0.1          # s: cadence of MOVE commands while holding


@dataclass
class SafetyStateMachine:
    cfg: SafetyConfig = field(default_factory=SafetyConfig)
    state: str = IDLE
    _t: float = 0.0
    _since: float = 0.0           # time we entered current state
    _last_hold_active: float = -1e9
    _last_heartbeat: float = -1e9
    _last_move: float = -1e9
    _armed_at: float = 0.0
    _out: list = field(default_factory=list)

    # ---- helpers -----------------------------------------------------------
    def _emit(self, cmd: str, ttl: float = 0.0):
        self._out.append({"cmd": cmd, "t": round(self._t, 4), "ttl": ttl})

    def _goto(self, state: str):
        if state != self.state:
            self.state = state
            self._since = self._t

    def drain(self):
        out, self._out = self._out, []
        return out

    def _heartbeat_ok(self) -> bool:
        return (self._t - self._last_heartbeat) <= self.cfg.heartbeat_timeout

    # ---- inputs ------------------------------------------------------------
    def heartbeat(self, t: float):
        self._t = t
        self._last_heartbeat = t

    def hold(self, active: bool, t: float):
        self._t = t
        if active:
            self._last_hold_active = t
            # a live hold also proves the continuous source is alive
            self._last_heartbeat = t
            if self.state == ARMED:
                self._goto(HOLDING)
                self._last_move = -1e9

    def gesture(self, kind: str, t: float):
        self._t = t
        if self.state == IDLE:
            if kind == self.cfg.arm_gesture:
                self._goto(ARMED)
                self._armed_at = t
                self._emit("ARM")
        elif self.state in (ARMED, HOLDING):
            if kind == self.cfg.disarm_gesture:
                self._emit("DISARM")
                self._begin_stopping()

    def _begin_stopping(self):
        if self.state in (ARMED,):
            # not moving yet -> straight to IDLE
            self._emit("STOP")
            self._goto(IDLE)
        elif self.state in (HOLDING, STOPPING):
            self._emit("STOP")
            self._goto(STOPPING)

    # ---- time advance (drives watchdogs/timeouts/among) --------------------
    def tick(self, t: float):
        self._t = t
        if self.state == ARMED:
            if (t - self._armed_at) >= self.cfg.arm_timeout or not self._heartbeat_ok():
                self._emit("STOP")
                self._goto(IDLE)
        elif self.state == HOLDING:
            hold_fresh = (t - self._last_hold_active) <= self.cfg.hold_watchdog
            if not hold_fresh or not self._heartbeat_ok():
                self._begin_stopping()
            else:
                if (t - self._last_move) >= self.cfg.move_interval:
                    self._last_move = t
                    self._emit("MOVE", ttl=self.cfg.move_ttl)
        elif self.state == STOPPING:
            if (t - self._since) >= self.cfg.stopping_ramp:
                self._goto(IDLE)


# --------------------------------------------------------------------------- tests
def _run(sm, script):
    """script: list of (op, *args). Returns all emitted commands."""
    cmds = []
    for op, *a in script:
        getattr(sm, op)(*a)
        cmds += sm.drain()
    return cmds


def _kinds(cmds):
    return [c["cmd"] for c in cmds]


def _self_test():
    cfg = SafetyConfig()

    # 1) happy path: arm -> hold -> MOVEs -> release -> STOP -> IDLE
    sm = SafetyStateMachine(cfg=cfg)
    cmds = _run(sm, [
        ("gesture", "FLICK", 0.0),       # ARM
        ("hold", True, 0.1),             # -> HOLDING
        ("tick", 0.2), ("tick", 0.3), ("tick", 0.4),  # MOVEs (hold still fresh? needs refresh)
    ])
    # hold went stale after 0.1 (+watchdog .2) => by t=0.4 it should be STOPPING/STOP
    assert "ARM" in _kinds(cmds)
    assert sm.state in (STOPPING, IDLE)

    # 2) continuous hold produces repeated MOVEs, then release stops
    sm = SafetyStateMachine(cfg=cfg)
    script = [("gesture", "FLICK", 0.0)]
    t = 0.05
    while t < 0.6:                       # refresh hold every 0.05s (< watchdog)
        script.append(("hold", True, t))
        script.append(("tick", t))
        t += 0.05
    cmds = _run(sm, script)
    assert sm.state == HOLDING
    assert _kinds(cmds).count("MOVE") >= 3, _kinds(cmds)
    # now stop refreshing hold; watchdog must stop us
    cmds2 = _run(sm, [("tick", 0.9)])
    assert "STOP" in _kinds(cmds2)
    assert sm.state in (STOPPING, IDLE)

    # 3) hold without arming does nothing (fail-closed)
    sm = SafetyStateMachine(cfg=cfg)
    cmds = _run(sm, [("hold", True, 0.0), ("tick", 0.1)])
    assert sm.state == IDLE and "MOVE" not in _kinds(cmds)

    # 4) disarm gesture while holding stops immediately
    sm = SafetyStateMachine(cfg=cfg)
    cmds = _run(sm, [("gesture", "FLICK", 0.0), ("hold", True, 0.05), ("tick", 0.05),
                     ("gesture", "FLICK", 0.06)])
    assert "DISARM" in _kinds(cmds) and "STOP" in _kinds(cmds)
    assert sm.state in (STOPPING, IDLE)

    # 5) arm timeout: armed but never holds -> auto back to IDLE
    sm = SafetyStateMachine(cfg=cfg)
    cmds = _run(sm, [("gesture", "FLICK", 0.0), ("tick", cfg.arm_timeout + 0.1)])
    assert sm.state == IDLE and "STOP" in _kinds(cmds)

    # 6) heartbeat loss while holding -> STOP (signal-loss fail-safe)
    sm = SafetyStateMachine(cfg=cfg)
    cmds = _run(sm, [("gesture", "FLICK", 0.0), ("hold", True, 0.05), ("tick", 0.05)])
    assert sm.state == HOLDING
    # advance time past heartbeat_timeout WITHOUT hold/heartbeat refresh
    cmds2 = _run(sm, [("tick", 0.05 + cfg.heartbeat_timeout + 0.05)])
    assert "STOP" in _kinds(cmds2) and sm.state in (STOPPING, IDLE)

    # 7) STOPPING cannot jump back to HOLDING without a fresh arm
    sm = SafetyStateMachine(cfg=cfg)
    _run(sm, [("gesture", "FLICK", 0.0), ("hold", True, 0.05), ("tick", 0.05)])
    _run(sm, [("tick", 0.9)])            # -> STOPPING (hold stale)
    assert sm.state == STOPPING
    _run(sm, [("hold", True, 0.95), ("tick", 0.96)])  # hold during STOPPING ignored
    assert sm.state in (STOPPING, IDLE)
    assert sm.state != HOLDING

    print("safety_state_machine_PWT self-test OK — all fail-safes pass (7 cases).")


if __name__ == "__main__":
    _self_test()
