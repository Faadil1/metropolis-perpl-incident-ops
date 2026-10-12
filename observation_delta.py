"""Compare two sanitized authenticated Perpl testnet observations.

Count changes are operational signals, not proof of order errors, fills, or
incident recovery. This code contains no exchange write path.
"""

def compare_live_observations(previous, current):
    if not isinstance(current,dict) or current.get('classification')!='AUTHENTICATED_PERPL_TESTNET_ACCOUNT_OVERVIEW':
        raise ValueError('comparison requires a validated live account observation')
    base={'classification':'BASELINE_ONLY','requires_investigation':False,
          'incident_detected':False,'exchange_writes_enabled':False,
          'signals':[]}
    if not isinstance(previous,dict) or previous.get('classification')!='AUTHENTICATED_PERPL_TESTNET_ACCOUNT_OVERVIEW':
        return base
    prev_ids={(r['instance_id'],r['account_id']) for r in previous.get('accounts',[])}
    current_ids={(r['instance_id'],r['account_id']) for r in current.get('accounts',[])}
    if prev_ids!=current_ids:
        return {**base,'classification':'ACCOUNT_SET_CHANGED_REBASE_REQUIRED',
                'requires_investigation':True,
                'signals':[{'type':'ACCOUNT_SET_CHANGED','interpretation':'UNKNOWN'}]}
    signals=[]
    for label in ('open_orders_count','open_positions_count'):
        old=previous.get(label); new=current.get(label)
        if type(old) is not int or type(new) is not int:
            raise ValueError('observation count malformed')
        if old!=new:
            signals.append({'type':'COUNT_CHANGED','resource':label,
                            'previous_count':old,'current_count':new,
                            'interpretation':'ACTIVITY_OBSERVED_OUTCOME_UNKNOWN'})
    for stream in ('wallet','orders','positions'):
        old=previous.get('snapshot_blocks',{}).get(stream)
        new=current.get('snapshot_blocks',{}).get(stream)
        if type(old) is int and type(new) is int and new<old:
            signals.append({'type':'SNAPSHOT_BLOCK_REGRESSION','stream':stream,
                            'previous_block':old,'current_block':new,
                            'interpretation':'STALE_OR_REORG_UNKNOWN'})
    a={r['account_id']:r for r in previous.get('accounts',[])}
    for r in current.get('accounts',[]):
        past=a.get(r['account_id'],{})
        for flag in ('frozen','order_forwarding_enabled'):
            if past.get(flag)!=r.get(flag):
                signals.append({'type':'ACCOUNT_FLAG_CHANGED','account_id':r['account_id'],
                                'field':flag,'previous_value':past.get(flag),
                                'current_value':r.get(flag),
                                'interpretation':'CHANGE_OBSERVED_CAUSE_UNKNOWN'})
    state='ACTIVITY_CHANGE_REVIEW_ONLY' if signals else 'NO_CHANGE_OBSERVED'
    return {**base,'classification':state,'requires_investigation':bool(signals),
            'signals':signals}
