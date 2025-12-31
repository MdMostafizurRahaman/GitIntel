"""
Enhanced Agentic Workflow Methods
Add these methods to EnhancedAgenticSystem class
"""

def generate_sample(self, num_rows: int = 10) -> Dict[str, Any]:
    """
    Generate SAMPLE dataset (5-10 rows) for user review
    
    Args:
        num_rows: Number of sample rows (default 10)
        
    Returns:
        Sample dataset info with preview
    """
    if not self.current_requirement:
        return {'error': 'No dataset requirement set'}
    
    self._add_message(MessageType.SYSTEM, 
        f"📊 Generating {num_rows}-row SAMPLE for review...")
    
    try:
        # Generate limited sample
        original_limit = getattr(self, '_row_limit', None)
        self._row_limit = num_rows
        
        # Extract sample data from repository
        data = self._extract_data_from_repo()
        data = data[:num_rows]  # Limit to sample size
        
        # Apply formulas
        data = self._apply_formulas(data)
        
        # Convert to DataFrame
        self.sample_data = pd.DataFrame(data)
        self.sample_generated = True
        
        # Restore original limit
        if original_limit:
            self._row_limit = original_limit
        
        # Show preview to user
        preview_info = self._format_sample_preview(self.sample_data)
        self._add_message(MessageType.PREVIEW, 
            f"\n📋 SAMPLE DATASET PREVIEW ({num_rows} rows):\n{preview_info}")
        
        self._add_message(MessageType.QUESTION, 
            "\n💬 Please review the sample. You can:\n"
            "   • 'accepted' / 'looks good' / 'proceed' → Generate full dataset\n"
            "   • Provide feedback for changes → I'll modify and regenerate sample\n"
            "   • 'cancel' / 'stop' → Abort generation")
        
        return {
            'status': 'sample_generated',
            'sample_rows': len(self.sample_data),
            'columns': list(self.sample_data.columns),
            'preview': preview_info,
            'awaiting_feedback': True
        }
        
    except Exception as e:
        self._add_message(MessageType.ERROR, f"❌ Sample generation failed: {e}")
        return {'error': str(e)}

def process_feedback(self, feedback: str) -> Dict[str, Any]:
    """
    Process user feedback on sample dataset
    
    Args:
        feedback: User's feedback text
        
    Returns:
        Action result (accepted, regenerate, error)
    """
    self._add_message(MessageType.USER, feedback)
    self.feedback_iterations += 1
    
    # Check for acceptance keywords
    acceptance_keywords = ['accept', 'looks good', 'proceed', 'ok', 'correct', 'yes', 'perfect', 'right', 'thik ace', 'valo', 'hbe']
    feedback_lower = feedback.lower()
    
    if any(keyword in feedback_lower for keyword in acceptance_keywords):
        self.user_accepted = True
        self._add_message(MessageType.SUCCESS, 
            "✅ Sample ACCEPTED! Proceeding with FULL dataset generation...")
        return {
            'status': 'accepted',
            'action': 'generate_full',
            'feedback_iterations': self.feedback_iterations
        }
    
    # Check for cancellation
    cancel_keywords = ['cancel', 'stop', 'abort', 'no', 'nah', 'band kro']
    if any(keyword in feedback_lower for keyword in cancel_keywords):
        self._add_message(MessageType.INFO, "⚠️ Generation cancelled by user.")
        return {
            'status': 'cancelled',
            'action': 'abort'
        }
    
    # User wants changes - analyze feedback
    self._add_message(MessageType.THINKING, 
        f"🤔 Analyzing feedback (iteration #{self.feedback_iterations})...")
    
    changes = self._analyze_feedback(feedback)
    
    if changes.get('understood', False):
        # Apply changes to requirement
        self._apply_changes_to_requirement(changes)
        
        self._add_message(MessageType.PLAN, 
            f"📝 Changes identified:\n{changes['summary']}\n\n"
            "Regenerating sample with modifications...")
        
        # Regenerate sample
        self.sample_generated = False
        result = self.generate_sample()
        
        return {
            'status': 'modified',
            'action': 'regenerated_sample',
            'changes': changes,
            'feedback_iterations': self.feedback_iterations,
            'new_sample': result
        }
    else:
        # Need clarification on feedback
        self._add_message(MessageType.QUESTION, 
            f"❓ {changes.get('clarification_needed', 'Could you clarify what changes you want?')}")
        return {
            'status': 'needs_clarification',
            'question': changes.get('clarification_needed'),
            'feedback_iterations': self.feedback_iterations
        }

def _format_sample_preview(self, df: pd.DataFrame) -> str:
    """Format sample dataframe for display"""
    if df is None or len(df) == 0:
        return "(Empty dataset)"
    
    # Show first 5 rows with formatted output
    preview = "\n"
    preview += "Columns: " + ", ".join(df.columns) + "\n"
    preview += "-" * 80 + "\n"
    preview += df.head(min(5, len(df))).to_string(index=False) + "\n"
    preview += "-" * 80 + "\n"
    preview += f"Total rows: {len(df)}\n"
    
    # Show basic stats for numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        preview += "\nNumeric Summary:\n"
        for col in numeric_cols:
            preview += f"  {col}: min={df[col].min():.2f}, max={df[col].max():.2f}, mean={df[col].mean():.2f}\n"
    
    return preview

def _analyze_feedback(self, feedback: str) -> Dict[str, Any]:
    """Use LLM to analyze user feedback and identify changes"""
    if not self.model:
        # Simple keyword-based analysis
        return {
            'understood': False,
            'clarification_needed': 'Could you specify exactly what needs to change?'
        }
    
    prompt = f"""You are analyzing user feedback on a sample dataset.

Current Dataset Columns:
{list(self.sample_data.columns) if self.sample_data is not None else []}

Current Requirement:
{self.current_requirement}

User Feedback:
{feedback}

Analyze the feedback and determine:
1. What specific changes are requested?
2. Which columns need modification/addition/removal?
3. What filters or calculations need adjustment?
4. Is the feedback clear enough to make changes?

Respond in JSON:
{{
    "understood": true/false,
    "changes": {{
        "add_columns": ["col1", ...],
        "remove_columns": ["col2", ...],
        "modify_formulas": {{"col_name": "new formula"}},
        "modify_filters": ["filter description"],
        "other_changes": "description"
    }},
    "summary": "brief summary of changes",
    "clarification_needed": "question if unclear" or null
}}"""
    
    try:
        response = self.model.generate_content(prompt)
        result = json.loads(self._extract_json(response.text))
        return result
    except:
        return {
            'understood': False,
            'clarification_needed': 'Could you specify exactly what needs to change?'
        }

def _apply_changes_to_requirement(self, changes: Dict[str, Any]):
    """Apply feedback changes to current requirement"""
    if not self.current_requirement or not changes.get('changes'):
        return
    
    mods = changes['changes']
    
    # Add columns
    if 'add_columns' in mods:
        for col in mods['add_columns']:
            if col not in self.current_requirement.columns:
                self.current_requirement.columns.append(col)
    
    # Remove columns
    if 'remove_columns' in mods:
        for col in mods['remove_columns']:
            if col in self.current_requirement.columns:
                self.current_requirement.columns.remove(col)
    
    # Modify formulas
    if 'modify_formulas' in mods:
        self.current_requirement.formulas.update(mods['modify_formulas'])
    
    # Modify filters
    if 'modify_filters' in mods:
        self.current_requirement.filters.extend(mods['modify_filters'])
