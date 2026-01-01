def build_report(url, findings):
    summary = {"High": 0, "Medium": 0, "Low": 0}
    score = 0

    weights = {"High": 20, "Medium": 10, "Low": 5}

    for f in findings:
        severity = f["severity"]
        if severity in summary:
            summary[severity] += 1
            score += weights.get(severity, 0)

    score = min(score, 100)

    return {
        "target": url,
        "summary": summary,
        "risk_score": score,
        "findings": findings,
    }
