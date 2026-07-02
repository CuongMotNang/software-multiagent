"""Test ArtifactStore - với sandbox thật."""

import json
import shutil
import sys
from pathlib import Path

# Setup path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import graph.artifact_store as store

# Dùng sandbox thật (KHÔNG override)
THREAD_ID = "test_hitl_001"
ARTIFACTS_DIR = store.SANDBOX_ROOT / "workspace" / THREAD_ID / "artifacts"

def cleanup():
    """Xóa thư mục test trước khi chạy."""
    if ARTIFACTS_DIR.exists():
        shutil.rmtree(ARTIFACTS_DIR.parent)

def test_prd():
    store.save_prd(THREAD_ID, "# PRD Test\n\nĐây là PRD mẫu.")
    content = store.read_prd(THREAD_ID)
    assert content == "# PRD Test\n\nĐây là PRD mẫu.", f"FAIL: {content}"
    print("✓ PRD test passed")

def test_design():
    store.save_design(THREAD_ID, "# Design Doc\n\n## Kiến trúc\n- Microservices")
    content = store.read_design(THREAD_ID)
    assert "Microservices" in content, f"FAIL: {content}"
    print("✓ Design test passed")

def test_mockup():
    store.save_mockup(THREAD_ID, "<html><body><h1>Mockup Test</h1></body></html>")
    content = store.read_mockup(THREAD_ID)
    assert "<h1>Mockup Test</h1>" in content, f"FAIL: {content}"
    print("✓ Mockup test passed")

def test_test_report():
    report = {"passed": 5, "failed": 1, "coverage": 87.5, "recommendations": ["Add more tests"]}
    store.save_test_report(THREAD_ID, report)
    loaded = store.read_test_report(THREAD_ID)
    assert loaded == report, f"FAIL: {loaded}"
    print("✓ Test report passed")

def test_test_results():
    log = "tests/test_a.py::test_x PASSED\ntests/test_b.py::test_y FAILED\nAssertionError..."
    store.save_test_results(THREAD_ID, log)
    content = store.read_test_results(THREAD_ID)
    assert "PASSED" in content and "FAILED" in content, f"FAIL: {content}"
    print("✓ Test results passed")

def test_engineer_log():
    log = "OpenHands completed OK.\nNew files: 3\n  - app.py\n  - requirements.txt\n  - README.md"
    store.save_engineer_log(THREAD_ID, log)
    content = store.read_engineer_log(THREAD_ID)
    assert "app.py" in content, f"FAIL: {content}"
    print("✓ Engineer log passed")

def test_manifest():
    manifest = {
        "thread_id": THREAD_ID,
        "created_at": store._now(),
        "artifacts": ["prd_v1.md", "design_doc.md", "mockup.html"]
    }
    store.save_manifest(THREAD_ID, manifest)
    loaded = store.read_manifest(THREAD_ID)
    assert loaded["thread_id"] == THREAD_ID, f"FAIL: {loaded}"
    print("✓ Manifest test passed")

def test_list_artifacts():
    files = store.list_artifacts(THREAD_ID)
    expected = ["design_doc.md", "engineer_log.txt", "manifest.json", "mockup.html", "prd_v1.md", "test_report.json", "test_results.txt"]
    assert len(files) == len(expected), f"FAIL: Expected {len(expected)} files, got {len(files)}"
    print(f"✓ List artifacts: {len(files)} files")
    for f in files:
        print(f"   - {f}")

def test_directory_structure():
    """Kiểm tra cấu trúc thư mục thật."""
    assert ARTIFACTS_DIR.exists(), f"FAIL: Artifacts dir not found: {ARTIFACTS_DIR}"
    assert ARTIFACTS_DIR.is_dir(), f"FAIL: Not a directory: {ARTIFACTS_DIR}"
    
    # Kiểm tra từng file
    expected_files = [
        "prd_v1.md",
        "design_doc.md", 
        "mockup.html",
        "test_report.json",
        "test_results.txt",
        "engineer_log.txt",
        "manifest.json"
    ]
    
    for fname in expected_files:
        fpath = ARTIFACTS_DIR / fname
        assert fpath.exists(), f"FAIL: Missing file {fname}"
        assert fpath.stat().st_size > 0, f"FAIL: Empty file {fname}"
    
    print(f"✓ Directory structure OK: {ARTIFACTS_DIR}")

if __name__ == "__main__":
    print("=" * 60)
    print(f"Testing ArtifactStore với sandbox thật:")
    print(f"  Path: {ARTIFACTS_DIR}")
    print("=" * 60)
    
    cleanup()
    
    test_prd()
    test_design()
    test_mockup()
    test_test_report()
    test_test_results()
    test_engineer_log()
    test_manifest()
    test_list_artifacts()
    test_directory_structure()
    
    print("\n" + "=" * 60)
    print("PM: ALL TESTS PASSED ✓")
    print("=" * 60)
    print(f"\nArtifacts đã được lưu tại:")
    print(f"  {ARTIFACTS_DIR}")
