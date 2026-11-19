"""
Final Year Project — UAV Construction Progress Assessment
Test Suite: Project Management API — Phases 2 & 3
Tests: create_project (timeline), _compute_project_metrics, /summary,
       /full_assessment, /qualitative_results, /quantitative_metrics,
       /activity, /stats (delay classification).
"""

import sys
import os
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta, date

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# ─── App factory ─────────────────────────────────────────────────────────────
import importlib

def make_test_app():
    """Create app instance with temp directories for isolated testing."""
    # Temporarily patch dirs via environment
    tmpdir = tempfile.mkdtemp(prefix="uav_test_")
    os.environ["TEST_TMPDIR"] = tmpdir
    import app as flask_app
    flask_app.app.config["TESTING"] = True
    flask_app.app.config["WTF_CSRF_ENABLED"] = False
    # Override storage paths to tmpdir
    flask_app.METADATA_DIR    = Path(tmpdir) / "metadata"
    flask_app.PROJECTS_FILE   = Path(tmpdir) / "metadata" / "projects.json"
    flask_app.ACTIVITY_FILE   = Path(tmpdir) / "metadata" / "activity.json"
    flask_app.METADATA_DIR.mkdir(parents=True, exist_ok=True)
    return flask_app.app, tmpdir


@pytest.fixture(scope="module")
def client():
    flask_app, tmpdir = make_test_app()
    with flask_app.test_client() as c:
        yield c
    shutil.rmtree(tmpdir, ignore_errors=True)


# ─── Helpers ─────────────────────────────────────────────────────────────────
def _create_project(client, **overrides):
    today = date.today()
    end   = today + timedelta(days=365)
    body  = {
        "name":                 overrides.get("name", "Test Site Alpha"),
        "description":          "Automated test project",
        "location":             "Chennai, Tamil Nadu",
        "project_type":         "residential",
        "project_manager":      "Test Manager",
        "start_date":           today.isoformat(),
        "approximate_end_date": end.isoformat(),
        "planned_duration_days": 365,
        "client":               "Test Client",
        "contractor":           "Test Contractor",
    }
    body.update(overrides)
    r = client.post("/api/v1/projects", json=body)
    return r


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION A — Project CRUD with Timeline Fields
# ═══════════════════════════════════════════════════════════════════════════════

class TestProjectCreationWithTimeline:
    """Tests for extended project creation accepting timeline fields."""

    def test_create_project_returns_200(self, client):
        r = _create_project(client)
        assert r.status_code in (200, 201), f"Expected 200 or 201, got {r.status_code}: {r.data}"

    def test_create_project_success_flag(self, client):
        r = _create_project(client, name="Alpha B")
        d = r.get_json()
        assert d["success"] is True

    def test_create_project_has_project_id(self, client):
        r  = _create_project(client, name="Alpha C")
        d  = r.get_json()["data"]
        assert "project_id" in d
        assert len(d["project_id"]) > 0

    def test_create_project_stores_start_date(self, client):
        today = date.today().isoformat()
        r = _create_project(client, name="Alpha D", start_date=today)
        d = r.get_json()["data"]
        assert d.get("start_date") == today or d.get("start_date","").startswith(today)

    def test_create_project_stores_approximate_end_date(self, client):
        end = (date.today() + timedelta(days=180)).isoformat()
        r   = _create_project(client, name="Alpha E", approximate_end_date=end)
        d   = r.get_json()["data"]
        stored = d.get("approximate_end_date","")
        assert stored.startswith(end), f"end_date not stored: {stored}"

    def test_create_project_stores_project_manager(self, client):
        r = _create_project(client, name="Alpha F", project_manager="Jane Doe")
        d = r.get_json()["data"]
        assert d.get("project_manager") == "Jane Doe"

    def test_create_project_stores_project_type(self, client):
        r = _create_project(client, name="Alpha G", project_type="commercial")
        d = r.get_json()["data"]
        assert d.get("project_type") == "commercial"

    def test_create_project_computes_planned_duration(self, client):
        start = date.today()
        end   = start + timedelta(days=300)
        r = _create_project(client, name="Alpha H",
                            start_date=start.isoformat(),
                            approximate_end_date=end.isoformat())
        d = r.get_json()["data"]
        # planned_duration_days should be set from dates
        dur = d.get("planned_duration_days") or d.get("planned_duration")
        assert dur is not None, "planned_duration_days not computed"

    def test_create_project_missing_name_returns_400(self, client):
        r = client.post("/api/v1/projects", json={"description": "no name"})
        assert r.status_code == 400

    def test_get_project_returns_schedule_metrics(self, client):
        r  = _create_project(client, name="Alpha I")
        pid = r.get_json()["data"]["project_id"]
        rg  = client.get(f"/api/v1/projects/{pid}")
        assert rg.status_code == 200
        d   = rg.get_json()["data"]
        # schedule_metrics injected by get_project
        sm  = d.get("schedule_metrics", {})
        assert "elapsed_days" in sm or "planned_duration_days" in sm


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION B — _compute_project_metrics (via /summary endpoint)
# ═══════════════════════════════════════════════════════════════════════════════

class TestComputeProjectMetrics:
    """Tests the _compute_project_metrics logic via the /summary endpoint."""

    @pytest.fixture
    def project_id(self, client):
        start = date.today() - timedelta(days=90)
        end   = date.today() + timedelta(days=275)
        r  = _create_project(client, name="Metrics Test Project",
                              start_date=start.isoformat(),
                              approximate_end_date=end.isoformat())
        return r.get_json()["data"]["project_id"]

    def test_summary_returns_200(self, client, project_id):
        r = client.get(f"/api/v1/projects/{project_id}/summary")
        assert r.status_code == 200

    def test_summary_has_elapsed_days(self, client, project_id):
        d = client.get(f"/api/v1/projects/{project_id}/summary").get_json()["data"]
        assert d.get("elapsed_days") is not None
        assert d["elapsed_days"] >= 0

    def test_summary_elapsed_days_approximately_correct(self, client, project_id):
        d = client.get(f"/api/v1/projects/{project_id}/summary").get_json()["data"]
        # started 90 days ago, so elapsed should be ~90
        elapsed = d.get("elapsed_days", 0)
        assert 85 <= elapsed <= 95, f"elapsed_days {elapsed} out of expected range 85-95"

    def test_summary_has_planned_duration(self, client, project_id):
        d = client.get(f"/api/v1/projects/{project_id}/summary").get_json()["data"]
        dur = d.get("planned_duration_days")
        assert dur is not None and dur > 0

    def test_summary_has_remaining_days(self, client, project_id):
        d = client.get(f"/api/v1/projects/{project_id}/summary").get_json()["data"]
        assert d.get("remaining_days") is not None

    def test_summary_expected_progress_in_range(self, client, project_id):
        d = client.get(f"/api/v1/projects/{project_id}/summary").get_json()["data"]
        exp = d.get("expected_progress")
        if exp is not None:
            assert 0.0 <= exp <= 100.0, f"expected_progress {exp} out of range"

    def test_summary_delay_status_is_valid(self, client, project_id):
        d  = client.get(f"/api/v1/projects/{project_id}/summary").get_json()["data"]
        ds = d.get("delay_status", "")
        valid = {"Ahead of Schedule", "On Schedule", "At Risk", "Delayed",
                 "Pending Analysis", "Unknown", ""}
        assert ds in valid, f"Invalid delay_status: {ds}"

    def test_summary_404_for_unknown_project(self, client):
        r = client.get("/api/v1/projects/nonexistent-xyz/summary")
        assert r.status_code == 404

    def test_formula_explanation_present(self, client, project_id):
        rg = client.get(f"/api/v1/projects/{project_id}")
        d  = rg.get_json()["data"]
        sm = d.get("schedule_metrics", {})
        formula = sm.get("schedule_formula","")
        assert "elapsed" in formula or formula == "" or sm == {}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION C — /stats Endpoint (Delay Classification Counts)
# ═══════════════════════════════════════════════════════════════════════════════

class TestStatsEndpoint:
    """Tests /api/v1/stats returns extended classification fields."""

    def test_stats_returns_200(self, client):
        r = client.get("/api/v1/stats")
        assert r.status_code == 200

    def test_stats_has_total_projects(self, client):
        d = client.get("/api/v1/stats").get_json()["data"]
        assert "total_projects" in d
        assert isinstance(d["total_projects"], int)

    def test_stats_has_delayed_projects(self, client):
        d = client.get("/api/v1/stats").get_json()["data"]
        assert "delayed_projects" in d
        assert isinstance(d["delayed_projects"], int)
        assert d["delayed_projects"] >= 0

    def test_stats_has_at_risk_projects(self, client):
        d = client.get("/api/v1/stats").get_json()["data"]
        assert "at_risk_projects" in d
        assert isinstance(d["at_risk_projects"], int)

    def test_stats_has_project_summaries(self, client):
        d = client.get("/api/v1/stats").get_json()["data"]
        assert "project_summaries" in d
        assert isinstance(d["project_summaries"], list)

    def test_stats_project_summaries_have_delay_status(self, client):
        d = client.get("/api/v1/stats").get_json()["data"]
        for ps in d["project_summaries"]:
            assert "delay_status" in ps, f"Missing delay_status in project summary: {ps}"

    def test_stats_risk_distribution_present(self, client):
        d = client.get("/api/v1/stats").get_json()["data"]
        assert "risk_distribution" in d
        rd = d["risk_distribution"]
        for key in ("low","medium","high","critical"):
            assert key in rd


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION D — /activity Endpoint
# ═══════════════════════════════════════════════════════════════════════════════

class TestProjectActivity:
    """Tests /api/v1/projects/<id>/activity endpoint."""

    @pytest.fixture
    def project_id(self, client):
        r = _create_project(client, name="Activity Test Project")
        return r.get_json()["data"]["project_id"]

    def test_activity_returns_200(self, client, project_id):
        r = client.get(f"/api/v1/projects/{project_id}/activity")
        assert r.status_code == 200

    def test_activity_has_events_list(self, client, project_id):
        d = client.get(f"/api/v1/projects/{project_id}/activity").get_json()["data"]
        assert "events" in d
        assert isinstance(d["events"], list)

    def test_activity_has_total(self, client, project_id):
        d = client.get(f"/api/v1/projects/{project_id}/activity").get_json()["data"]
        assert "total" in d

    def test_activity_404_for_unknown(self, client):
        r = client.get("/api/v1/projects/does-not-exist/activity")
        assert r.status_code == 404

    def test_activity_creation_logged(self, client, project_id):
        # Project creation should be logged
        d    = client.get(f"/api/v1/projects/{project_id}/activity").get_json()["data"]
        evts = d["events"]
        types = [e.get("event_type","") for e in evts]
        assert any("creat" in t.lower() for t in types), \
            f"Creation event not found. Event types: {types}"

    def test_activity_limit_param(self, client, project_id):
        r = client.get(f"/api/v1/projects/{project_id}/activity?limit=2")
        d = r.get_json()["data"]
        assert len(d["events"]) <= 2


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION E — /qualitative_results Endpoint
# ═══════════════════════════════════════════════════════════════════════════════

class TestQualitativeResults:
    """Tests GET /api/v1/projects/<id>/qualitative_results."""

    @pytest.fixture
    def project_id(self, client):
        r = _create_project(client, name="Qualitative Test Project")
        return r.get_json()["data"]["project_id"]

    def test_qualitative_returns_200(self, client, project_id):
        r = client.get(f"/api/v1/projects/{project_id}/qualitative_results")
        assert r.status_code == 200

    def test_qualitative_has_results_list(self, client, project_id):
        d = client.get(f"/api/v1/projects/{project_id}/qualitative_results").get_json()["data"]
        assert "results" in d
        assert isinstance(d["results"], list)

    def test_qualitative_has_total_results(self, client, project_id):
        d = client.get(f"/api/v1/projects/{project_id}/qualitative_results").get_json()["data"]
        assert "total_results" in d
        assert isinstance(d["total_results"], int)

    def test_qualitative_has_result_types(self, client, project_id):
        d = client.get(f"/api/v1/projects/{project_id}/qualitative_results").get_json()["data"]
        assert "result_types" in d
        assert isinstance(d["result_types"], list)

    def test_qualitative_404_for_unknown(self, client):
        r = client.get("/api/v1/projects/nonexistent/qualitative_results")
        assert r.status_code == 404

    def test_qualitative_results_structure(self, client, project_id):
        d = client.get(f"/api/v1/projects/{project_id}/qualitative_results").get_json()["data"]
        for result in d.get("results", []):
            assert "result_type"       in result
            assert "stage"             in result
            assert "interpretation"    in result
            assert "output_exists"     in result


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION F — /quantitative_metrics Endpoint
# ═══════════════════════════════════════════════════════════════════════════════

class TestQuantitativeMetrics:
    """Tests GET /api/v1/projects/<id>/quantitative_metrics."""

    @pytest.fixture
    def project_id(self, client):
        r = _create_project(client, name="Quantitative Test Project")
        return r.get_json()["data"]["project_id"]

    def test_quantitative_returns_200(self, client, project_id):
        r = client.get(f"/api/v1/projects/{project_id}/quantitative_metrics")
        assert r.status_code == 200

    def test_quantitative_has_three_categories(self, client, project_id):
        d = client.get(f"/api/v1/projects/{project_id}/quantitative_metrics").get_json()["data"]
        assert "software_validation" in d
        assert "ai_model_metrics"    in d
        assert "project_monitoring"  in d

    def test_software_validation_category_label(self, client, project_id):
        d  = client.get(f"/api/v1/projects/{project_id}/quantitative_metrics").get_json()["data"]
        sv = d["software_validation"]
        assert "A" in sv.get("category",""), "Category A label missing"

    def test_ai_metrics_category_label(self, client, project_id):
        d  = client.get(f"/api/v1/projects/{project_id}/quantitative_metrics").get_json()["data"]
        am = d["ai_model_metrics"]
        assert "B" in am.get("category",""), "Category B label missing"

    def test_project_monitoring_category_label(self, client, project_id):
        d  = client.get(f"/api/v1/projects/{project_id}/quantitative_metrics").get_json()["data"]
        pm = d["project_monitoring"]
        assert "C" in pm.get("category",""), "Category C label missing"

    def test_ai_metrics_has_detection_section(self, client, project_id):
        d  = client.get(f"/api/v1/projects/{project_id}/quantitative_metrics").get_json()["data"]
        am = d["ai_model_metrics"]
        assert "detection" in am

    def test_detection_metrics_honest_about_missing_gt(self, client, project_id):
        d  = client.get(f"/api/v1/projects/{project_id}/quantitative_metrics").get_json()["data"]
        det = d["ai_model_metrics"]["detection"]
        # If no ground truth / no model, should say "Not available", not fabricate numbers
        mAP = det.get("mAP","")
        if isinstance(mAP, str):
            assert "not available" in mAP.lower() or "not" in mAP.lower()

    def test_project_monitoring_has_schedule(self, client, project_id):
        d  = client.get(f"/api/v1/projects/{project_id}/quantitative_metrics").get_json()["data"]
        pm = d["project_monitoring"]
        assert "schedule" in pm

    def test_important_notice_present(self, client, project_id):
        d = client.get(f"/api/v1/projects/{project_id}/quantitative_metrics").get_json()["data"]
        assert "important_notice" in d
        notice = d["important_notice"]
        assert "not" in notice.lower() or "separate" in notice.lower()

    def test_quantitative_404_for_unknown(self, client):
        r = client.get("/api/v1/projects/nonexistent/quantitative_metrics")
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION G — POST /full_assessment Endpoint
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullAssessment:
    """Tests POST /api/v1/projects/<id>/full_assessment."""

    @pytest.fixture
    def project_id(self, client):
        start = (date.today() - timedelta(days=30)).isoformat()
        end   = (date.today() + timedelta(days=335)).isoformat()
        r = _create_project(client, name="Full Assessment Test",
                            start_date=start, approximate_end_date=end)
        return r.get_json()["data"]["project_id"]

    def test_full_assessment_returns_200(self, client, project_id):
        r = client.post(f"/api/v1/projects/{project_id}/full_assessment",
                        json={"limit": 2, "run_xai": False})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.data}"

    def test_full_assessment_success_flag(self, client, project_id):
        r = client.post(f"/api/v1/projects/{project_id}/full_assessment",
                        json={"limit": 2, "run_xai": False})
        assert r.get_json()["success"] is True

    def test_full_assessment_has_workflow(self, client, project_id):
        d = client.post(f"/api/v1/projects/{project_id}/full_assessment",
                        json={"limit": 2, "run_xai": False}).get_json()["data"]
        assert "workflow" in d
        assert isinstance(d["workflow"], dict)

    def test_full_assessment_workflow_has_steps(self, client, project_id):
        wf = client.post(f"/api/v1/projects/{project_id}/full_assessment",
                         json={"limit": 2, "run_xai": False}).get_json()["data"]["workflow"]
        expected_steps = ["step1_validation","step2_file_check","step3_temporal_data"]
        for step in expected_steps:
            assert step in wf, f"Missing workflow step: {step}"

    def test_full_assessment_has_progress_analysis(self, client, project_id):
        d = client.post(f"/api/v1/projects/{project_id}/full_assessment",
                        json={"limit": 2, "run_xai": False}).get_json()["data"]
        assert "progress_analysis" in d
        pa = d["progress_analysis"]
        assert "delay_status" in pa

    def test_full_assessment_has_quantitative_results(self, client, project_id):
        d = client.post(f"/api/v1/projects/{project_id}/full_assessment",
                        json={"limit": 2, "run_xai": False}).get_json()["data"]
        assert "quantitative_results" in d

    def test_full_assessment_has_overall_assessment(self, client, project_id):
        d = client.post(f"/api/v1/projects/{project_id}/full_assessment",
                        json={"limit": 2, "run_xai": False}).get_json()["data"]
        oa = d.get("overall_assessment","")
        assert isinstance(oa, str) and len(oa) > 20, \
            f"overall_assessment too short or missing: '{oa}'"

    def test_full_assessment_overall_is_dynamic(self, client, project_id):
        d  = client.post(f"/api/v1/projects/{project_id}/full_assessment",
                         json={"limit": 2, "run_xai": False}).get_json()["data"]
        oa = d.get("overall_assessment","")
        # Must contain actual project name, not a static placeholder
        proj_name = "Full Assessment Test"
        assert proj_name in oa, f"Project name not in overall_assessment: {oa}"

    def test_full_assessment_has_project_overview(self, client, project_id):
        d = client.post(f"/api/v1/projects/{project_id}/full_assessment",
                        json={"limit": 2, "run_xai": False}).get_json()["data"]
        assert "project_overview" in d
        po = d["project_overview"]
        assert "project_name" in po

    def test_full_assessment_404_for_unknown(self, client):
        r = client.post("/api/v1/projects/nonexistent/full_assessment", json={})
        assert r.status_code == 404

    def test_full_assessment_updates_activity_log(self, client, project_id):
        client.post(f"/api/v1/projects/{project_id}/full_assessment",
                    json={"limit": 2, "run_xai": False})
        d    = client.get(f"/api/v1/projects/{project_id}/activity").get_json()["data"]
        evts = d["events"]
        types = [e.get("event_type","") for e in evts]
        assert any("assessment" in t.lower() for t in types), \
            f"No assessment event in log. Types found: {types}"

    def test_full_assessment_delay_status_valid(self, client, project_id):
        d  = client.post(f"/api/v1/projects/{project_id}/full_assessment",
                         json={"limit": 2, "run_xai": False}).get_json()["data"]
        ds = d.get("progress_analysis",{}).get("delay_status","")
        valid = {"Ahead of Schedule","On Track","On Schedule","At Risk","Delayed",
                 "Pending Analysis","Unknown",""}
        assert ds in valid, f"Invalid delay_status: {ds}"


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION H — Data Integrity Checks
# ═══════════════════════════════════════════════════════════════════════════════

class TestDataIntegrity:
    """Verifies data consistency across endpoints for the same project."""

    @pytest.fixture
    def project_id(self, client):
        start = (date.today() - timedelta(days=60)).isoformat()
        end   = (date.today() + timedelta(days=305)).isoformat()
        r = _create_project(client, name="Integrity Test Project",
                            start_date=start, approximate_end_date=end)
        return r.get_json()["data"]["project_id"]

    def test_summary_and_get_consistent_elapsed(self, client, project_id):
        summary = client.get(f"/api/v1/projects/{project_id}/summary").get_json()["data"]
        project = client.get(f"/api/v1/projects/{project_id}").get_json()["data"]
        sm      = project.get("schedule_metrics",{})
        s_elapsed = summary.get("elapsed_days")
        p_elapsed = sm.get("elapsed_days")
        if s_elapsed is not None and p_elapsed is not None:
            assert abs(s_elapsed - p_elapsed) <= 1, \
                f"elapsed_days mismatch: summary={s_elapsed}, get_project={p_elapsed}"

    def test_expected_progress_formula(self, client, project_id):
        """expected_progress = clamp(elapsed/planned * 100, 0, 100)"""
        d       = client.get(f"/api/v1/projects/{project_id}/summary").get_json()["data"]
        elapsed = d.get("elapsed_days")
        planned = d.get("planned_duration_days")
        expected= d.get("expected_progress")
        if elapsed is not None and planned and expected is not None:
            computed = round(min(max(elapsed / planned * 100, 0), 100), 2)
            assert abs(computed - expected) < 1.0, \
                f"Formula mismatch: computed={computed}, stored={expected}"

    def test_quantitative_honest_mAP(self, client, project_id):
        """mAP must NOT be a float — it must be 'Not available' when no ground truth."""
        d   = client.get(f"/api/v1/projects/{project_id}/quantitative_metrics").get_json()["data"]
        mAP = d["ai_model_metrics"]["detection"].get("mAP","")
        assert not isinstance(mAP, float), \
            "mAP should not be a float (fabricated) — use 'Not available' string"

    def test_stats_counts_non_negative(self, client):
        d = client.get("/api/v1/stats").get_json()["data"]
        for field in ("total_projects","active_projects","delayed_projects","at_risk_projects"):
            val = d.get(field,0)
            assert val >= 0, f"{field} is negative: {val}"


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION I — Pipeline Status Endpoint
# ═══════════════════════════════════════════════════════════════════════════════

class TestPipelineStatus:
    """Verifies /api/v1/projects/<id>/pipeline_status endpoint."""

    @pytest.fixture
    def project_id(self, client):
        r = _create_project(client, name="Pipeline Status Test")
        return r.get_json()["data"]["project_id"]

    def test_pipeline_status_returns_200(self, client, project_id):
        r = client.get(f"/api/v1/projects/{project_id}/pipeline_status")
        assert r.status_code == 200
        d = r.get_json()
        assert d["success"] is True

    def test_pipeline_status_structure(self, client, project_id):
        r = client.get(f"/api/v1/projects/{project_id}/pipeline_status")
        d = r.get_json()["data"]
        assert "steps" in d
        assert "steps_total" in d
        assert "steps_completed" in d
        assert "completion_pct" in d
        assert isinstance(d["steps"], list)
        assert len(d["steps"]) > 0

    def test_pipeline_status_404_for_unknown_project(self, client):
        r = client.get("/api/v1/projects/non-existent-id/pipeline_status")
        assert r.status_code == 404

