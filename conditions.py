def check_conditions(current_atr, previous_atr, settings):
    results = []

    change = current_atr - previous_atr

    for condition, config in settings.items():

        if not config["enabled"]:
            continue

        threshold = config["threshold"]
        triggered = False

        if condition == "C1":
            triggered = abs(change) >= threshold

        elif condition == "C2":
            triggered = current_atr >= threshold

        elif condition == "C3":
            triggered = change >= threshold

        elif condition == "C4":
            triggered = change <= -threshold

        if triggered:
            results.append(condition)

    return results
