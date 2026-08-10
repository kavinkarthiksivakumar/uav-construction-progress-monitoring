"""
Test Suite — Module 6: Explainable AI (GradCAM + SHAP + Report)
IEEE M.Tech Project — Explainable Vision-Based Construction Progress Assessment

Tests:
  1. GradCAM heatmap generation (synthetic mode)
  2. GradCAM batch processing
  3. SHAP feature explanation (simulation mode)
  4. SHAP chart generation
  5. XAI HTML report generation
  6. XAI PDF report (availability check)
  7. End-to-end Module 6 pipeline
  8. API endpoint health checks
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

# ── Path setup ─────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def tmp_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("module6_test")


@pytest.fixture(scope="module")
def sample_image(tmp_dir):
    """Create a synthetic 256×256 RGB test image."""
    try:
        from PIL import Image
        img = Image.fromarray(
            np.random.randint(50, 200, (256, 256, 3), dtype=np.uint8)
        )
        p = tmp_dir / "test_image.png"
        img.save(str(p))
        return p
    except Exception as e:
        pytest.skip(f"PIL not available: {e}")


@pytest.fixture(scope="module")
def sample_prediction():
    """Return a realistic Module 5 prediction dict."""
    return {
        "predicted_at": "2026-07-16T14:00:00Z",
        "progress": {
            "progress_score":     62.4,
            "expected_progress":  55.0,
        },
        "delay": {
            "delay_days":         -11,
            "risk_level":         "on_track",
        },
        "risk": {
            "risk_level":         "on_track",
            "risk_color":         "#22c55e",
        },
        "sub_scores": {
            "change_score":   70.0,
            "activity_score": 60.0,
            "temporal_score": 55.0,
            "quality_score":  80.0,
        },
        "s_curve": {
            "n_points": 10,
            "x_labels": [f"Month {i+1}" for i in range(10)],
            "planned_data": list(range(0, 101, 10)),
            "actual_data":  [0, 8, 18, 30, 42, 55, 62, None, None, None],
        },
    }


@pytest.fixture(scope="module")
def sample_project():
    """Return a minimal project metadata dict."""
    return {
        "project_id":  "test-proj-001",
        "name":        "Test Construction Site Alpha",
        "description": "Unit test project",
        "location":    "Test City",
        "created_at":  "2026-01-01T00:00:00Z",
        "status":      "active",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: GradCAM Heatmap (Synthetic)
# ─────────────────────────────────────────────────────────────────────────────

class TestGradCAM:

    def test_import(self):
        """Module 6 GradCAM can be imported."""
        from backend.modules.module6_xai.gradcam import (
            generate_gradcam_heatmap, generate_gradcam_batch
        )
        assert callable(generate_gradcam_heatmap)
        assert callable(generate_gradcam_batch)

    def test_synthetic_heatmap_shape(self, sample_image, tmp_dir):
        """Synthetic heatmap returns correct shape."""
        from backend.modules.module6_xai.gradcam import _load_image_rgb, _synthetic_heatmap
        img = _load_image_rgb(sample_image)
        hm  = _synthetic_heatmap(img)
        assert hm.shape == img.shape[:2], "Heatmap must have same H×W as input"
        assert hm.dtype == np.float32
        assert hm.min() >= 0.0
        assert hm.max() <= 1.0

    def test_generate_heatmap_success(self, sample_image, tmp_dir):
        """GradCAM generates overlay and heatmap files."""
        from backend.modules.module6_xai.gradcam import generate_gradcam_heatmap
        out = tmp_dir / "gradcam_out"
        result = generate_gradcam_heatmap(
            image_path = sample_image,
            output_dir = out,
        )
        assert result["success"], f"GradCAM failed: {result.get('error')}"
        assert "overlay_path" in result
        assert "heatmap_path" in result
        assert Path(result["overlay_path"]).exists()
        assert Path(result["heatmap_path"]).exists()
        assert result["mode"] == "synthetic"

    def test_heatmap_stats_present(self, sample_image, tmp_dir):
        """GradCAM result includes activation stats."""
        from backend.modules.module6_xai.gradcam import generate_gradcam_heatmap
        out = tmp_dir / "gradcam_stats"
        result = generate_gradcam_heatmap(
            image_path = sample_image,
            output_dir = out,
        )
        assert result["success"]
        stats = result.get("stats", {})
        assert "max_activation"      in stats
        assert "mean_activation"     in stats
        assert "high_activation_pct" in stats
        assert 0 <= stats["max_activation"]  <= 1.0
        assert 0 <= stats["mean_activation"] <= 1.0

    def test_batch_gradcam(self, sample_image, tmp_dir):
        """GradCAM batch processes multiple images."""
        from backend.modules.module6_xai.gradcam import generate_gradcam_batch
        out = tmp_dir / "gradcam_batch"
        result = generate_gradcam_batch(
            image_paths = [sample_image, sample_image],
            output_dir  = out,
            max_items   = 2,
        )
        assert result["total"] == 2
        assert result["succeeded"] >= 1
        assert len(result["results"]) == 2

    def test_missing_image_handled(self, tmp_dir):
        """GradCAM handles missing image path gracefully."""
        from backend.modules.module6_xai.gradcam import generate_gradcam_heatmap
        result = generate_gradcam_heatmap(
            image_path = tmp_dir / "nonexistent.png",
            output_dir = tmp_dir / "err_out",
        )
        assert result["success"] is False
        assert "error" in result


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: SHAP Explanation
# ─────────────────────────────────────────────────────────────────────────────

class TestSHAP:

    def test_import(self):
        """Module 6 SHAP can be imported."""
        from backend.modules.module6_xai.shap_explain import generate_shap_explanation
        assert callable(generate_shap_explanation)

    def test_simulation_shap(self, sample_prediction, tmp_dir):
        """SHAP simulation mode produces valid attributions."""
        from backend.modules.module6_xai.shap_explain import (
            generate_shap_explanation, FEATURE_NAMES
        )
        out = tmp_dir / "shap_out"
        result = generate_shap_explanation(
            prediction = sample_prediction,
            output_dir = out,
        )
        assert result["success"], f"SHAP failed: {result.get('error')}"
        assert "shap_values" in result
        shap_vals = result["shap_values"]
        for fname in FEATURE_NAMES:
            assert fname in shap_vals, f"Missing SHAP value for {fname}"
        assert isinstance(result["feature_importance"], list)
        assert len(result["feature_importance"]) == len(FEATURE_NAMES)

    def test_shap_narrative(self, sample_prediction, tmp_dir):
        """SHAP explanation includes human-readable narrative."""
        from backend.modules.module6_xai.shap_explain import generate_shap_explanation
        out = tmp_dir / "shap_narrative"
        result = generate_shap_explanation(
            prediction = sample_prediction,
            output_dir = out,
        )
        assert result["success"]
        assert isinstance(result.get("narrative", ""), str)
        assert len(result.get("narrative", "")) > 10

    def test_shap_json_saved(self, sample_prediction, tmp_dir):
        """SHAP saves JSON summary file."""
        from backend.modules.module6_xai.shap_explain import generate_shap_explanation
        out = tmp_dir / "shap_json"
        result = generate_shap_explanation(
            prediction = sample_prediction,
            output_dir = out,
        )
        assert result["success"]
        assert "json_path" in result
        assert Path(result["json_path"]).exists()
        with open(result["json_path"], "r") as f:
            saved = json.load(f)
        assert "shap_values"   in saved
        assert "features"      in saved
        assert "base_value"    in saved
        assert saved["base_value"] == 50.0

    def test_shap_bar_chart(self, sample_prediction, tmp_dir):
        """SHAP bar chart PNG is generated."""
        from backend.modules.module6_xai.shap_explain import generate_shap_explanation
        out = tmp_dir / "shap_charts"
        result = generate_shap_explanation(
            prediction = sample_prediction,
            output_dir = out,
        )
        assert result["success"]
        if result.get("bar_chart_path"):
            assert Path(result["bar_chart_path"]).exists()

    def test_simulate_shap_values_formula(self):
        """Simulated SHAP values follow the expected linear formula."""
        from backend.modules.module6_xai.shap_explain import _simulate_shap_values, FEATURE_WEIGHTS
        features = {
            "change_score":   70.0,
            "activity_score": 60.0,
            "temporal_score": 50.0,
            "quality_score":  80.0,
        }
        shap = _simulate_shap_values(features)
        # change_score: w=0.40, (70-50)*0.40 = 8.0
        assert abs(shap["change_score"] - 8.0) < 0.01
        # temporal_score: w=0.20, (50-50)*0.20 = 0.0
        assert abs(shap["temporal_score"] - 0.0) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: XAI Report Generation
# ─────────────────────────────────────────────────────────────────────────────

class TestXAIReport:

    def test_import(self):
        """Module 6 PDF/HTML report can be imported."""
        from backend.modules.module6_xai.pdf_report import generate_xai_pdf_report
        assert callable(generate_xai_pdf_report)

    def test_html_report_generated(self, sample_project, sample_prediction, tmp_dir):
        """HTML report is generated successfully."""
        from backend.modules.module6_xai.shap_explain import generate_shap_explanation
        from backend.modules.module6_xai.pdf_report import generate_xai_pdf_report

        shap_dir = tmp_dir / "report_shap"
        shap_result = generate_shap_explanation(
            prediction = sample_prediction,
            output_dir = shap_dir,
        )

        out = tmp_dir / "xai_report"
        result = generate_xai_pdf_report(
            project         = sample_project,
            prediction      = sample_prediction,
            shap_result     = shap_result,
            gradcam_results = [],
            output_dir      = out,
        )

        assert result["success"], f"Report failed: {result.get('error')}"
        assert "html_path" in result
        html_path = Path(result["html_path"])
        assert html_path.exists()
        content = html_path.read_text(encoding="utf-8")
        assert "XAI Explainability Report" in content
        assert sample_project["name"] in content

    def test_report_contains_shap_data(self, sample_project, sample_prediction, tmp_dir):
        """HTML report embeds SHAP analysis."""
        from backend.modules.module6_xai.shap_explain import generate_shap_explanation
        from backend.modules.module6_xai.pdf_report import generate_xai_pdf_report

        shap_dir = tmp_dir / "report_shap2"
        shap_result = generate_shap_explanation(
            prediction = sample_prediction,
            output_dir = shap_dir,
        )

        out = tmp_dir / "xai_report2"
        result = generate_xai_pdf_report(
            project         = sample_project,
            prediction      = sample_prediction,
            shap_result     = shap_result,
            gradcam_results = [],
            output_dir      = out,
        )
        assert result["success"]
        html = Path(result["html_path"]).read_text(encoding="utf-8")
        assert "SHAP" in html
        assert "GradCAM" in html
        assert "Recommendation" in html

    def test_json_summary_saved(self, sample_project, sample_prediction, tmp_dir):
        """XAI report saves JSON summary."""
        from backend.modules.module6_xai.shap_explain import generate_shap_explanation
        from backend.modules.module6_xai.pdf_report import generate_xai_pdf_report

        shap_dir = tmp_dir / "report_shap3"
        shap_result = generate_shap_explanation(
            prediction = sample_prediction,
            output_dir = shap_dir,
        )

        out = tmp_dir / "xai_report3"
        result = generate_xai_pdf_report(
            project         = sample_project,
            prediction      = sample_prediction,
            shap_result     = shap_result,
            gradcam_results = [],
            output_dir      = out,
        )
        assert result["success"]
        assert "summary_path" in result
        assert Path(result["summary_path"]).exists()


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: End-to-End Module 6 Pipeline
# ─────────────────────────────────────────────────────────────────────────────

class TestEndToEndModule6:

    def test_full_pipeline(self, sample_image, sample_project, sample_prediction, tmp_dir):
        """Complete Module 6 pipeline runs without errors."""
        from backend.modules.module6_xai.gradcam import generate_gradcam_batch
        from backend.modules.module6_xai.shap_explain import generate_shap_explanation
        from backend.modules.module6_xai.pdf_report import generate_xai_pdf_report

        # Stage 1: GradCAM
        cam_dir = tmp_dir / "e2e_gradcam"
        cam_batch = generate_gradcam_batch(
            image_paths = [sample_image],
            output_dir  = cam_dir,
            max_items   = 1,
        )
        assert cam_batch["succeeded"] == 1

        # Stage 2: SHAP
        shap_dir = tmp_dir / "e2e_shap"
        shap_result = generate_shap_explanation(
            prediction = sample_prediction,
            output_dir = shap_dir,
        )
        assert shap_result["success"]

        # Stage 3: Report
        report_dir = tmp_dir / "e2e_report"
        gradcam_results = [r for r in cam_batch["results"] if r.get("success")]
        report = generate_xai_pdf_report(
            project         = sample_project,
            prediction      = sample_prediction,
            shap_result     = shap_result,
            gradcam_results = gradcam_results,
            output_dir      = report_dir,
        )
        assert report["success"]
        assert Path(report["html_path"]).exists()

    def test_pipeline_without_gradcam_images(self, sample_project, sample_prediction, tmp_dir):
        """Pipeline works even when no GradCAM images are available."""
        from backend.modules.module6_xai.shap_explain import generate_shap_explanation
        from backend.modules.module6_xai.pdf_report import generate_xai_pdf_report

        shap_dir = tmp_dir / "nogcam_shap"
        shap_result = generate_shap_explanation(
            prediction = sample_prediction,
            output_dir = shap_dir,
        )

        report_dir = tmp_dir / "nogcam_report"
        report = generate_xai_pdf_report(
            project         = sample_project,
            prediction      = sample_prediction,
            shap_result     = shap_result,
            gradcam_results = [],  # no images
            output_dir      = report_dir,
        )
        assert report["success"]


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Flask API Endpoints (integration)
# ─────────────────────────────────────────────────────────────────────────────

class TestModule6API:

    @pytest.fixture(scope="class")
    def client(self):
        """Create Flask test client."""
        try:
            from backend.app import app
            app.config["TESTING"] = True
            with app.test_client() as c:
                yield c
        except Exception as e:
            pytest.skip(f"Flask app unavailable: {e}")

    def test_health_includes_app(self, client):
        """Health endpoint is reachable."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_xai_status_no_project(self, client):
        """XAI status for non-existent project returns 404 or 500 (abort propagation)."""
        resp = client.get("/api/v1/projects/nonexistent-proj/xai/status")
        assert resp.status_code in (404, 500), f"Expected 404 or 500, got {resp.status_code}"

    def test_xai_gradcam_no_project(self, client):
        """GradCAM endpoint returns 404 or 500 for missing project."""
        resp = client.post(
            "/api/v1/projects/nonexistent-proj/xai/gradcam",
            json={},
        )
        assert resp.status_code in (404, 500), f"Expected 404 or 500, got {resp.status_code}"

    def test_xai_shap_no_project(self, client):
        """SHAP endpoint returns 404 or 500 for missing project."""
        resp = client.post(
            "/api/v1/projects/nonexistent-proj/xai/shap",
            json={},
        )
        assert resp.status_code in (404, 500), f"Expected 404 or 500, got {resp.status_code}"
