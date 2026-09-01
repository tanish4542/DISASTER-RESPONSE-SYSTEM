"""Priority calculation service for emergencies."""

def calculate_priority_score(urgency, people_affected, injured, trapped, fire, medical_emergency):
    """Calculate priority score (0-100)."""
    score = urgency * 10
    if injured:
        score += 25
    if trapped:
        score += 25
    if fire:
        score += 20
    if medical_emergency:
        score += 20
    if people_affected >= 10:
        score += 30
    elif people_affected >= 5:
        score += 20
    elif people_affected >= 2:
        score += 10
    return min(score, 100)

def get_priority_level(score):
    """Determine priority level from score."""
    if score >= 80:
        return "CRITICAL"
    elif score >= 60:
        return "HIGH"
    elif score >= 30:
        return "MEDIUM"
    else:
        return "LOW"

def calculate_priority(urgency, people_affected, injured, trapped, fire, medical_emergency):
    """Calculate both priority score and level."""
    score = calculate_priority_score(urgency, people_affected, injured, trapped, fire, medical_emergency)
    level = get_priority_level(score)
    return score, level
