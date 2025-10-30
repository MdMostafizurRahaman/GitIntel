# Run Cumulative Analysis
import os
import sys

# Import our analyze_packages script as module
sys.path.append('.')

# Modify the global MODE variable
print("Running cumulative analysis...")

# Read and modify the script
with open('analyze_packages.py', 'r') as f:
    content = f.read()

# Change MODE to cumulative
modified_content = content.replace("MODE = 'per_commit'", "MODE = 'cumulative'")
modified_content = modified_content.replace("OUTPUT_CSV = 'package_churn_analysis.csv'", "OUTPUT_CSV = 'cumulative_package_analysis.csv'")

# Write to new file
with open('analyze_packages_cumulative.py', 'w') as f:
    f.write(modified_content)

print("Created cumulative analysis script: analyze_packages_cumulative.py")
print("You can run it with: python analyze_packages_cumulative.py")