#!/usr/bin/env python3
from autonomous_agent import AutonomousDatasetAgent, AgentMode

agent = AutonomousDatasetAgent()
mode, query = agent.parse_user_input("/agent large ck dataset")
plan = agent.generate_task_plan(query)
result = agent.execute_plan(plan, mode)

print("✅ Test Results:")
print(f"  Success: {result.get('success')}")
print(f"  Output file exists: {result.get('output_file')}")
print(f"  Tasks: {result.get('tasks_completed')}/{result.get('tasks_total')}")
