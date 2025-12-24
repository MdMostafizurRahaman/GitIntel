#!/usr/bin/env python3
from autonomous_agent import AutonomousDatasetAgent, AgentMode

agent = AutonomousDatasetAgent()

# Test with the exact user request
query = "make dataset of Weighted Methods per Class (WMC), Depth of Inheritance Tree (DIT), Number of Children (NOC), Coupling Between Objects (CBO), Response For a Class (RFC), Lack of Cohesion of Methods (LCOM) and Weighted Methods per Class (WMC) + Depth of Inheritance Tree (DIT) + Number of Children (NOC) + Coupling Between Objects (CBO) + Response For a Class (RFC) + Lack of Cohesion of Methods (LCOM)"

mode, clean_query = agent.parse_user_input(f"/agent {query}")
print(f"🤖 Mode: {mode}")
print(f"📝 Query: {clean_query[:100]}...")
print()

plan = agent.generate_task_plan(clean_query)
print(f"📊 Metrics detected: {plan.get('metrics')}")
print()

result = agent.execute_plan(plan, mode)
print(f"✅ Success: {result.get('success')}")
print(f"📈 Tasks: {result.get('tasks_completed')}/{result.get('tasks_total')}")
print(f"📁 Output file: {result.get('output_file')}")

# Check the file content
import csv
if result.get('output_file'):
    print("\n✅ DATASET PREVIEW:")
    with open(result['output_file'], 'r') as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        print(f"📋 Columns: {header}")
        print("\n📊 First 3 rows:")
        for i, row in enumerate(reader):
            if i >= 3:
                break
            print(f"  Row {i+1}: {dict(row)}")
