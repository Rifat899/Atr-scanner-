from conditions import check_conditions

settings = {
    "C1": {"enabled": True, "threshold": 0.5},
    "C2": {"enabled": True, "threshold": 3.0},
    "C3": {"enabled": True, "threshold": 0.5},
    "C4": {"enabled": True, "threshold": 0.5}
}

result = check_conditions(3.5, 2.8, settings)

print("Triggered conditions:", result)