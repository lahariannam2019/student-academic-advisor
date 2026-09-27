from typing import List, Dict, Any, Optional


def calculate_subject_performance(marks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Deterministically calculate subject weighted percentage, trend, and assessment summaries.

    Each mark item has:
        - name: str
        - assessment_type: str
        - max_marks: float
        - obtained_marks: float
        - weight: float (% of total subject grade, e.g. 20.0)
        - date: str
    """
    if not marks:
        return {
            "current_score_pct": None,
            "total_weight_evaluated": 0.0,
            "weighted_score": 0.0,
            "trend": "insufficient_data",
            "assessment_count": 0,
            "assessments": [],
        }

    total_weight = 0.0
    weighted_obtained = 0.0
    assessments_summary = []

    for m in marks:
        max_m = float(m.get("max_marks", 100))
        obt_m = float(m.get("obtained_marks", 0))
        weight = float(m.get("weight", 0))
        date_val = str(m.get("date", ""))

        if max_m <= 0:
            continue

        pct = round((obt_m / max_m) * 100.0, 2)
        total_weight += weight
        weighted_obtained += (obt_m / max_m) * weight

        assessments_summary.append({
            "name": m.get("name", "Assessment"),
            "type": m.get("assessment_type", "exam"),
            "percentage": pct,
            "obtained": obt_m,
            "max": max_m,
            "weight": weight,
            "date": date_val,
        })

    # Sort assessments chronologically if date present
    assessments_summary.sort(key=lambda x: x["date"])

    # Calculate current score normalized to 100%
    if total_weight > 0:
        current_score_pct = round((weighted_obtained / total_weight) * 100.0, 2)
    else:
        # Simple unweighted average fallback if weights are not provided
        scores = [a["percentage"] for a in assessments_summary]
        current_score_pct = round(sum(scores) / len(scores), 2) if scores else None

    # Trend calculation
    trend = "stable"
    if len(assessments_summary) >= 2:
        recent = assessments_summary[-1]["percentage"]
        prior = assessments_summary[-2]["percentage"]
        if recent > prior + 3.0:
            trend = "improving"
        elif recent < prior - 3.0:
            trend = "declining"

    return {
        "current_score_pct": current_score_pct,
        "total_weight_evaluated": round(total_weight, 2),
        "weighted_score": round(weighted_obtained, 2),
        "trend": trend,
        "assessment_count": len(assessments_summary),
        "assessments": assessments_summary,
    }
