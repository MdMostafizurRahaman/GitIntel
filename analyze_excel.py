#!/usr/bin/env python3
import pandas as pd
import os

def analyze_excel_files():
    # Package churn analysis
    churn_file = 'package_churn_analysis_20251030_134751.xlsx'
    if os.path.exists(churn_file):
        print('📊 PACKAGE CHURN ANALYSIS EXCEL:')
        print('=' * 50)
        df_churn = pd.read_excel(churn_file)
        print(f'Total packages analyzed: {len(df_churn)}')
        print(f'Columns: {list(df_churn.columns)}')
        print()
        print('Sample data (first 3 rows):')
        print(df_churn.head(3).to_string())
        print()

    # LOC analysis
    loc_file = 'loc_analysis_20251030_134955.xlsx'
    if os.path.exists(loc_file):
        print('📈 LOC ANALYSIS EXCEL:')
        print('=' * 50)
        df_loc = pd.read_excel(loc_file)
        print(f'Total packages analyzed: {len(df_loc)}')
        print(f'Columns: {list(df_loc.columns)}')
        print()
        print('Sample data (first 3 rows):')
        print(df_loc.head(3).to_string())
        print()

if __name__ == "__main__":
    analyze_excel_files()