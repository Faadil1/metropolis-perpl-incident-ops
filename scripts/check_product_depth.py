"""Fail-closed Product Reality completeness contract for this local research build.

Existing canonical Product Reality / Product Exploitation policy is the owner.
This validator neither invents a new gate nor turns CI-green into product proof.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "product" / "PRODUCT_DEPTH_ACCEPTANCE.json"
GATES = ROOT / "GATE_REGISTRY_PRELOCK.yaml"

REQUIRED = {
    "real_authenticated_account_read",
    "real_normal_order_lifecycle_read",
    "genuine_negative_event_or_uncertain_outcome",
    "independent_operator_problem_and_demand",
    "differentiation_against_native_and_existing_clients",
    "integrated_live_incident_core_loop",
    "safe_authorized_corrective_action",
    "verified_business_consequence_after_action",
    "success_negative_boundary_recovery_paths",
    "persistent_identity_state_permissions",
    "websocket_gap_recovery_and_full_history_pagination",
    "live_dependency_failure_and_refusal",
    "real_operator_surface",
    "external_operator_trial",
    "operator_judge_self_serve_on_real_shared_core",
    "repeatable_setup_cleanroom_and_security",
    "observable_causal_receipts_and_reality_ledger",
    "time_to_first_product_value",
    "operational_economics_when_material",
    "post_vertical_slice_depth_gap_review",
    "post_vertical_slice_product_exploitation",
}
ALLOWED = {"ACTIVE", "BLOCKED", "PROVEN", "N/A"}
VALID_STOPS = {
    "deadline_or_official_rule_boundary",
    "safety_security_privacy_or_protected_authority_boundary",
    "marginal_user_value_or_competitive_differentiation_no_longer_justifies_cost_or_risk",
    "additional_scope_breaks_product_coherence_or_reliability",
    "required_external_access_is_unavailable_and_no_truthful_safe_path_exists",
}

def parse_registered_gate_statuses(text: str) -> dict[str, str]:
    if "gateways:\n" not in text:
        raise ValueError("missing canonical project gateway registry")
    matches = re.findall(r"^  ([A-Z0-9_]+): \{status: (ACTIVE|BLOCKED|PROVEN|N/A)\}", text.split("gateways:\n", 1)[1], re.M)
    if not matches or len(matches) != len(dict(matches)):
        raise ValueError("missing or duplicate registered gates")
    return dict(matches)

def audit(contract: dict, registry_text: str) -> list[str]:
    errors = []
    def fail_if(condition: bool, message: str) -> None:
        if condition:
            errors.append(message)
    if not isinstance(contract, dict):
        return ["completion contract must be an object"]
    try:
        gates = parse_registered_gate_statuses(registry_text)
    except ValueError as exc:
        return [str(exc)]
    dimensions = contract.get("dimensions")
    if not isinstance(dimensions, dict):
        return ["dimensions must be a keyed mapping"]
    fail_if(not REQUIRED.issubset(dimensions), "a canonical applicable depth dimension is missing")
    fail_if(len(gates) < 65, "registered canonical gates were silently dropped")
    fail_if(contract.get("vertical_slice_rule") != "ENTRY_POINT_NOT_DEFINITION_OF_DONE",
            "vertical slice incorrectly treated as the Definition of Done")
    fail_if(contract.get("evidence_rule") != "OUTPUT_OF_REAL_PRODUCT_BEHAVIOR_NOT_PRIMARY_ENGINE",
            "evidence cannot become the primary product")
    fail_if(contract.get("authority") != "PROJECT_LOCAL_PROJECTION_OF_ALREADY_PROMOTED_CANON__NO_NEW_GLOBAL_GATE",
            "the local checklist cannot replace or elevate global canon")
    valid_st = contract.get("valid_stop_condition")
    fail_if(valid_st is not None and valid_st not in VALID_STOPS,
            "invalid stop condition; having enough proofs is not a stop condition")
    material_gaps = []
    for name, item in dimensions.items():
        if not isinstance(item, dict) or item.get("status") not in ALLOWED:
            errors.append(f"{name}: invalid depth status")
            continue
        if item.get("material") not in (True, False):
            errors.append(f"{name}: material must be explicit")
        if item["status"] == "N/A" and not item.get("not_applicable_reason"):
            errors.append(f"{name}: N/A needs a real reason")
        if item["status"] == "PROVEN" and not (
            isinstance(item.get("evidence"), list) and item["evidence"]
        ):
            errors.append(f"{name}: PROVEN requires a concrete evidence reference")
        if item.get("material") is True and item["status"] not in ("PROVEN", "N/A"):
            material_gaps.append(name)
    if material_gaps:
        fail_if(contract.get("completion_claim") != "NOT_COMPLETE",
                "MATERIAL DEPTH BLOCKER: cannot claim PRODUCT_COMPLETE")
        fail_if(contract.get("build_candidate_ready") is not False,
                "MATERIAL DEPTH BLOCKER: cannot promote BUILD_CANDIDATE_READY")
        fail_if(
            contract.get("primary_workstream") != "PRODUCT_EXPLOITATION" and valid_st is None,
            "WORKSTREAM_DRIFT: material product gaps cannot be displaced by evidence/demo/packaging",
        )
        fail_if(
            contract.get("valid_stop_condition") is not None and contract.get("completion_claim") != "NOT_COMPLETE",
            "valid stop condition does not magically complete an incomplete product",
        )
    fail_if(not contract.get("next_highest_value_depth_delta") and bool(material_gaps),
            "unfinished product requires a concrete next material user-value delta")
    fail_if("CORE_USER_VALUE" not in str(contract.get("next_depth_delta_priority_basis", "")),
            "product capability must outrank proof quantity as prioritization driver")
    fail_if(contract.get("first_incident_recovery_slice") == "PROVEN" and
            dimensions.get("integrated_live_incident_core_loop", {}).get("status") != "PROVEN",
            "cannot claim first live incident slice without live core loop")
    fail_if(contract.get("completion_claim") == "PRODUCT_COMPLETE" and
            (any(x in ("ACTIVE", "BLOCKED") for x in gates.values()) or material_gaps),
            "the gateway registry has not been terminally reconciled for full-product claim")
    for label, field in (("concept_lock", "concept_lock"), ("live_incident_core_loop", "live_core_loop")):
        match = re.search(rf"^{field}: (ACTIVE|BLOCKED|PROVEN|N/A)$", registry_text, re.M)
        if label == "concept_lock" and match and contract.get(label) != match.group(1):
            errors.append("concept_lock differs from canonical project registry")
    if gates.get("LIVE_DEPTH") == "BLOCKED":
        fail_if(contract.get("live_incident_core_loop") == "PROVEN",
                "live incident product cannot be claimed while LIVE_DEPTH is BLOCKED")
    if gates.get("DIFFERENTIATOR") == "BLOCKED":
        fail_if(contract.get("completion_claim") == "PRODUCT_COMPLETE",
                "competitive differentiator remains BLOCKED")
    if gates.get("POST_VERTICAL_SLICE_DEPTH_GAP_REVIEW") not in ("ACTIVE", "PROVEN"):
        errors.append("post-vertical-slice depth gap review must be activated for proven bounded live slice")
    if gates.get("PRODUCT_EXPLOITATION_LOOP") not in ("ACTIVE", "PROVEN"):
        errors.append("product exploitation must remain active, not silently N/A")
    if contract.get("safe_action_depth", {}).get("exchange_write_currently_enabled") is not False:
        errors.append("testnet exchange writes may not be enabled by evidence policy")
    fail_if(contract.get("workstream_drift_status") == "WORKSTREAM_DRIFT",
            "unresolved WORKSTREAM_DRIFT blocks readiness")
    return errors

def main() -> int:
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    registry_text=GATES.read_text(encoding="utf-8")
    failures=audit(contract,registry_text)
    if failures:
        for x in failures:
            print("PRODUCT DEPTH CONTRACT FAILED:", x)
        return 1
    outstanding=sum(
        item["material"] and item["status"] not in ("PROVEN","N/A")
        for item in contract["dimensions"].values()
    )
    print("Depth contract coherent: NOT COMPLETE; material gaps=",outstanding,
          "; primary workstream=",contract["primary_workstream"],
          "; proof is an output of product operation, not the product.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
