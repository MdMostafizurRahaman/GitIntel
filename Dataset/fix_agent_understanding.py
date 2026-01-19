"""
Quick Fix for Conversational Agent - Better Understanding
Add this logic to your agent's message processing
"""

def should_proceed_with_generation(conversation_history):
    """
    Check if we have enough information to proceed WITHOUT asking more questions
    
    Returns: (should_proceed: bool, config: dict)
    """
    
    # Extract all user messages
    user_messages = []
    for msg in conversation_history:
        if msg.get('role') == 'user':
            user_messages.append(msg.get('content', '').lower())
    
    combined_input = ' '.join(user_messages)
    
    # Check 1: Do we have metrics specified?
    metrics_found = []
    known_metrics = [
        'technical_debt', 'code_smells', 'bug_density', 'num_bugs', 
        'has_defect', 'vulnerabilities', 'cyclomatic_complexity',
        'maintainability_index', 'test_coverage', 'duplication',
        'loc', 'wmc', 'dit', 'noc', 'cbo', 'rfc', 'lcom'
    ]
    
    for metric in known_metrics:
        if metric.replace('_', ' ') in combined_input or metric in combined_input:
            metrics_found.append(metric)
    
    # Check 2: Do we have a row count?
    row_count = None
    import re
    
    # Look for numbers that represent row count
    for msg in user_messages:
        # Pattern: "1000", "1000 data", "1000 rows", "1000 files"
        number_match = re.search(r'\b(\d+)\s*(data|rows|files|samples|records)?\b', msg)
        if number_match:
            potential_count = int(number_match.group(1))
            # If number is reasonable for dataset size (10-10000)
            if 10 <= potential_count <= 10000:
                row_count = potential_count
                break
    
    # Check 3: Has user confirmed dataset type?
    dataset_confirmed = False
    confirmations = ['yes', 'approve', 'correct', 'software health', 'health dataset']
    for conf in confirmations:
        if conf in combined_input:
            dataset_confirmed = True
            break
    
    # Decision: Should we proceed?
    if len(metrics_found) >= 3 and dataset_confirmed:
        # We have enough info!
        return True, {
            'metrics': metrics_found,
            'row_count': row_count or 100,  # Default to 100 if not specified
            'dataset_type': 'software_health',
            'ready': True
        }
    
    return False, {}


# Example usage in your agent:
def process_user_input(user_message, conversation_history):
    """
    Modified agent message processing
    """
    
    # Add message to history
    conversation_history.append({
        'role': 'user',
        'content': user_message
    })
    
    # Check if we should proceed
    should_proceed, config = should_proceed_with_generation(conversation_history)
    
    if should_proceed:
        # Stop asking questions, start generating!
        print(f"✅ Ready to generate!")
        print(f"   Metrics: {', '.join(config['metrics'])}")
        print(f"   Rows: {config['row_count']}")
        print(f"   Dataset: {config['dataset_type']}")
        
        # Call your generation function here
        # generate_dataset(config)
        
        return {
            'status': 'generating',
            'config': config,
            'message': 'Starting dataset generation...'
        }
    else:
        # Continue asking questions
        return {
            'status': 'needs_clarification',
            'message': 'I need more information...'
        }


# Test the logic
if __name__ == '__main__':
    # Simulate your conversation
    test_history = [
        {'role': 'user', 'content': 'make a health dataset'},
        {'role': 'assistant', 'content': 'Software or Physical Health?'},
        {'role': 'user', 'content': 'Software Health Dataset'},
        {'role': 'assistant', 'content': 'Which metrics?'},
        {'role': 'user', 'content': 'technical_debt, code_smells, bug_density, num_bugs, has_defect, vulnerabilities, cyclomatic_complexity'},
        {'role': 'assistant', 'content': 'How many files?'},
        {'role': 'user', 'content': '1000'},
        {'role': 'assistant', 'content': 'What kind of data?'},  # This shouldn't happen!
        {'role': 'user', 'content': '1000 data'}  # User is frustrated
    ]
    
    should_proceed, config = should_proceed_with_generation(test_history)
    
    print("\n" + "="*70)
    print("AGENT DECISION TEST")
    print("="*70)
    print(f"\nShould Proceed: {should_proceed}")
    if should_proceed:
        print(f"\nConfig:")
        print(f"  Metrics: {config['metrics']}")
        print(f"  Row Count: {config['row_count']}")
        print(f"  Dataset Type: {config['dataset_type']}")
        print(f"\n✅ Agent should START GENERATING now, not ask more questions!")
    else:
        print("\n❌ Agent needs more information")
