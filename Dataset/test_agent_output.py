#!/usr/bin/env python3
from autonomous_agent import AutonomousDatasetAgent, AgentMode

agent = AutonomousDatasetAgent()

# Parse user input
mode, query = agent.parse_user_input("/agent make a large dataset of ck metrics with kloc/1000")
print(f"Mode: {mode}")
print(f"Query: {query}")
print()

# Generate plan
plan = agent.generate_task_plan(query)
print(f"Plan intent: {plan.get('intent')}")
print(f"Plan metrics: {plan.get('metrics')}")
print(f"Plan tasks: {len(plan.get('tasks', []))} tasks")
print()

# Execute plan
result = agent.execute_plan(plan, mode)
print(f"Success: {result.get('success')}")
print(f"Tasks completed: {result.get('tasks_completed')}/{result.get('tasks_total')}")
print(f"Output file: {result.get('output_file')}")
print()
print("Messages:")
for msg in result.get('messages', []):
    print(f"  - {msg}")
