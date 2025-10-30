from llm_git_analyzer import LLMGitAnalyzer

analyzer = LLMGitAnalyzer()
analyzer.set_repository('d:/GitIntel/kafka')

commands = [
    'Show me lines of code',
    'Package wise complexity dekhao',
    'Show code changes over 1000 lines',
    'Release wise changes dekhao',
    'LOC time ratio dekhao'
]

for cmd in commands:
    print(f'\nCommand: {cmd}')
    try:
        result = analyzer.process_natural_language_command(cmd)
        print(f'Analysis Type: {result["analysis_type"]}')
        print(f'Description: {result["description"]}')
    except Exception as e:
        print(f'Error: {e}')