import json

STATE_FILE = "alert_state.json"


def load_state():
    with open(STATE_FILE, "r") as file:
        return json.load(file)


def save_state(state):
    with open(STATE_FILE, "w") as file:
        json.dump(state, file, indent=2)


def get_new_triggers(symbol, timeframe, triggered_conditions, state):
    new_triggers = []

    for condition in ["C1", "C2", "C3", "C4"]:
        key = f"{symbol}_{timeframe}_{condition}"

        is_triggered = condition in triggered_conditions
        was_triggered = state.get(key, False)

        if is_triggered and not was_triggered:
            new_triggers.append(condition)

        state[key] = is_triggered

    return new_triggers