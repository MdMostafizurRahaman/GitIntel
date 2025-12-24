#!/usr/bin/env python3
"""Test real dataset generation"""

from autonomous_agent import AutonomousDatasetAgent, AgentMode
import json

agent = AutonomousDatasetAgent()
agent.set_repository(".")  # Current directory

query = "I need kloc, ssoc, loc & (kloc+ssoc+loc)/3"
print(f"Query: {query}\n")

# Generate plan
plan = agent.generate_task_plan(query)
print(f"Plan Intent: {plan.get('intent')}")
print(f"Metrics: {plan.get('metrics')}\n")

# Execute in AGENT mode
print("Executing plan...")
result = agent.execute_plan(plan, AgentMode.AGENT)

print("\nExecution Result:")
for msg in result.get('messages', []):
    print(f"  {msg}")

print(f"\nOutput file: {result.get('output_file')}")
print(f"Success: {result['success']}")
print(f"Tasks completed: {result['tasks_completed']}/{result['tasks_total']}")

# Check if file exists
if result.get('output_file'):
    import os
    if os.path.exists(result['output_file']):
        print(f"✅ File exists: {result['output_file']}")
        with open(result['output_file']) as f:
            lines = f.readlines()
            print(f"   Lines: {len(lines)}")
            print(f"   Header: {lines[0].strip()}")
    else:
        print(f"❌ File not found: {result['output_file']}")
