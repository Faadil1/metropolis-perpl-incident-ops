"""Persistent local operator incident ledger. Exchange writes are intentionally NOT implemented."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
import os
import sqlite3
import uuid
from pathlib import Path

STATUS = {0:'UNSPECIFIED',1:'PENDING',2:'OPEN',3:'PARTIALLY_FILLED',4:'FILLED',5:'CANCELED',6:'EXPIRED',7:'FAILED',8:'UNTRIGGERED',9:'TRIGGERED',10:'EXECUTED'}
TERMINAL_ORDER_STATES = {4,5,6,10}
MANUAL = 'MANUAL_UNVERIFIED'
LIVE = 'PERPL_AUTHENTICATED_READ'
WS_LIVE = 'PERPL_WS_AUTHENTICATED'

def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def now():
    return datetime.now(timezone.utc).isoformat()

class IncidentStore:
    def __init__(self, path):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass  # Windows file permissions require platform-specific protection
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS incidents(
          id TEXT PRIMARY KEY, network TEXT NOT NULL, account_id INTEGER NOT NULL,
          rq INTEGER NOT NULL, market_id INTEGER NOT NULL, status TEXT NOT NULL,
          order_status INTEGER, order_id INTEGER,
          has_definitive_ack INTEGER NOT NULL DEFAULT 0,
          frame_seq INTEGER, ws_gap INTEGER NOT NULL DEFAULT 0,
          last_source TEXT NOT NULL DEFAULT 'NONE', last_refresh_at TEXT,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          UNIQUE(network, account_id, rq)
        );
        CREATE TABLE IF NOT EXISTS incident_events(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          incident_id TEXT NOT NULL REFERENCES incidents(id),
          kind TEXT NOT NULL, source TEXT NOT NULL, payload_sha256 TEXT NOT NULL,
          payload_json TEXT NOT NULL, prev_hash TEXT NOT NULL, event_hash TEXT NOT NULL,
          created_at TEXT NOT NULL,
          UNIQUE(incident_id, kind, payload_sha256, source)
        );
        CREATE TABLE IF NOT EXISTS account_snapshots(
          incident_id TEXT NOT NULL REFERENCES incidents(id), kind TEXT NOT NULL,
          raw_json TEXT NOT NULL, source TEXT NOT NULL, observed_at TEXT NOT NULL,
          PRIMARY KEY(incident_id, kind)
        );
        CREATE TABLE IF NOT EXISTS approvals(
          id TEXT PRIMARY KEY, incident_id TEXT NOT NULL REFERENCES incidents(id),
          action TEXT NOT NULL, owner_note TEXT NOT NULL, state TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        """)

    def create(self, network, account_id, rq, market_id):
        if network != 'testnet':
            raise ValueError('only testnet supported')
        if not all(type(x) is int and x >= 0 for x in (account_id, rq, market_id)) or account_id == 0 or rq == 0:
            raise ValueError('account_id and rq must be positive integers; market_id nonnegative')
        ident = str(uuid.uuid4())
        t = now()
        self.db.execute('INSERT INTO incidents(id,network,account_id,rq,market_id,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',
                        (ident,network,account_id,rq,market_id,'SUBMISSION_UNCERTAIN',t,t))
        self.log(ident,'INCIDENT_CREATED',MANUAL,{'network':network,'account_id':account_id,'rq':rq,'market_id':market_id})
        return self.get(ident)

    def get(self, ident):
        row = self.db.execute('SELECT * FROM incidents WHERE id=?',(ident,)).fetchone()
        if row is None:
            raise KeyError('incident not found')
        result = dict(row)
        result['plan'] = self.plan(ident)
        return result

    def all(self):
        rows = self.db.execute('SELECT id FROM incidents ORDER BY created_at DESC LIMIT 200').fetchall()
        return [self.get(row['id']) for row in rows]

    def log(self, ident, kind, source, payload):
        if not self.db.execute('SELECT 1 FROM incidents WHERE id=?',(ident,)).fetchone():
            raise KeyError(ident)
        data = canon(payload)
        sha = hashlib.sha256(data.encode()).hexdigest()
        if self.db.execute('SELECT 1 FROM incident_events WHERE incident_id=? AND kind=? AND source=? AND payload_sha256=?',
                           (ident,kind,source,sha)).fetchone():
            return False
        last = self.db.execute('SELECT event_hash FROM incident_events WHERE incident_id=? ORDER BY id DESC LIMIT 1',(ident,)).fetchone()
        prev = last['event_hash'] if last else 'GENESIS'
        timestamp = now()
        value = hashlib.sha256(f'{ident}\n{kind}\n{source}\n{sha}\n{prev}\n{timestamp}'.encode()).hexdigest()
        self.db.execute('INSERT INTO incident_events(incident_id,kind,source,payload_sha256,payload_json,prev_hash,event_hash,created_at) VALUES(?,?,?,?,?,?,?,?)',
                        (ident,kind,source,sha,data,prev,value,timestamp))
        return True

    def ledger(self, ident):
        return [dict(row) for row in self.db.execute('SELECT * FROM incident_events WHERE incident_id=? ORDER BY id',(ident,)).fetchall()]

    def verify_ledger(self, ident):
        prev = 'GENESIS'
        for item in self.ledger(ident):
            data_hash = hashlib.sha256(item['payload_json'].encode()).hexdigest()
            if item['prev_hash'] != prev or data_hash != item['payload_sha256']:
                return False
            value = hashlib.sha256(f"{ident}\n{item['kind']}\n{item['source']}\n{item['payload_sha256']}\n{prev}\n{item['created_at']}".encode()).hexdigest()
            if value != item['event_hash']:
                return False
            prev = value
        return True

    def _transition(self, ident, status, source, **fields):
        names = ['status','last_source','updated_at'] + list(fields)
        vals = [status,source,now()] + list(fields.values())
        self.db.execute('UPDATE incidents SET '+','.join(f'{n}=?' for n in names)+' WHERE id=?',(*vals,ident))

    def apply_frame(self, ident, frame, source=MANUAL):
        if source not in (MANUAL, WS_LIVE):
            raise ValueError('invalid provenance')
        incident = self.get(ident)
        mt = frame.get('mt')
        if source == MANUAL and incident['last_source'] in (LIVE, WS_LIVE):
            self.log(ident,'MANUAL_FIXTURE_NOT_APPLIED_OVER_LIVE_STATE',MANUAL,frame)
            return self.get(ident)
        if mt == 24:
            updates = frame.get('d')
            if not isinstance(updates,list):
                raise ValueError('mt:24 requires d[]')
            for item in updates:
                if not isinstance(item,dict) or item.get('rq') != incident['rq'] or item.get('acc') != incident['account_id'] or item.get('mkt') != incident['market_id']:
                    continue
                state = item.get('st')
                if state not in STATUS:
                    continue
                current = self.get(ident)
                if state == 7 and current['has_definitive_ack']:
                    self.log(ident,'LATE_FAILURE_IGNORED',source,item)
                    continue
                if not self.log(ident,'ORDER_UPDATE',source,item):
                    continue
                oid = item.get('oid')
                if state == 7:
                    if current['order_status'] is None or current['order_status'] == 7:
                        self._transition(ident,'EXCHANGE_REJECTED',source,order_status=7)
                elif state == 1:
                    if not current['has_definitive_ack']:
                        self._transition(ident,'SUBMISSION_UNCERTAIN',source,order_status=1)
                else:
                    if current['order_status'] in TERMINAL_ORDER_STATES and current['order_status'] != state:
                        self.log(ident,'CONFLICTING_TERMINAL_UPDATE',source,{'prior_st':current['order_status'],'incoming_st':state})
                        self._transition(ident,'CONFLICT_RECONCILE_REQUIRED',source)
                        continue
                    status = {2:'KNOWN_OPEN',3:'PARTIAL_FILL_REVIEW',4:'ORDER_FILLED_CONSEQUENCE_UNVERIFIED',
                              5:'ORDER_CANCELED',6:'ORDER_EXPIRED',8:'TRIGGER_WAITING',9:'TRIGGERED_RECONCILE',
                              10:'EXECUTED_RECONCILE'}.get(state,'RECONCILING')
                    values = {'order_status':state,'has_definitive_ack':1}
                    if isinstance(oid,int):
                        values['order_id'] = oid
                    self._transition(ident,status,source,**values)
        elif mt == 19:
            if source != WS_LIVE:
                self.log(ident,'MANUAL_SEQUENCE_UNVERIFIED',MANUAL,frame)
                return self.get(ident)
            sn = frame.get('sn')
            if type(sn) is int:
                self.log(ident,'WS_SEQUENCE_ANCHOR',source,{'sn':sn})
                self._transition(ident,incident['status'],source,frame_seq=sn,ws_gap=0)
        elif mt == 100:
            if source != WS_LIVE:
                self.log(ident,'MANUAL_HEARTBEAT_UNVERIFIED',MANUAL,frame)
                return self.get(ident)
            sn = frame.get('sn')
            current = self.get(ident)
            if type(sn) is int and current['frame_seq'] is not None:
                if sn != current['frame_seq']+1:
                    self.log(ident,'WS_SEQUENCE_GAP',source,{'previous':current['frame_seq'],'new':sn})
                    self._transition(ident,'STREAM_STALE_RECONCILE_REQUIRED',source,frame_seq=sn,ws_gap=1)
                elif not current['ws_gap']:
                    self._transition(ident,current['status'],source,frame_seq=sn)
        elif mt in (23,26):
            if source == MANUAL:
                self.log(ident,'MANUAL_SNAPSHOT_UNVERIFIED',MANUAL,frame)
                return self.get(ident)
            self._snapshot(ident,{23:'orders',26:'positions'}[mt],frame,source)
        else:
            self.log(ident,'FRAME_IGNORED_UNSUPPORTED',source,{'mt':mt})
        return self.get(ident)

    def _snapshot(self, ident, kind, frame, source):
        expected = {'wallet':19,'orders':23,'positions':26}[kind]
        data = frame.get('d')
        if frame.get('mt') != expected or not isinstance(data, dict if kind=='wallet' else list):
            raise ValueError('snapshot schema uncertain; must remain UNKNOWN')
        timestamp = now()
        self.db.execute('INSERT INTO account_snapshots(incident_id,kind,raw_json,source,observed_at) VALUES(?,?,?,?,?) ON CONFLICT(incident_id,kind) DO UPDATE SET raw_json=excluded.raw_json,source=excluded.source,observed_at=excluded.observed_at',
                        (ident,kind,canon(frame),source,timestamp))
        self.log(ident,'SNAPSHOT_'+kind.upper(),source,{'mt':expected,'sha256':hashlib.sha256(canon(frame).encode()).hexdigest(),'observed_at':timestamp})

    def _reconcile_history(self, ident, snapshots, source):
        """Positive evidence may resolve uncertainty; absence in one history page never does."""
        inc = self.get(ident)
        history = snapshots.get('order_history')
        fills = snapshots.get('fills')
        if history is None or fills is None:
            self.log(ident, 'HISTORY_UNAVAILABLE_KEEP_UNKNOWN', source,
                     {'reason':'authenticated history not supplied'})
            return
        for label, page in (('order_history', history), ('fills', fills)):
            if not isinstance(page, dict) or not isinstance(page.get('d'),list):
                raise ValueError(f'Invalid {label} history schema')
            self.log(ident, 'HISTORY_PAGE_'+label.upper(), source,
                     {'count':len(page['d']), 'more_pages':bool(page.get('np')),
                      'sha256':hashlib.sha256(canon(page).encode()).hexdigest()})
        matches = [o for o in history['d'] if
                   isinstance(o,dict) and
                   o.get('rq')==inc['rq'] and o.get('acc')==inc['account_id'] and
                   o.get('mkt')==inc['market_id']]
        if not matches:
            self.log(ident,'HISTORY_NO_MATCH_NOT_PROOF_OF_FAILURE',source,
                     {'more_pages':bool(history.get('np')),'rq':inc['rq']})
            return
        event=matches[0]  # Perpl history is newest-first. Only positive events can resolve.
        state=event.get('st')
        oid=event.get('oid')
        self.log(ident,'EXCHANGE_ORDER_HISTORY_MATCH',source,
                 {'rq':inc['rq'],'acc':inc['account_id'],'mkt':inc['market_id'],
                  'oid':oid,'order_status':state})
        if state not in STATUS:
            return
        if state == 4:
            matched_fill = any(isinstance(f,dict) and type(oid) is int
                               and f.get('oid')==oid and f.get('acc')==inc['account_id']
                               and f.get('mkt')==inc['market_id'] for f in fills['d'])
            if matched_fill:
                self.log(ident,'FILL_HISTORY_CONFIRMED',source,
                         {'oid':oid,'rq':inc['rq'],'proof':'venue fill-history first page'})
            status = ('FILL_CONFIRMED_POSITION_RECONCILIATION_NEEDED' if matched_fill
                      else 'ORDER_FILLED_CONSEQUENCE_UNVERIFIED')
        elif state in (2,3,5,6,7,8,9,10):
            status={2:'KNOWN_OPEN',3:'PARTIAL_FILL_REVIEW',5:'ORDER_CANCELED',
                    6:'ORDER_EXPIRED',7:'EXCHANGE_REJECTED',8:'TRIGGER_WAITING',
                    9:'TRIGGERED_RECONCILE',10:'EXECUTED_RECONCILE'}[state]
        else:
            return
        fields={'order_status':state,'has_definitive_ack':int(state not in (7,)),
                'last_source':source}
        if type(oid) is int:
            fields['order_id']=oid
        self._transition(ident,status,source,**{k:v for k,v in fields.items() if k!='last_source'})

    def refresh_snapshots(self, ident, snapshots, source=LIVE):
        if source != LIVE:
            raise ValueError('refresh requires authenticated read transport')
        for kind in ('wallet','orders','positions'):
            if kind not in snapshots:
                raise ValueError('all snapshots required')
            self._snapshot(ident,kind,snapshots[kind],source)
        self._reconcile_history(ident,snapshots,source)
        current = self.get(ident)
        self.db.execute('UPDATE incidents SET last_refresh_at=?,last_source=?,updated_at=? WHERE id=?',(now(),source,now(),ident))
        if current['ws_gap']:
            self.log(ident,'GAP_RECOVERY_REQUIRES_WS_SEQUENCE_ANCHOR',source,{'reason':'reconnect trading WS'})
        elif current['status']=='SUBMISSION_UNCERTAIN':
            self.log(ident,'UNKNOWN_ACK_PRESERVED',source,{'reason':'snapshots cannot establish fill without definitive rq status'})
        return self.get(ident)

    def plan(self, ident):
        inc = self.db.execute('SELECT * FROM incidents WHERE id=?',(ident,)).fetchone()
        if inc is None:
            raise KeyError(ident)
        inc = dict(inc)
        if inc['ws_gap']:
            return {'action':'RECONNECT_AND_RECONCILE','permission':'READ_ONLY','reason':'websocket sequence gap','can_cancel':False}
        if inc['status'] in ('KNOWN_OPEN','PARTIAL_FILL_REVIEW'):
            row = self.db.execute("SELECT raw_json,source FROM account_snapshots WHERE incident_id=? AND kind='orders'",(ident,)).fetchone()
            match = False
            if row and row['source']==LIVE and inc['order_id'] is not None:
                doc = json.loads(row['raw_json'])
                match = any(isinstance(o,dict) and all((o.get('rq')==inc['rq'],o.get('oid')==inc['order_id'],o.get('acc')==inc['account_id'],o.get('mkt')==inc['market_id'])) for o in doc.get('d',[]))
            return {'action':'OWNER_APPROVAL_FOR_CANCEL' if match else 'REFRESH_LIVE_OPEN_ORDERS','permission':'OWNER_APPROVAL','reason':'only known open order with matching authenticated snapshot is reviewable','can_cancel':match}
        if inc['status'] in ('ORDER_FILLED_CONSEQUENCE_UNVERIFIED','FILL_CONFIRMED_POSITION_RECONCILIATION_NEEDED'):
            return {'action':'CONFIRM_FILLS_AND_POSITION','permission':'READ_ONLY','reason':'fill report does not prove final position','can_cancel':False}
        if inc['status'] in ('ORDER_CANCELED','ORDER_EXPIRED','EXCHANGE_REJECTED'):
            return {'action':'RECONCILE_HISTORY_AND_POSITION','permission':'READ_ONLY','reason':'order status alone does not prove account consequence','can_cancel':False}
        return {'action':'HOLD_AND_RECONCILE','permission':'READ_ONLY','reason':'unknown; do not create a new rq due to timeout','can_cancel':False}

    def request_cancel_review(self, ident, owner_note):
        if not isinstance(owner_note,str) or len(owner_note.strip())<8:
            raise ValueError('owner note must be at least 8 characters')
        if not self.plan(ident)['can_cancel']:
            raise ValueError('cannot request cancel without authenticated known-open matching snapshot')
        rid = str(uuid.uuid4())
        self.db.execute('INSERT INTO approvals(id,incident_id,action,owner_note,state,created_at) VALUES(?,?,?,?,?,?)',
                        (rid,ident,'CANCEL_EXISTING_ORDER',owner_note.strip()[:1000],'REVIEW_ONLY_NOT_EXECUTED',now()))
        self.log(ident,'OWNER_REVIEW_REQUESTED',MANUAL,{'approval_id':rid,'execution':'NOT_IMPLEMENTED'})
        return {'approval_id':rid,'state':'REVIEW_ONLY_NOT_EXECUTED','exchange_write':'NOT_IMPLEMENTED'}
