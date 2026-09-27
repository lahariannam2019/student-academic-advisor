import math
from typing import Dict, Any


def calculate_attendance_metrics(
    attended_classes: int,
    total_classes: int,
    target_pct: float = 75.0,
) -> Dict[str, Any]:
    """
    Deterministically calculate attendance percentage, safety margin,
    classes needed (if below target), or classes that can be missed (if above target).

    Args:
        attended_classes: Number of classes attended (present).
        total_classes: Total number of classes held (excluding cancelled).
        target_pct: Target minimum attendance percentage (e.g. 75.0).

    Returns:
        Dict containing:
            - percentage: float (e.g. 88.0)
            - status: 'safe' | 'warning' | 'critical'
            - classes_needed: int (if below target)
            - classes_can_miss: int (if above target)
            - is_below_target: bool
    """
    # Edge case 1: No classes held yet
    if total_classes <= 0:
        return {
            "percentage": 100.0,
            "status": "safe",
            "classes_needed": 0,
            "classes_can_miss": 0,
            "is_below_target": False,
            "attended": 0,
            "total": 0,
            "target_pct": target_pct,
        }

    # Ensure attended cannot exceed total
    attended = min(attended_classes, total_classes)
    percentage = round((attended / total_classes) * 100.0, 2)
    target_ratio = target_pct / 100.0

    classes_needed = 0
    classes_can_miss = 0
    is_below_target = percentage < target_pct

    if is_below_target:
        # Edge case: Target >= 100% and student already missed a class
        if target_ratio >= 1.0:
            classes_needed = 999  # Mathematically impossible to reach 100% once missed
        else:
            # Formula: (A + c) / (T + c) >= target_ratio
            # c * (1 - target_ratio) >= target_ratio * T - A
            numerator = (target_ratio * total_classes) - attended
            if numerator > 0:
                classes_needed = math.ceil(numerator / (1.0 - target_ratio))
            else:
                classes_needed = 1
    else:
        # Above or equal to target
        if target_ratio <= 0:
            classes_can_miss = 999
        else:
            # Formula: A / (T + m) >= target_ratio
            # A - target_ratio * T >= target_ratio * m
            numerator = attended - (target_ratio * total_classes)
            classes_can_miss = max(0, math.floor(numerator / target_ratio))

    # Determine status
    if percentage < target_pct:
        status = "critical"
    elif percentage < target_pct + 5.0:
        status = "warning"
    else:
        status = "safe"

    return {
        "percentage": percentage,
        "status": status,
        "classes_needed": classes_needed,
        "classes_can_miss": classes_can_miss,
        "is_below_target": is_below_target,
        "attended": attended,
        "total": total_classes,
        "target_pct": target_pct,
    }
