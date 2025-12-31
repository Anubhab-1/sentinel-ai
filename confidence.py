def calculate_confidence(metadata):
    if not metadata.get("reachable"):
        return 20, "Low"

    score = 60

    https_ctx = metadata.get("https_context", {})
    header_consensus = metadata.get("header_consensus", {})

    # -----------------------------
    # Transport confidence
    # -----------------------------
    if https_ctx.get("https_only"):
        score += 15
    if https_ctx.get("redirects_to_https"):
        score += 10
    if https_ctx.get("http_accessible"):
        score -= 20

    # -----------------------------
    # Consensus quality
    # -----------------------------
    consistent_controls = 0
    partial_controls = 0

    for observations in header_consensus.values():
        unique = set(observations)
        if len(unique) == 1:
            consistent_controls += 1
        else:
            partial_controls += 1

    if consistent_controls >= 3:
        score += 10

    if partial_controls >= 3:
        score -= 15

    score = max(20, min(score, 95))

    if score >= 80:
        return score, "High"
    elif score >= 55:
        return score, "Medium"
    else:
        return score, "Low"
