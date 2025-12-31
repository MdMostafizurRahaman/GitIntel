"""Deep analysis of agentic system"""
from enhanced_agentic_system import EnhancedAgenticSystem, AgentMode

print('=== ANALYZING AGENTIC SYSTEM STATE MACHINE ===\n')

# Initialize
system = EnhancedAgenticSystem(mode=AgentMode.ASK)
system.set_repository('d:\\GitIntel\\repo')

# Test 1: Start conversation
print('[TEST 1] Start conversation')
result = system.start_conversation('Create dataset with LOC and CBO')
print(f'Status: {result.get("status")}')
print(f'Keys: {list(result.keys())}')
print()

# Test 2: Continue with yes
print('[TEST 2] Continue with yes (should generate sample)')
result = system.continue_conversation('yes')
print(f'Status: {result.get("status")}')
print(f'Keys: {list(result.keys())}')
print(f'sample_generated: {system.sample_generated}')
print(f'user_accepted: {system.user_accepted}')
print()

# Test 3: Try to generate full without acceptance
print('[TEST 3] Try full generation without acceptance')
result = system.generate_full_dataset()
print(f'Error: {result.get("error")}')
print(f'Message: {result.get("message")}')
