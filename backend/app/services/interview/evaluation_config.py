# Mappings, thresholds, and weights for NextRound evaluations

# Map Turn Analysis enums to numerical score out of 100
QUALITY_SCORE_MAPPING = {
    "EXCELLENT": 100,
    "GOOD": 85,
    "FAIR": 65,
    "POOR": 40,
}

# Recommendation score boundaries
RECOMMENDATION_THRESHOLDS = [
    {"min": 90, "max": 100, "recommendation": "Strong Hire"},
    {"min": 80, "max": 89, "recommendation": "Hire"},
    {"min": 65, "max": 79, "recommendation": "Borderline Hire"},
    {"min": 0, "max": 64, "recommendation": "Needs Improvement"},
]

# Configurable weights for overall score calculation
EVALUATION_WEIGHTS = {
    "TECHNICAL": {
        "technical_accuracy": 0.40,
        "depth": 0.20,
        "coverage": 0.20,
        "communication": 0.10,
        "confidence": 0.10,
    },
    "BEHAVIORAL": {
        "technical_accuracy": 0.0,
        "depth": 0.25,
        "coverage": 0.0,
        "communication": 0.45,
        "confidence": 0.30,
    },
    "SYSTEM_DESIGN": {
        "technical_accuracy": 0.30,
        "depth": 0.30,
        "coverage": 0.20,
        "communication": 0.10,
        "confidence": 0.10,
    },
}

# Dynamic categories depending on the interview category type mapping
SKILL_NAME_MAPPINGS = {
    "TECHNICAL": {
        "Technical Knowledge": "technical_accuracy",
        "Depth of Answers": "depth",
        "Problem Solving": "coverage",
        "Communication": "communication",
        "Confidence": "confidence",
    },
    "BEHAVIORAL": {
        "Depth of Answers": "depth",
        "Communication": "communication",
        "Confidence": "confidence",
    },
    "SYSTEM_DESIGN": {
        "Technical Knowledge": "technical_accuracy",
        "Depth of Answers": "depth",
        "Problem Solving": "coverage",
        "Communication": "communication",
        "Confidence": "confidence",
    },
}
