import threading
import time
import pytest
from monitor_core import Monitor

def test_monitor_disabled_by_default_and_never_trades():
    monitor=Monitor(lambda: None)
    assert monitor.status()["enabled"] is False
    assert monitor.status()["exchange_writes_enabled"] is False

def test_operator_can_start_repeated_live_core_poll_and_stop():
    seen=threading.Event()
    count=[]
    def read():
        count.append("signed read pipeline called")
        seen.set()
    monitor=Monitor(read)
    assert monitor.start(15)["already_running"] is False
    assert seen.wait(1.0)
    assert monitor.start(15)["already_running"] is True
    deadline=time.monotonic()+1.0
    while monitor.status()["runs"]<1 and time.monotonic()<deadline:
        time.sleep(.01)
    assert monitor.status()["runs"]>=1
    monitor.stop()
    assert monitor.status()["enabled"] is False

def test_invalid_rate_limits_fail_closed():
    monitor=Monitor(lambda:None)
    for rate in (0,14,3601,1.5,True):
        with pytest.raises(ValueError):
            monitor.start(rate)
    assert monitor.status()["enabled"] is False

def test_failed_signed_read_does_not_become_live_success():
    seen=threading.Event()
    def broken():
        seen.set()
        raise ConnectionError("fake unavailable")
    mon=Monitor(broken)
    mon.start(15)
    assert seen.wait(1.0)
    end=time.monotonic()+1.0
    while mon.status()["failed_reads"]==0 and time.monotonic()<end:
        time.sleep(.01)
    assert mon.status()["failed_reads"]>=1
    assert mon.status()["runs"]==0
    assert mon.status()["last_success_at"] is None
    mon.stop()

def test_monitor_no_reconnect_or_external_write_claim():
    mon=Monitor(lambda:None)
    assert mon.status()["classification"]=="LOCAL_OPTIONAL_SIGNED_POLLING_NOT_PRODUCTION_MONITORING"
    assert mon.status()["full_incident_recovery_proven"] is False
