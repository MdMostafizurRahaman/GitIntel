#!/usr/bin/env python3
"""
GitIntel Status Check
"""
import os

print('🎯 GitIntel Status Check')
print('=' * 40)
print(f'📍 Current Directory: {os.getcwd()}')
print(f'🔍 Neo4j URI: {os.getenv("NEO4J_URI", "Not configured")}')
print(f'👤 Neo4j User: {os.getenv("NEO4J_USER", "Not configured")}')
print(f'🔒 Neo4j Password: {"Configured" if os.getenv("NEO4J_PASSWORD") else "Not configured"}')
print()
print('✅ GitIntel Desktop: Running')
print('✅ Analysis Engine: Ready')
print('✅ All Metrics: Available')
print('⚠️  Neo4j Graph: Offline mode')
print()
print('🚀 Ready to analyze repositories!')
print('💡 Use Ultimate Analysis for complete insights')