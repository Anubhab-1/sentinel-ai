def adjust_severity(finding, metadata):
    header = finding["header"]
    severity = finding["severity"]
    reasons = finding.get("reasons", [])

    https_ctx = metadata.get("https_context", {})
    uses_js = metadata.get("uses_js", False)
    uses_forms = metadata.get("uses_forms", False)

    if header == "Content-Security-Policy":
        if not uses_js:
            reasons.append("No JavaScript detected, CSP impact reduced")
            return "Low"
        if https_ctx.get("https_only"):
            reasons.append("HTTPS enforced, CSP risk reduced")
            return "Medium"

    if header == "X-Frame-Options":
        if not uses_js and not uses_forms:
            reasons.append("No interactive UI detected, clickjacking risk reduced")
            return "Low"
        if https_ctx.get("https_only"):
            reasons.append("HTTPS-only site, clickjacking surface reduced")
            return "Low"

    if header == "X-Content-Type-Options":
        if https_ctx.get("https_only"):
            reasons.append("Modern browser mitigations apply under HTTPS")
            return "Low"

    if header == "Referrer-Policy":
        reasons.append("Low impact unless sensitive URL parameters exist")
        return "Low"

    if header == "Strict-Transport-Security":
        if https_ctx.get("http_accessible"):
            reasons.append("Site accessible over HTTP, HSTS critical")
            return "High"
        if https_ctx.get("redirects_to_https"):
            reasons.append("HTTP redirects to HTTPS, HSTS risk reduced")
            return "Medium"
        reasons.append("HTTPS-only access observed")
        return "Low"

    return severity
