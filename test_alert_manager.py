from alert_manager import get_new_triggers

state = {}

print("TEST 1: First trigger")
result = get_new_triggers("BTCUSDT", "4H", ["C1"], state)
print("New alerts:", result)

print("\nTEST 2: Same trigger again")
result = get_new_triggers("BTCUSDT", "4H", ["C1"], state)
print("New alerts:", result)

print("\nTEST 3: Condition resets")
result = get_new_triggers("BTCUSDT", "4H", [], state)
print("New alerts:", result)

print("\nTEST 4: Condition triggers again")
result = get_new_triggers("BTCUSDT", "4H", ["C1"], state)
print("New alerts:", result)