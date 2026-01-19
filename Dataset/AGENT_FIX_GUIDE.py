"""
SOLUTION: Improve Agent Understanding in GUI

Problem: Agent keeps asking clarification questions even when user already provided:
- 7 specific metrics
- Confirmed "Software Health Dataset"  
- Said "1000 data" meaning 1000 rows

Root Cause: LLM doesn't have clear logic to detect when to STOP asking and START generating

এখানে 2টা solution:
"""

# ═════════════════════════════════════════════════════════════════════════════
# SOLUTION 1: Add Smart Stopping Logic in Agent Processing
# ═════════════════════════════════════════════════════════════════════════════

def check_if_ready_to_proceed(conversation_history, llm_provider):
    """
    Before sending to LLM, check if we already have enough info
    """
    import re
    
    # Extract all user messages
    user_texts = []
    for msg in conversation_history:
        if msg.get('role') == 'user':
            user_texts.append(msg.get('content', '').lower())
    
    combined = ' '.join(user_texts)
    
    # Pattern detection
    has_metrics = bool(re.search(r'(technical_debt|code_smells|bug_density|num_bugs|has_defect|vulnerabilities|cyclomatic_complexity)', combined))
    has_confirmation = bool(re.search(r'(yes|approve|correct|software health)', combined))
    has_row_count = bool(re.search(r'\b(\d{2,5})\s*(data|rows|files)?\b', combined))
    
    # Decision tree
    if has_metrics and has_confirmation and has_row_count:
        return True, {
            'action': 'generate',
            'reason': 'User provided metrics + confirmation + row count'
        }
    
    return False, {'action': 'clarify'}


# ═════════════════════════════════════════════════════════════════════════════
# SOLUTION 2: Better Prompt Engineering for LLM
# ═════════════════════════════════════════════════════════════════════════════

def create_smart_agent_prompt(user_message, conversation_history, metrics_catalog):
    """
    Create a better prompt that prevents excessive questioning
    """
    
    # Extract what we already know
    known_info = extract_known_info(conversation_history)
    
    prompt = f"""You are a dataset generation agent. Your goal is to understand requirements QUICKLY and generate datasets.

IMPORTANT RULES:
1. If user already specified metrics (list of metric names), DON'T ask which metrics again
2. If user says a number like "1000" or "1000 data", that means ROW COUNT, not a metric threshold
3. If user confirmed dataset type (e.g., "Software Health Dataset"), DON'T ask again
4. MAXIMUM 2 clarification questions, then START GENERATING

WHAT WE ALREADY KNOW:
{format_known_info(known_info)}

USER'S LATEST MESSAGE:
{user_message}

DECISION:
- If we have: dataset type + metrics + row count → Reply "READY TO GENERATE"
- If missing critical info → Ask ONE specific question
- NEVER ask about things already answered

Your response:"""
    
    return prompt


def extract_known_info(conversation_history):
    """Extract what information we already have"""
    import re
    
    info = {
        'dataset_type': None,
        'metrics': [],
        'row_count': None,
        'confirmations': []
    }
    
    for msg in conversation_history:
        if msg.get('role') == 'user':
            text = msg.get('content', '').lower()
            
            # Dataset type
            if 'software health' in text or 'health dataset' in text:
                info['dataset_type'] = 'software_health'
            
            # Metrics (look for snake_case metric names)
            metric_pattern = r'\b([a-z_]+_[a-z_]+)\b'
            found_metrics = re.findall(metric_pattern, text)
            info['metrics'].extend(found_metrics)
            
            # Row count
            number_match = re.search(r'\b(\d{2,5})\s*(data|rows|files|samples)?\b', text)
            if number_match:
                info['row_count'] = int(number_match.group(1))
            
            # Confirmations
            if any(word in text for word in ['yes', 'approve', 'correct', 'ok']):
                info['confirmations'].append(text)
    
    # Deduplicate metrics
    info['metrics'] = list(set(info['metrics']))
    
    return info


def format_known_info(info):
    """Format known information for prompt"""
    lines = []
    
    if info['dataset_type']:
        lines.append(f"✅ Dataset Type: {info['dataset_type']}")
    else:
        lines.append("❓ Dataset Type: Unknown")
    
    if info['metrics']:
        lines.append(f"✅ Metrics ({len(info['metrics'])}): {', '.join(info['metrics'][:5])}")
    else:
        lines.append("❓ Metrics: Not specified")
    
    if info['row_count']:
        lines.append(f"✅ Row Count: {info['row_count']}")
    else:
        lines.append("❓ Row Count: Not specified")
    
    return '\n'.join(lines)


# ═════════════════════════════════════════════════════════════════════════════
# SOLUTION 3: Add a "Smart Bypass" - Skip LLM if Info is Complete
# ═════════════════════════════════════════════════════════════════════════════

def process_user_message_smartly(user_message, conversation_history, llm_provider):
    """
    Process user message with smart decision making
    """
    
    # Step 1: Check if we can proceed without asking LLM
    ready, decision_info = check_if_ready_to_proceed(conversation_history, llm_provider)
    
    if ready:
        # BYPASS LLM - We have enough info!
        return {
            'status': 'ready_to_generate',
            'action': 'START GENERATION',
            'config': extract_generation_config(conversation_history),
            'message': '✅ All information collected. Starting dataset generation...'
        }
    
    # Step 2: Use LLM with better prompt
    prompt = create_smart_agent_prompt(user_message, conversation_history, None)
    llm_response = llm_provider.generate_content(prompt)
    
    # Step 3: Parse LLM response
    if 'READY TO GENERATE' in llm_response:
        return {
            'status': 'ready_to_generate',
            'action': 'START GENERATION'
        }
    else:
        return {
            'status': 'needs_clarification',
            'question': llm_response
        }


def extract_generation_config(conversation_history):
    """Extract final configuration for generation"""
    info = extract_known_info(conversation_history)
    
    return {
        'dataset_type': info['dataset_type'] or 'custom',
        'metrics': info['metrics'],
        'row_count': info['row_count'] or 100,
        'output_format': 'csv',
        'repository': 'kafka',  # From current session
        'ready': True
    }


# ═════════════════════════════════════════════════════════════════════════════
# HOW TO INTEGRATE INTO YOUR GUI
# ═════════════════════════════════════════════════════════════════════════════

"""
In gui/main.py, find where you process agent messages.
Replace the current logic with:

def _handle_user_agent_input(self, user_message):
    '''Process user message in agent panel'''
    
    # Add to conversation
    self.conversation_history.append({
        'role': 'user',
        'content': user_message
    })
    
    # NEW: Smart processing
    result = process_user_message_smartly(
        user_message, 
        self.conversation_history,
        self.multi_provider_llm
    )
    
    if result['status'] == 'ready_to_generate':
        # Stop asking questions, start generating!
        self.add_agent_message(MessageType.SUCCESS, result['message'])
        self._start_dataset_generation(result['config'])
    else:
        # Ask clarification
        self.add_agent_message(MessageType.QUESTION, result['question'])
"""

print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                         SOLUTION SUMMARY                                  ║
╚═══════════════════════════════════════════════════════════════════════════╝

Problem: Agent keeps asking "What kind of data?" even after user provided all info

Solution: Add 3-layer smart decision making:

1. FIRST CHECK: Do we have enough info already?
   - If YES → Skip LLM, start generating
   - If NO → Ask LLM for help

2. BETTER PROMPTS: Tell LLM what we already know
   - "User already said 1000 data = 1000 rows"
   - "User already listed 7 metrics"
   - "User confirmed Software Health Dataset"

3. STOP RULE: Maximum 2 clarifications, then generate anyway
   - Prevents infinite question loops
   - Better user experience

এই code টা আপনার gui/main.py তে integrate করলে problem solve হবে।
""")
