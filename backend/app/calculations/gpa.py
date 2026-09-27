from typing import List, Dict, Any, Optional

# Supported grading scale tables
GRADING_SCALES = {
    "10_point": [
        {"min_pct": 90.0, "grade": "O", "points": 10.0},
        {"min_pct": 80.0, "grade": "A+", "points": 9.0},
        {"min_pct": 70.0, "grade": "A", "points": 8.0},
        {"min_pct": 60.0, "grade": "B+", "points": 7.0},
        {"min_pct": 50.0, "grade": "B", "points": 6.0},
        {"min_pct": 40.0, "grade": "C", "points": 5.0},
        {"min_pct": 0.0, "grade": "F", "points": 0.0},
    ],
    "4_point": [
        {"min_pct": 93.0, "grade": "A", "points": 4.0},
        {"min_pct": 90.0, "grade": "A-", "points": 3.7},
        {"min_pct": 87.0, "grade": "B+", "points": 3.3},
        {"min_pct": 83.0, "grade": "B", "points": 3.0},
        {"min_pct": 80.0, "grade": "B-", "points": 2.7},
        {"min_pct": 75.0, "grade": "C+", "points": 2.3},
        {"min_pct": 70.0, "grade": "C", "points": 2.0},
        {"min_pct": 60.0, "grade": "D", "points": 1.0},
        {"min_pct": 0.0, "grade": "F", "points": 0.0},
    ],
}


def percentage_to_grade_point(pct: float, scale_name: str = "10_point") -> Dict[str, Any]:
    """Convert an assessment percentage to grade and grade points based on scale."""
    scale = GRADING_SCALES.get(scale_name, GRADING_SCALES["10_point"])
    for bracket in scale:
        if pct >= bracket["min_pct"]:
            return {
                "grade": bracket["grade"],
                "points": bracket["points"],
                "scale": scale_name,
            }
    return {"grade": "F", "points": 0.0, "scale": scale_name}


def calculate_sgpa(subjects: List[Dict[str, Any]], scale_name: str = "10_point") -> Dict[str, Any]:
    """
    Calculate Semester Grade Point Average (SGPA) with credit-weighting.

    Each subject dict:
        - credits: float
        - percentage: float (or grade_point directly)
    """
    total_credits = 0.0
    total_weighted_points = 0.0

    for s in subjects:
        credits = float(s.get("credits", 0))
        if credits <= 0:
            continue

        if "grade_point" in s and s["grade_point"] is not None:
            gp = float(s["grade_point"])
        elif "percentage" in s and s["percentage"] is not None:
            gp = percentage_to_grade_point(float(s["percentage"]), scale_name)["points"]
        else:
            continue

        total_credits += credits
        total_weighted_points += gp * credits

    if total_credits == 0:
        return {"sgpa": None, "total_credits": 0.0}

    sgpa = round(total_weighted_points / total_credits, 2)
    return {"sgpa": sgpa, "total_credits": total_credits}


def calculate_cgpa(
    past_semesters: List[Dict[str, Any]],
    current_sgpa: Optional[float] = None,
    current_credits: float = 0.0,
) -> Dict[str, Any]:
    """
    Calculate Cumulative Grade Point Average (CGPA) credit-weighted across semesters.

    Each past semester dict:
        - sgpa: float
        - total_credits: float
    """
    total_credits = 0.0
    total_grade_points = 0.0

    for sem in past_semesters:
        credits = float(sem.get("total_credits", 0))
        sgpa = sem.get("sgpa")
        if credits > 0 and sgpa is not None:
            total_credits += credits
            total_grade_points += float(sgpa) * credits

    if current_sgpa is not None and current_credits > 0:
        total_credits += current_credits
        total_grade_points += current_sgpa * current_credits

    if total_credits == 0:
        return {"cgpa": 0.0, "total_credits": 0.0}

    cgpa = round(total_grade_points / total_credits, 2)
    return {
        "cgpa": cgpa,
        "total_credits": total_credits,
        "total_grade_points": round(total_grade_points, 2),
    }


def calculate_goal_feasibility(
    current_cgpa: float,
    completed_credits: float,
    target_cgpa: float,
    remaining_credits: float = 40.0,
    max_scale_point: float = 10.0,
) -> Dict[str, Any]:
    """
    Mathematically calculate whether a student's target CGPA is achievable
    across their remaining degree credits.

    Formula:
        Target_CGPA = (Current_Points + Required_SGPA * Rem_Credits) / (Done_Credits + Rem_Credits)
        Required_SGPA = (Target_CGPA * Total_Degree_Credits - Current_Points) / Rem_Credits
    """
    if remaining_credits <= 0:
        return {
            "feasible": current_cgpa >= target_cgpa,
            "required_sgpa": None,
            "message": "No remaining credits registered.",
        }

    current_points = current_cgpa * completed_credits
    total_degree_credits = completed_credits + remaining_credits
    target_total_points = target_cgpa * total_degree_credits
    points_needed = target_total_points - current_points

    required_sgpa = round(points_needed / remaining_credits, 2)
    is_feasible = required_sgpa <= max_scale_point

    if is_feasible and required_sgpa <= 0:
        message = f"Your target of {target_cgpa:.2f} is already virtually locked with your current {current_cgpa:.2f} CGPA."
    elif is_feasible:
        message = (
            f"Achievable: You need an average SGPA of {required_sgpa:.2f} across your remaining "
            f"{int(remaining_credits)} credits to hit {target_cgpa:.2f} CGPA."
        )
    else:
        message = (
            f"Mathematically impossible under a {max_scale_point:.1f} scale: Reaching {target_cgpa:.2f} "
            f"would require an unattainable SGPA of {required_sgpa:.2f} (> {max_scale_point:.1f})."
        )

    return {
        "feasible": is_feasible,
        "required_sgpa": required_sgpa,
        "current_cgpa": current_cgpa,
        "target_cgpa": target_cgpa,
        "remaining_credits": remaining_credits,
        "message": message,
    }
