"""Owner-controlled bounded local monitor of the real signed read core.

Uses the same account refresh and case persistence pipeline as the UI.
No exchange write, no cron service, no guarantee of production uptime.
"""
from __future__ import annotations
import threading
from datetime import datetime,timezone

def now():
    return datetime.now(timezone.utc).isoformat()

class Monitor:
    def __init__(self,refresh):
        self.refresh=refresh
        self._guard=threading.Lock()
        self._halt=threading.Event()
        self._worker=None
        self._enabled=False
        self._interval=45
        self._runs=0
        self._failed=0
        self._last_ok=None
        self._last_error=None
        self._started_at=None

    def status(self):
        with self._guard:
            alive=self._worker is not None and self._worker.is_alive()
            return {"enabled":self._enabled and alive,"interval_seconds":self._interval,
                    "runs":self._runs,"failed_reads":self._failed,
                    "last_success_at":self._last_ok,
                    "last_error_at":self._last_error,
                    "started_at":self._started_at,
                    "classification":"LOCAL_OPTIONAL_SIGNED_POLLING_NOT_PRODUCTION_MONITORING",
                    "exchange_writes_enabled":False,
                    "full_incident_recovery_proven":False}

    def start(self,interval_seconds=45):
        if type(interval_seconds) is not int or not 15<=interval_seconds<=3600:
            raise ValueError("interval must be 15..3600 seconds")
        with self._guard:
            if self._worker is not None and self._worker.is_alive():
                return {"already_running":True}
            self._interval=interval_seconds
            self._halt.clear()
            self._enabled=True
            self._started_at=now()
            self._worker=threading.Thread(target=self._work,name="PerplLocalSignedReadMonitor",daemon=True)
            self._worker.start()
        return {"already_running":False}

    def stop(self):
        with self._guard:
            self._enabled=False
            self._halt.set()
        return {"stopped":True}

    def _work(self):
        # First run immediately; operator can observe whether signing fails.
        while not self._halt.is_set():
            try:
                self.refresh()
                with self._guard:
                    self._runs+=1
                    self._last_ok=now()
            except Exception:
                # Never print secrets or raw signed API response to stdout.
                with self._guard:
                    self._failed+=1
                    self._last_error=now()
            if self._halt.wait(self._interval):
                break
        with self._guard:
            self._enabled=False
