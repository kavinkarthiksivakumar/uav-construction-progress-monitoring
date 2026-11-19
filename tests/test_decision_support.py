"""
Final Year Project — UAV Construction Progress Assessment
Test Suite: Decision Support Layer — Health Score, XAI Query Engine,
Final Inspection Summary, Dataset Evaluation Store, and new API endpoints.

Run:  python -m pytest tests/test_decision_support.py -v
"""

import sys
import json
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION A — Health Score Unit Tests (pure functions)
# ═══════════════════════════════════════════════════════════════════════════════

from backend.modules.decision_support import (
    compute_health_score,
    answer_query,
    AVAILABLE_QUERIES,
    QUERY_LABELS,
    build_final_summary,
    load_change_detection_eval,
    load_detection_eval,
)
from backend.modules.decision_support.health_score import (
    classify_schedule_variance,
    HEALTH_CLASSIFICATIONS,
)


class TestScheduleVarianceClassification:
    def test_on_track(self):
        assert classify_schedule_variance(0.0)["band"] == "on_track"
        assert classify_schedule_variance(5.0)["band"] == "on_track"

    def test_minor_delay_risk(self):
        assert classify_schedule_variance(-1.0)["band"] == "minor_delay_risk"
        assert classify_schedule_variance(-10.0)["band"] == "minor_delay_risk"

    def test_moderate_delay(self):
        assert classify_schedule_variance(-10.1)["band"] == "moderate_delay"
        assert classify_schedule_variance(-20.0)["band"] == "moderate_delay"

    def test_high_delay_risk(self):
        assert classify_schedule_variance(-20.1)["band"] == "high_delay_risk"
        assert classify_schedule_variance(-45.0)["band"] == "high_delay_risk"

    def test_unknown_when_none(self):
        assert classify_schedule_variance(None)["band"] == "unknown"


class TestHealthScore:
    def _sched(self, expected=65.0, actual=48.0):
        return {"expected_progress": expected, "actual_progress": actual}

    def test_full_data_score_range(self):
        h = compute_health_score(
            {"module5_score": 48.0, "image_count": 12},
            self._sched(),
            {"avg_compliance": 80.0, "total_detections": 40, "image_count": 6,
             "aggregate_counts": {"NO-Hardhat": 4, "Person": 10}},
            {"image_count": 12, "avg_quality_score": 75},
        )
        assert h["score"] is not None
        assert 0 <= h["score"] <= 100
        assert h["classification"] in {c["label"] for c in HEALTH_CLASSIFICATIONS}
        # Behind schedule → variance recorded
        assert h["schedule_variance"] < 0
        assert "behind the planned timeline" in h["variance_interpretation"]

    def test_breakdown_sums_reflect_weights(self):
        h = compute_health_score(
            {"module5_score": 80.0}, self._sched(50.0, 80.0),
            {"avg_compliance": 100.0, "total_detections": 30, "image_count": 3,
             "aggregate_counts": {}},
            {"image_count": 10, "avg_quality_score": 90},
        )
        b = h["breakdown"]
        assert abs(b["progress"]["max"] - 35.0) < 0.01   # w_progress = 0.35
        assert abs(b["schedule"]["max"] - 25.0) < 0.01   # w_schedule = 0.25
        assert abs(b["safety"]["max"] - 20.0) < 0.01     # w_safety   = 0.20

    def test_healthy_project_classifies_high(self):
        h = compute_health_score(
            {"module5_score": 90.0}, self._sched(50.0, 90.0),
            {"avg_compliance": 95.0, "total_detections": 60, "image_count": 4,
             "aggregate_counts": {"Person": 15}},
            {"image_count": 12, "avg_quality_score": 90},
        )
        assert h["score"] >= 80
        assert h["classification"] == "HEALTHY"

    def test_no_data_is_not_assessable(self):
        h = compute_health_score({}, {}, {}, {})
        assert h["score"] is None
        assert h["classification"] == "NOT ASSESSABLE"

    def test_renormalisation_with_partial_data(self):
        h = compute_health_score(
            {"image_count": 5}, {}, {}, {"image_count": 5, "avg_quality_score": 80}
        )
        assert h["score"] is not None
        assert h["renormalised"] is True
        assert 0 <= h["score"] <= 100

    def test_custom_weights_respected(self):
        h = compute_health_score(
            {"module5_score": 50.0}, self._sched(50.0, 50.0),
            {"avg_compliance": 0.0, "total_detections": 1, "image_count": 2,
             "aggregate_counts": {}},
            {"image_count": 4, "avg_quality_score": 50},
            weights={"progress": 1.0, "schedule": 0.0, "safety": 0.0,
                     "confidence": 0.0, "activity": 0.0},
        )
        # Only progress counts → score equals progress value
        assert abs(h["score"] - 50.0) < 1.5


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION B — XAI Query Engine Unit Tests
# ═══════════════════════════════════════════════════════════════════════════════

_SCHED = {
    "expected_progress": 72.0,
    "actual_progress": 55.0,
    "progress_deviation": -17.0,
}
_BAND = {
    "band": "moderate_delay", "label": "MODERATE DELAY",
    "interpretation": "Physical construction progress is 17.0 percentage points behind.",
}
_CHG = [{
    "pair_id": "pair_001", "change_percent": 12.5, "num_regions": 14,
    "overlay_url": "/api/v1/module4/overlay/p/o.png",
    "mask_url": "/api/v1/module4/overlay/p/m.png",
}]
_DET = {
    "image_count": 5, "total_detections": 30, "avg_compliance": 70.0,
    "aggregate_counts": {"NO-Hardhat": 4, "NO-Safety Vest": 3, "Person": 12},
}


class TestXaiQueryEngine:
    def test_catalog_complete(self):
        expected = {"what_changed", "progress_status", "why_delayed",
                    "safety_concerns", "region_attention", "evidence", "limitations"}
        assert set(AVAILABLE_QUERIES) == expected
        assert set(QUERY_LABELS.keys()) == expected

    def test_unknown_query_returns_error_and_catalog(self):
        r = answer_query("bogus_query", {}, {}, {}, [], {})
        assert "error" in r
        assert r["available_queries"] == AVAILABLE_QUERIES

    def test_all_queries_have_uniform_structure(self):
        for q in AVAILABLE_QUERIES:
            r = answer_query(q, {}, _SCHED, _BAND, _CHG, _DET)
            for field in ("finding", "why", "confidence", "evidence",
                          "limitations", "recommendation"):
                assert field in r, f"query={q} missing field={field}"
            assert r["confidence"]["level"] in ("High", "Moderate", "Low")

    def test_what_changed_reports_change_evidence(self):
        r = answer_query("what_changed", {}, _SCHED, _BAND, _CHG, _DET)
        assert "pair" in r["finding"].lower()
        assert r["artifacts"] is not None and r["artifacts"]["overlays"]

    def test_why_delayed_explains_negative_variance(self):
        r = answer_query("why_delayed", {"module5_delay_days": 25}, _SCHED, _BAND, _CHG, _DET)
        assert "MODERATE DELAY" in r["finding"]
        assert "-17.0" in r["finding"]
        assert any("delay_days" in str(e) or "+" in str(e) for e in r["evidence"])

    def test_why_delayed_positive_variance_not_delayed(self):
        sched = {"expected_progress": 50.0, "actual_progress": 65.0, "progress_deviation": 15.0}
        band = {"band": "on_track", "label": "ON TRACK", "interpretation": "on/ahead"}
        r = answer_query("why_delayed", {}, sched, band, [], {})
        assert "not delayed" in r["finding"].lower()

    def test_safety_concerns_count_violations(self):
        r = answer_query("safety_concerns", {}, _SCHED, _BAND, [], _DET)
        assert "7 missing-PPE instance(s)" in r["finding"]
        assert "MODERATE RISK" in r["finding"]

    def test_no_data_queries_degrade_gracefully(self):
        for q in ("what_changed", "safety_concerns"):
            r = answer_query(q, {}, {}, {}, [], {})
            assert "No " in r["finding"] or "not available" in r["finding"].lower()
            assert r["recommendation"]  # still actionable guidance


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION C — Final Summary Generator Unit Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestFinalSummary:
    def _inputs(self):
        project = {
            "project_id": "p-test", "name": "Tower A", "location": "Chennai",
            "project_type": "commercial", "status": "active",
            "start_date": "2026-01-01", "approximate_end_date": "2026-12-31",
            "image_count": 25,
        }
        sched = {"expected_progress": 70.0, "actual_progress": 62.0,
                 "progress_deviation": -8.0}
        band = classify_schedule_variance(-8.0)
        chg = {"available": True, "pairs_analysed": 3, "avg_change_pct": 14.2,
               "total_regions": 42}
        det = {"avg_compliance": 85.0, "total_detections": 19, "image_count": 8,
               "aggregate_counts": {"NO-Hardhat": 4, "Person": 12, "machinery": 3}}
        health = compute_health_score(project, sched, det,
                                      {"image_count": 25, "avg_quality_score": 80})
        return project, sched, band, chg, det, health

    def test_summary_structure(self):
        project, sched, band, chg, det, health = self._inputs()
        s = build_final_summary(project, sched, band, chg, det, health)
        for key in ("title", "generated_at", "project", "images_analyzed", "progress",
                    "safety", "change_detection", "health_score", "key_findings",
                    "recommended_actions", "text_report", "data_integrity_note"):
            assert key in s

    def test_findings_traceable_to_evidence(self):
        project, sched, band, chg, det, health = self._inputs()
        s = build_final_summary(project, sched, band, chg, det, health)
        joined = "\n".join(s["key_findings"])
        assert "12 personnel" in joined           # from detection counts
        assert "14.2%" in joined                  # from change results
        assert "8.0 percentage points" in joined  # from schedule variance
        assert "PPE" in joined                    # violations

    def test_text_report_contains_core_numbers(self):
        project, sched, band, chg, det, health = self._inputs()
        s = build_final_summary(project, sched, band, chg, det, health)
        t = s["text_report"]
        assert "PROJECT INSPECTION SUMMARY" in t
        assert "62.0%" in t and "70.0%" in t
        assert "KEY FINDINGS" in t and "RECOMMENDED ACTIONS" in t

    def test_persist_to_disk(self, tmp_path):
        project, sched, band, chg, det, health = self._inputs()
        out = tmp_path / "summary.json"
        build_final_summary(project, sched, band, chg, det, health, output_path=out)
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["project"]["name"] == "Tower A"

    def test_empty_inputs_produce_safe_summary(self):
        s = build_final_summary({}, {}, {}, {}, {},
                                compute_health_score({}, {}, {}, {}))
        assert s["key_findings"]  # always at least the "no data" finding


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION D — Evaluation Store Tests (REAL saved evaluation files)
# ═══════════════════════════════════════════════════════════════════════════════

class TestEvaluationStore:
    def test_change_detection_eval_loads_real_results(self):
        ev = load_change_detection_eval()
        if not ev.get("available"):
            return  # file absent on this machine — skip gracefully
        assert "Classical" in ev["methodology_label"] or \
               "classical" in ev["methodology_label"].lower()
        ds = ev["datasets"]
        assert "levir_cd_plus" in ds and "sysu_cd" in ds
        # Values must match the actual saved evaluation report
        assert abs(ds["levir_cd_plus"]["iou"] - 0.0685) < 1e-6
        assert abs(ds["levir_cd_plus"]["f1_score"] - 0.1118) < 1e-6
        assert abs(ds["sysu_cd"]["iou"] - 0.1852) < 1e-6
        assert abs(ds["sysu_cd"]["f1_score"] - 0.2921) < 1e-6
        # Integrity disclosure present
        assert "NOT trained deep-learning" in ev["important_disclosure"]

    def test_detection_eval_loads_real_dataset_stats(self):
        de = load_detection_eval()
        if not de.get("available"):
            return
        assert de["totals"]["images"] > 0
        assert de["totals"]["annotations"] > 0
        assert len(de["classes"]) == 10
        # Must be labelled as dataset analysis, NOT model performance
        assert "ANNOTATION" in de["important_disclosure"].upper()
        assert "NOT" in de["important_disclosure"].upper()


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION E — API Endpoint Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════

import importlib
import os
import tempfile
import shutil


def make_test_app():
    tmpdir = tempfile.mkdtemp(prefix="uav_ds_test_")
    os.environ["TEST_TMPDIR"] = tmpdir
    sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
    import app as flask_app
    flask_app.app.config["TESTING"] = True
    flask_app.METADATA_DIR  = Path(tmpdir) / "metadata"
    flask_app.PROJECTS_FILE = Path(tmpdir) / "metadata" / "projects.json"
    flask_app.ACTIVITY_FILE = Path(tmpdir) / "metadata" / "activity.json"
    flask_app.METADATA_DIR.mkdir(parents=True, exist_ok=True)
    flask_app.PROCESSED_M7_DIR = Path(tmpdir) / "processed" / "module7_decision"
    flask_app.PROCESSED_M3_DIR = Path(tmpdir) / "processed" / "module3"
    flask_app.PROCESSED_M4_DIR = Path(tmpdir) / "processed" / "module4"
    flask_app.PROCESSED_M5_DIR = Path(tmpdir) / "processed" / "module5"
    flask_app.PROCESSED_M6_DIR = Path(tmpdir) / "processed" / "module6"
    return flask_app.app, tmpdir


import pytest


@pytest.fixture(scope="module")
def client():
    app, tmpdir = make_test_app()
    with app.test_client() as c:
        yield c
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture(scope="module")
def project_id(client):
    today = date.today()
    r = client.post("/api/v1/projects", json={
        "name": "Decision Support Test Site",
        "start_date": (today - timedelta(days=200)).isoformat(),
        "approximate_end_date": (today + timedelta(days=165)).isoformat(),
        "project_manager": "QA Bot",
        "project_type": "infrastructure",
    })
    assert r.status_code == 201
    return r.get_json()["data"]["project_id"]


class TestProjectPatchExtendedFields:
    def test_patch_end_date_and_manager(self, client, project_id):
        new_end = (date.today() + timedelta(days=300)).isoformat()
        r = client.patch(f"/api/v1/projects/{project_id}",
                         json={"approximate_end_date": new_end,
                               "project_manager": "New Manager"})
        assert r.status_code == 200
        d = r.get_json()["data"]
        assert d["project_manager"] == "New Manager"
        assert d["planned_duration_days"] is not None

    def test_patch_extended_statuses_accepted(self, client, project_id):
        for status in ("under_inspection", "at_risk", "on_track"):
            r = client.patch(f"/api/v1/projects/{project_id}", json={"status": status})
            assert r.status_code == 200
            assert r.get_json()["data"]["status"] == status

    def test_patch_invalid_status_rejected(self, client, project_id):
        r = client.patch(f"/api/v1/projects/{project_id}", json={"status": "banana"})
        assert r.status_code == 400


class TestHealthScoreEndpoint:
    def test_health_score_endpoint_structure(self, client, project_id):
        r = client.get(f"/api/v1/projects/{project_id}/health_score")
        assert r.status_code == 200
        data = r.get_json()["data"]
        assert "health" in data and "methodology" in data
        h = data["health"]
        for key in ("score", "classification", "breakdown", "components",
                    "weights_used", "interpretation"):
            assert key in h

    def test_health_score_404_unknown_project(self, client):
        r = client.get("/api/v1/projects/nope/health_score")
        assert r.status_code == 404

    def test_health_score_persists_to_project(self, client, project_id):
        client.get(f"/api/v1/projects/{project_id}/health_score")
        r = client.get(f"/api/v1/projects/{project_id}")
        proj = r.get_json()["data"]
        if proj.get("health_score") is not None:
            assert proj.get("health_status") is not None


class TestXaiQueryEndpoints:
    def test_query_catalog(self, client, project_id):
        r = client.get(f"/api/v1/projects/{project_id}/xai/queries")
        assert r.status_code == 200
        assert len(r.get_json()["data"]["available_queries"]) == 7

    def test_get_query(self, client, project_id):
        r = client.get(f"/api/v1/projects/{project_id}/xai/query?query=safety_concerns")
        assert r.status_code == 200
        d = r.get_json()["data"]
        assert "finding" in d and "recommendation" in d

    def test_post_query(self, client, project_id):
        r = client.post(f"/api/v1/projects/{project_id}/xai/query",
                        json={"query": "what_changed"})
        assert r.status_code == 200

    def test_invalid_query_400(self, client, project_id):
        r = client.get(f"/api/v1/projects/{project_id}/xai/query?query=nonsense")
        assert r.status_code == 400

    def test_query_logged_in_activity(self, client, project_id):
        client.get(f"/api/v1/projects/{project_id}/xai/query?query=evidence")
        r = client.get(f"/api/v1/activity?project_id={project_id}&limit=50")
        types = [e["event_type"] for e in r.get_json()["data"]["events"]]
        assert "xai_query_answered" in types


class TestFinalSummaryEndpoint:
    def test_generate_and_persist(self, client, project_id):
        r = client.post(f"/api/v1/projects/{project_id}/final_summary")
        assert r.status_code == 200
        d = r.get_json()["data"]
        assert d["title"] == "PROJECT INSPECTION SUMMARY"
        assert isinstance(d["key_findings"], list)
        assert isinstance(d["recommended_actions"], list)

    def test_saved_copy_retrievable(self, client, project_id):
        client.post(f"/api/v1/projects/{project_id}/final_summary")
        r = client.get(f"/api/v1/projects/{project_id}/final_summary")
        assert r.status_code == 200
        assert r.get_json()["data"].get("from_saved_file") is True

    def test_download_text(self, client, project_id):
        r = client.get(f"/api/v1/projects/{project_id}/final_summary/download")
        assert r.status_code == 200

    def test_download_json(self, client, project_id):
        r = client.get(f"/api/v1/projects/{project_id}/final_summary/download?format=json")
        assert r.status_code == 200


class TestEvaluationEndpoints:
    def test_change_detection_evaluation(self, client):
        r = client.get("/api/v1/evaluation/change_detection")
        if r.status_code == 404:
            pytest.skip("Evaluation report not generated on this machine")
        d = r.get_json()["data"]
        assert d["datasets"]["levir_cd_plus"]["iou"] == 0.0685
        assert "baseline" in d["category_title"].lower()

    def test_detection_evaluation(self, client):
        r = client.get("/api/v1/evaluation/detection")
        if r.status_code == 404:
            pytest.skip("Detection evaluation report not generated on this machine")
        d = r.get_json()["data"]
        assert d["dataset_name"] == "Roboflow Construction Site Safety"
        assert d["totals"]["images"] == 2799

    def test_per_pair_inclusion_flag(self, client):
        r = client.get("/api/v1/evaluation/change_detection?include_per_pair=true")
        if r.status_code == 404:
            pytest.skip("Evaluation report not generated on this machine")
        d = r.get_json()["data"]
        assert "per_pair_results" in d
        assert len(d["per_pair_results"]["levir_cd_plus"]) == 50


class TestActivityTrailIntegration:
    def test_full_assessment_logs_new_events(self, client, project_id):
        """Full assessment should emit decision-support activity events."""
        r = client.post(f"/api/v1/projects/{project_id}/full_assessment",
                        json={"limit": 2, "run_xai": False})
        assert r.status_code == 200
        events = client.get(f"/api/v1/activity?project_id={project_id}&limit=100") \
                       .get_json()["data"]["events"]
        types = {e["event_type"] for e in events}
        # Core pipeline + decision-support events must be present
        assert "assessment_completed" in types
        assert "quantitative_evaluation_completed" in types
        assert "qualitative_evaluation_completed" in types

    def test_assessment_includes_final_summary_section(self, client, project_id):
        r = client.post(f"/api/v1/projects/{project_id}/full_assessment",
                        json={"limit": 2, "run_xai": False})
        d = r.get_json()["data"]
        assert "final_summary" in d
        assert "workflow" in d
        assert d["workflow"].get("step16_health_score", {}).get("status") in (
            "completed", "insufficient_data", "error")

    def test_activity_entries_have_inspection_id_field(self, client, project_id):
        r = client.get(f"/api/v1/activity?project_id={project_id}&limit=5")
        events = r.get_json()["data"]["events"]
        assert len(events) > 0
        # inspection_id key exists (may be null) for traceability
        assert "inspection_id" in events[0]


class TestEvidenceReport:
    def test_build_evidence_report_structure(self):
        from backend.modules.decision_support.evidence_report import build_evidence_report
        proj = {
            "project_id": "test-pid-123",
            "name": "Metro Viaduct",
            "location": "Chennai",
            "status": "active",
            "images": [{"filename": "img1.png", "width": 1024, "height": 1024}]
        }
        rep = build_evidence_report(project=proj)
        assert rep["report_title"] == "CONSTRUCTION PROGRESS EVIDENCE REPORT"
        assert "sections" in rep
        sections = rep["sections"]
        for sec in ["A_project_information", "B_image_validation", "C_activity_detection",
                    "D_temporal_change", "E_progress_assessment", "F_delay_analysis",
                    "G_explainability", "H_system_confidence", "I_final_interpretation"]:
            assert sec in sections
        assert sections["A_project_information"]["project_id"] == "test-pid-123"

    def test_evidence_report_endpoint_200(self, client, project_id):
        r = client.get(f"/api/v1/projects/{project_id}/evidence_report")
        assert r.status_code == 200
        d = r.get_json()
        assert d["success"] is True
        data = d["data"]
        assert data["report_title"] == "CONSTRUCTION PROGRESS EVIDENCE REPORT"
        assert "sections" in data
        assert "A_project_information" in data["sections"]
        assert "I_final_interpretation" in data["sections"]

    def test_evidence_report_categories_taxonomy(self, client, project_id):
        """Must distinguish Category A, B, C, D, E."""
        r = client.get(f"/api/v1/projects/{project_id}/evidence_report")
        assert r.status_code == 200
        data = r.get_json()["data"]
        assert "categories_of_evidence" in data
        cats = data["categories_of_evidence"]
        expected_cats = [
            "category_A_verified_software_function",
            "category_B_verified_model_output",
            "category_C_dataset_benchmark_result",
            "category_D_qualitative_observation",
            "category_E_unavailable_not_yet_validated"
        ]
        for c in expected_cats:
            assert c in cats, f"Missing category {c}"
            assert "title" in cats[c]

    def test_evidence_chains_have_10_points(self, client, project_id):
        """Every analytical section must provide the 10-point evidence chain."""
        r = client.get(f"/api/v1/projects/{project_id}/evidence_report")
        assert r.status_code == 200
        sections = r.get_json()["data"]["sections"]
        chain_sections = ["B_image_validation", "C_activity_detection", "D_temporal_change", 
                          "E_progress_assessment", "F_delay_analysis", "G_explainability"]
        required_keys = [
            "1_input_file_or_inspection_id",
            "2_processing_module",
            "3_algorithm_or_model_executed",
            "4_output_artifact_generated",
            "5_numerical_result",
            "6_visual_evidence",
            "7_interpretation",
            "8_confidence_and_quality",
            "9_limitations",
            "10_timestamp_and_status"
        ]
        for s in chain_sections:
            assert "evidence_chain" in sections[s], f"Missing evidence_chain in {s}"
            chain = sections[s]["evidence_chain"]
            for k in required_keys:
                assert k in chain, f"Missing key {k} in {s} evidence_chain"

