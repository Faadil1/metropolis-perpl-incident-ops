"""Guard against evidence-first drift and false terminal-readiness promotion."""
from __future__ import annotations
import copy
import json
import runpy
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
module = runpy.run_path(str(ROOT / "scripts" / "check_product_depth.py"), run_name="test_validator_import")
audit = module["audit"]
source = json.loads((ROOT / "product" / "PRODUCT_DEPTH_ACCEPTANCE.json").read_text(encoding="utf-8"))
registry = (ROOT / "GATE_REGISTRY_PRELOCK.yaml").read_text(encoding="utf-8")

def change(**kwargs):
    result=copy.deepcopy(source)
    result.update(kwargs)
    return result

def test_current_product_must_honestly_remain_incomplete():
    assert audit(source,registry)==[]
    assert source["completion_claim"]=="NOT_COMPLETE"
    assert source["live_incident_core_loop"]=="BLOCKED"
    assert source["primary_workstream"]=="PRODUCT_EXPLOITATION"

def test_vertical_slice_cannot_become_definition_of_done():
    errors=audit(change(vertical_slice_rule="VERTICAL_SLICE_IS_DONE"),registry)
    assert any("vertical slice" in x for x in errors)

def test_evidence_packaging_cannot_displace_material_product_depth():
    errors=audit(change(primary_workstream="EVIDENCE_PACKAGING"),registry)
    assert any("WORKSTREAM_DRIFT" in x for x in errors)

def test_claiming_complete_from_green_ci_is_forbidden():
    errors=audit(change(completion_claim="PRODUCT_COMPLETE",build_candidate_ready=True),registry)
    assert any("cannot claim PRODUCT_COMPLETE" in x for x in errors)

def test_stop_for_enough_proofs_is_not_a_valid_stop_condition():
    errors=audit(change(valid_stop_condition="enough_proof_already_exists"),registry)
    assert any("invalid stop" in x for x in errors)

def test_legitimate_deadline_stop_keeps_product_incomplete():
    allowed=change(valid_stop_condition="deadline_or_official_rule_boundary",
        primary_workstream="STOPPED_BY_VALID_CONDITION")
    assert audit(allowed,registry)==[]
    invalid=change(valid_stop_condition="deadline_or_official_rule_boundary",
        primary_workstream="STOPPED_BY_VALID_CONDITION",completion_claim="PRODUCT_COMPLETE")
    assert any("cannot claim PRODUCT_COMPLETE" in e for e in audit(invalid,registry))

def test_missing_material_depth_dimension_blocks_validation():
    altered=copy.deepcopy(source)
    altered["dimensions"].pop("integrated_live_incident_core_loop")
    assert any("dimension is missing" in e for e in audit(altered,registry))

def test_proven_claim_requires_evidence_reference():
    altered=copy.deepcopy(source)
    altered["dimensions"]["genuine_negative_event_or_uncertain_outcome"]["status"]="PROVEN"
    assert any("PROVEN requires" in e for e in audit(altered,registry))

def test_live_incident_claim_blocked_by_registry():
    errors=audit(change(live_incident_core_loop="PROVEN"),registry)
    assert any("LIVE_DEPTH" in e for e in errors)

def test_cannot_silently_remove_post_slice_exploitation():
    altered=registry.replace("PRODUCT_EXPLOITATION_LOOP: {status: ACTIVE}",
                             "PRODUCT_EXPLOITATION_LOOP: {status: N/A}")
    assert any("product exploitation" in e for e in audit(source,altered))

def test_cannot_auto_enable_exchange_write_on_proof_claim():
    altered=copy.deepcopy(source)
    altered["safe_action_depth"]["exchange_write_currently_enabled"]=True
    assert any("may not be enabled" in e for e in audit(altered,registry))
