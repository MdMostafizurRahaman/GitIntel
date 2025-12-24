#!/usr/bin/env python3
"""Debug test for custom formula handling"""

from autonomous_agent import AutonomousDatasetAgent

agent = AutonomousDatasetAgent()
print('Testing Gemini LLM...')

# Test with custom formula
query = 'I need kloc, ssoc, loc & (kloc+ssoc+loc)/3'
print(f'Query: {query}')
print()

plan = agent.generate_task_plan(query)
print('Plan generated:')
print(f'  Intent: {plan.get("intent")}')
print(f'  Metrics: {plan.get("metrics")}')
print(f'  Confidence: {plan.get("confidence")}')
print(f'  Reasoning: {plan.get("reasoning")}')
print()
print('Full plan:')
import json
print(json.dumps(plan, indent=2))
