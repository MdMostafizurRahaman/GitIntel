#!/usr/bin/env python3
from conversational_agent import ConversationalDatasetAgent

agent = ConversationalDatasetAgent()

print("=" * 80)
print("TESTING CONVERSATIONAL AGENT")
print("=" * 80)

# Test 1: Clear request
print("\n[TEST 1] Clear metric request")
result1 = agent.start_conversation("I want WMC, RFC, CBO metrics with their sum")
print(result1)

print("\n" + "="*80)
print("[FEEDBACK] Confirmed: WMC, RFC, CBO with (WMC+RFC+CBO)")

result2 = agent.refine_with_feedback("Yes, exactly. WMC, RFC, CBO and (WMC+RFC+CBO) as the formula. 200 records please.")
print(f"\nStatus: {result2['status']}")
if result2['status'] == 'ready_to_generate':
    print(f"Config: {result2['config']}")
    filepath = agent.generate_dataset(result2['config'])
    print(f"\n[SUCCESS] Dataset: {filepath}")

# Test 2: Ambiguous request
print("\n" + "=" * 80)
print("\n[TEST 2] Ambiguous request")
result3 = agent.start_conversation("I need complexity and coupling metrics with some calculation")
print(result3)
