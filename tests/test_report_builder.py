from report_builder import build_report

def test_build_report_structure():
    findings = [
        {"severity": "High", "issue": "SQLi"},
        {"severity": "Low", "issue": "Info Leak"}
    ]
    report = build_report("http://test.com", findings)
    
    assert report["target"] == "http://test.com"
    assert report["risk_score"] == 25 # 20 (High) + 5 (Low)
    assert report["summary"]["High"] == 1
    assert report["summary"]["Low"] == 1
    assert len(report["findings"]) == 2

def test_build_report_empty():
    report = build_report("http://test.com", [])
    assert report["risk_score"] == 0
    assert report["summary"]["High"] == 0
