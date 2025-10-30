#!/usr/bin/env python3
"""
RepoChat Query Generator - Natural Language to Cypher Query Translation
"""

import os
import json
import re
from typing import Dict, List, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import Gemini AI, fallback to simple pattern matching
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Google Gemini not available, using pattern-based query generation")

class CypherQueryGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_gemini()
        
        # Common query patterns for fallback
        self.query_patterns = {
            'top_contributors': {
                'patterns': ['top contributors', 'most active', 'who committed', 'active developers', 'most commits', 'commits more', 'who commits more'],
                'cypher': 'MATCH (c:Contributor) RETURN c.name, c.email, c.commits ORDER BY c.commits DESC LIMIT 20'
            },
            'list_contributors': {
                'patterns': ['list of users', 'list users', 'show users', 'list contributors', 'show contributors'],
                'cypher': 'MATCH (c:Contributor) RETURN c.name, c.email, c.commits ORDER BY c.commits DESC LIMIT 20'
            },
            'lowest_contributors': {
                'patterns': ['lowest contributors', 'least active', 'fewest commits', 'minimum contributors'],
                'cypher': 'MATCH (c:Contributor) RETURN c.name, c.email, c.commits ORDER BY c.commits ASC LIMIT 10'
            },
            'specific_commit_count': {
                'patterns': ['exactly', 'exact', 'precisely', 'specifically'],
                'cypher': 'MATCH (c:Contributor) WHERE c.commits = {count} RETURN c.name, c.email, c.commits ORDER BY c.name'
            },
            'file_changes': {
                'patterns': ['file changes', 'modified files', 'changed files', 'file modifications'],
                'cypher': 'MATCH (c:Commit)-[r:MODIFIED]->(f:File) RETURN f.name, count(r) as changes ORDER BY changes DESC LIMIT 10'
            },
            'bug_fixes': {
                'patterns': ['bug fix', 'fixes', 'bug commits', 'fixed bugs'],
                'cypher': 'MATCH (c:Commit) WHERE c.is_bug_fix = true RETURN c.hash, c.message, c.author_name, c.date ORDER BY c.date DESC LIMIT 10'
            },
            'complex_files': {
                'patterns': ['complex files', 'complexity', 'complicated', 'highest complexity'],
                'cypher': 'MATCH (f:File) WHERE f.lines_of_code > 100 RETURN f.name, f.lines_of_code, f.language ORDER BY f.lines_of_code DESC LIMIT 10'
            },
            'recent_commits': {
                'patterns': ['recent commits', 'latest commits', 'last commits', 'new commits'],
                'cypher': 'MATCH (c:Commit) RETURN c.hash, c.message, c.author_name, c.date ORDER BY c.date DESC LIMIT 10'
            },
            'repository_stats': {
                'patterns': ['repository stats', 'repo statistics', 'project info', 'overview'],
                'cypher': 'MATCH (r:Repository) RETURN r.name, r.language, r.total_commits, r.total_branches, r.total_tags'
            },
            'large_files': {
                'patterns': ['large files', 'big files', 'largest files', 'file size'],
                'cypher': 'MATCH (f:File) RETURN f.name, f.size, f.lines_of_code ORDER BY f.size DESC LIMIT 10'
            },
            'contributor_files': {
                'patterns': ['contributor files', 'who modified', 'file contributors', 'authors'],
                'cypher': 'MATCH (contributor:Contributor)-[:AUTHORED]->(commit:Commit)-[:MODIFIED]->(file:File) RETURN contributor.name, file.name, count(commit) as modifications ORDER BY modifications DESC LIMIT 20'
            },
            'package_analysis': {
                'patterns': ['package', 'package churn', 'package changes', 'namespace'],
                'cypher': 'MATCH (f:File) WHERE f.language = "Java" RETURN substring(f.path, 0, apoc.text.indexOf(f.path, "/", 3)) as package, count(f) as files, sum(f.lines_of_code) as total_loc ORDER BY total_loc DESC LIMIT 10'
            },
            'monthly_commits': {
                'patterns': ['monthly commits', 'commits per month', 'monthly activity', 'commit timeline'],
                'cypher': 'MATCH (c:Commit) RETURN substring(c.date, 0, 7) as month, count(c) as commits ORDER BY month DESC LIMIT 12'
            },
            'all_contributors': {
                'patterns': ['all contributors', 'list contributors', 'contributors list', 'show contributors'],
                'cypher': 'MATCH (c:Contributor) RETURN c.name, c.email, c.commits ORDER BY c.commits DESC'
            },
            'commit_range': {
                'patterns': ['commits between', 'commit range', 'contributors with'],
                'cypher': 'MATCH (c:Contributor) WHERE c.commits >= {min} AND c.commits <= {max} RETURN c.name, c.email, c.commits ORDER BY c.commits DESC'
            }
        }
    
    def setup_gemini(self):
        """Setup Google Gemini AI for query generation"""
        # Temporarily disable LLM to avoid quota issues - using pattern-based approach
        self.model = None
        return
        
        if not GEMINI_AVAILABLE:
            self.model = None
            return
            
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                print("⚠️ GEMINI_API_KEY not found, using pattern-based query generation")
                self.model = None
                return
            
            genai.configure(api_key=api_key)
            
            # Try different model names
            model_names = ['gemini-pro-latest', 'gemini-1.5-flash-latest', 'gemini-1.5-pro-latest']
            self.model = None
            
            for model_name in model_names:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    print(f"✅ Gemini model loaded: {model_name}")
                    break
                except Exception as e:
                    continue
            
            if not self.model:
                print("⚠️ No Gemini model available, using pattern-based query generation")
                
        except Exception as e:
            self.logger.warning(f"Failed to setup Gemini: {e}")
            self.model = None
    
    def generate_query(self, question: str) -> Optional[str]:
        """Generate Cypher query from natural language question"""
        try:
            if self.model:
                return self._generate_query_with_llm(question)
            else:
                return self._generate_query_with_patterns(question)
                
        except Exception as e:
            self.logger.error(f"Query generation failed: {e}")
            return self._generate_query_with_patterns(question)
    
    def _generate_query_with_llm(self, question: str) -> Optional[str]:
        """Generate Cypher query using LLM"""
        schema_info = self._get_schema_description()
        
        prompt = f"""
You are a Cypher query generator for a software repository knowledge graph.

Schema Information:
{schema_info}

The knowledge graph contains information about:
- Repository: project information
- Commits: code changes, author, date, bug fixes
- Contributors: developers, their contributions
- Files: source code files, size, language, complexity
- Branches: git branches
- Tags: git tags

Relationships:
- (Contributor)-[:AUTHORED]->(Commit)
- (Commit)-[:MODIFIED]->(File)

Question: {question}

Generate a Cypher query to answer this question. Return ONLY the Cypher query, no explanation.

Examples:
Question: "Who are the top contributors?"
Query: MATCH (c:Contributor) RETURN c.name, c.email, c.commits ORDER BY c.commits DESC LIMIT 10

Question: "Which files change most frequently?"
Query: MATCH (c:Commit)-[r:MODIFIED]->(f:File) RETURN f.name, count(r) as changes ORDER BY changes DESC LIMIT 10

Question: "Show me bug fixing commits"
Query: MATCH (c:Commit) WHERE c.is_bug_fix = true RETURN c.hash, c.message, c.author_name, c.date ORDER BY c.date DESC LIMIT 10

Now generate the query for: {question}
"""

        try:
            response = self.model.generate_content(prompt)
            cypher_query = self._extract_cypher_from_response(response.text)
            return cypher_query
            
        except Exception as e:
            self.logger.error(f"LLM query generation failed: {e}")
            return None
    
    def _generate_query_with_patterns(self, question: str) -> Optional[str]:
        """Generate Cypher query using pattern matching"""
        import re
        from datetime import datetime
        
        question_lower = question.lower()
        
        # Check for Bengali keywords and translate them
        question_lower = self._translate_bengali_keywords(question_lower)
        
        # Extract numbers from question for various purposes
        numbers = re.findall(r'\d+', question_lower)
        
        # Handle date-based queries (today, recent, etc.)
        if any(word in question_lower for word in ['today', 'আজ', 'আজকে']):
            today_date = datetime.now().strftime('%Y-%m-%d')
            if any(word in question_lower for word in ['change', 'commit', 'code', 'modify', 'update']):
                # Query for commits made today
                return f"MATCH (contributor:Contributor)-[:AUTHORED]->(commit:Commit) WHERE commit.date STARTS WITH '{today_date}' RETURN DISTINCT contributor.name as name, contributor.email as email, count(commit) as today_commits ORDER BY today_commits DESC"
            elif any(word in question_lower for word in ['who', 'contributor', 'author', 'developer']):
                return f"MATCH (contributor:Contributor)-[:AUTHORED]->(commit:Commit) WHERE commit.date STARTS WITH '{today_date}' RETURN DISTINCT contributor.name as name, contributor.email as email, count(commit) as today_commits ORDER BY today_commits DESC"
        
        # Handle recent queries (last few days)
        elif any(word in question_lower for word in ['recent', 'recently', 'latest', 'last']):
            if any(word in question_lower for word in ['change', 'commit', 'code', 'modify', 'update']):
                # Show recent commits (last 7 days)
                return "MATCH (commit:Commit) WHERE commit.date >= date() - duration('P7D') RETURN commit.hash, commit.message, commit.author_name, commit.date ORDER BY commit.date DESC LIMIT 20"
            elif any(word in question_lower for word in ['who', 'contributor', 'author', 'developer']):
                return "MATCH (c:Contributor) WHERE c.last_commit IS NOT NULL RETURN c.name, c.email, c.commits, c.last_commit ORDER BY c.last_commit DESC LIMIT 10"
        
        # Handle this week/month queries - fallback to most recent contributors
        if any(phrase in question_lower for phrase in ['this week', 'এই সপ্তাহে', 'weekly']):
            return "MATCH (c:Contributor) WHERE c.last_commit IS NOT NULL RETURN c.name, c.email, c.commits, c.last_commit ORDER BY c.last_commit DESC LIMIT 20"
        
        if any(phrase in question_lower for phrase in ['this month', 'এই মাসে', 'monthly']):
            return "MATCH (c:Contributor) WHERE c.last_commit IS NOT NULL RETURN c.name, c.email, c.commits, c.last_commit ORDER BY c.last_commit DESC LIMIT 20"
        
        # Handle list queries with specific count
        if ('list' in question_lower or 'show' in question_lower) and numbers:
            count = int(numbers[0])
            # Check for any contributor-related words
            if any(word in question_lower for word in ['user', 'contributor', 'developer', 'author', 'contributer']):
                if any(word in question_lower for word in ['more', 'most', 'top', 'high']):
                    return f"MATCH (c:Contributor) RETURN c.name, c.email, c.commits ORDER BY c.commits DESC LIMIT {count}"
                elif any(word in question_lower for word in ['less', 'least', 'low', 'bottom']):
                    return f"MATCH (c:Contributor) RETURN c.name, c.email, c.commits ORDER BY c.commits ASC LIMIT {count}"
                else:
                    # Default to showing contributors in descending order by commits
                    return f"MATCH (c:Contributor) RETURN c.name, c.email, c.commits ORDER BY c.commits DESC LIMIT {count}"
        
        # Handle specific commit count queries
        if 'exactly' in question_lower or 'exact' in question_lower:
            if numbers:
                commit_count = numbers[0]
                return f"MATCH (c:Contributor) WHERE c.commits = {commit_count} RETURN c.name, c.email, c.commits ORDER BY c.name"
        
        # Handle range queries
        if 'more than' in question_lower or 'greater than' in question_lower:
            if numbers:
                commit_count = numbers[0]
                return f"MATCH (c:Contributor) WHERE c.commits > {commit_count} RETURN c.name, c.email, c.commits ORDER BY c.commits DESC LIMIT 20"
        
        if 'less than' in question_lower or 'fewer than' in question_lower:
            if numbers:
                commit_count = numbers[0]
                return f"MATCH (c:Contributor) WHERE c.commits < {commit_count} RETURN c.name, c.email, c.commits ORDER BY c.commits ASC LIMIT 20"
        
        # Handle specific contributor queries - more flexible patterns
        if any(phrase in question_lower for phrase in ['commits from', 'number of commit', 'commit from', 'commits by']):
            # Extract contributor name from question
            patterns = ['commits from', 'number of commit from', 'commit from', 'commits by']
            for pattern in patterns:
                if pattern in question_lower:
                    name_part = question_lower.split(pattern)[-1].strip().rstrip('?').strip()
                    if name_part:
                        return f"MATCH (c:Contributor) WHERE toLower(c.name) CONTAINS '{name_part}' OR toLower(c.email) CONTAINS '{name_part}' RETURN c.name, c.email, c.commits"
        
        # Handle lowest/fewest contributors
        if any(word in question_lower for word in ['lowest', 'fewest', 'minimum', 'least']):
            if 'contributor' in question_lower:
                return 'MATCH (c:Contributor) RETURN c.name, c.email, c.commits ORDER BY c.commits ASC LIMIT 10'
        
        # Find matching pattern
        for query_type, config in self.query_patterns.items():
            for pattern in config['patterns']:
                if pattern in question_lower:
                    print(f"🔍 Matched pattern: {pattern} -> {query_type}")
                    return config['cypher']
        
        # Check for specific patterns that might not be in our predefined list
        if any(word in question_lower for word in ['who', 'contributor', 'contributer', 'developer', 'author']):
            print("🔍 Generic contributor query")
            # Check if they want more contributors
            if numbers and int(numbers[0]) > 10:
                limit = int(numbers[0])
                return f'MATCH (c:Contributor) RETURN c.name, c.email, c.commits ORDER BY c.commits DESC LIMIT {limit}'
            else:
                return 'MATCH (c:Contributor) RETURN c.name, c.email, c.commits ORDER BY c.commits DESC LIMIT 20'
        
        # Default fallback query
        print("🔍 No specific pattern matched, using default query")
        return 'MATCH (c:Contributor) RETURN c.name, c.email, c.commits ORDER BY c.commits DESC LIMIT 20'
    
    def _translate_bengali_keywords(self, question: str) -> str:
        """Translate Bengali keywords to English"""
        translations = {
            'কে': 'who',
            'কোন': 'which',
            'কত': 'how many',
            'সবচেয়ে বেশি': 'most',
            'বেশি': 'more',
            'কম': 'less',
            'কমিট': 'commit',
            'ফাইল': 'file',
            'ডেভেলপার': 'developer',
            'প্রোগ্রামার': 'programmer',
            'চেঞ্জ': 'change',
            'বাগ': 'bug',
            'ইস্যু': 'issue',
            'ফিক্স': 'fix',
            'কোড': 'code',
            'আজ': 'today',
            'আজকে': 'today',
            'সাম্প্রতিক': 'recent',
            'নতুন': 'new',
            'হালনাগাদ': 'update',
            'পরিবর্তন': 'change',
            'লাইন': 'line',
            'প্যাকেজ': 'package',
            'ক্লাস': 'class',
            'মেথড': 'method',
            'ফাংশন': 'function'
        }
        
        for bengali, english in translations.items():
            question = question.replace(bengali, english)
        
        return question
    
    def _extract_cypher_from_response(self, response_text: str) -> Optional[str]:
        """Extract Cypher query from LLM response"""
        # Remove code block markers
        response_text = re.sub(r'```cypher\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        
        # Find MATCH statement
        match = re.search(r'MATCH.*?(?:RETURN.*?)(?=\n|$)', response_text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(0).strip()
        
        # If no MATCH found, look for any valid Cypher patterns
        cypher_patterns = [
            r'CREATE.*?(?=\n|$)',
            r'MERGE.*?(?=\n|$)',
            r'DELETE.*?(?=\n|$)',
            r'SET.*?(?=\n|$)'
        ]
        
        for pattern in cypher_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(0).strip()
        
        # Last resort: return the first line that looks like Cypher
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.upper() for keyword in ['MATCH', 'CREATE', 'RETURN', 'WHERE']):
                return line
        
        return None
    
    def generate_response(self, question: str, query_results: List[Dict[str, Any]]) -> str:
        """Generate natural language response from query results"""
        try:
            if not query_results:
                # Check if this was a date-specific query
                question_lower = question.lower()
                if any(word in question_lower for word in ['today', 'আজ', 'আজকে']):
                    from datetime import datetime
                    today_date = datetime.now().strftime('%B %d, %Y')
                    return f"📅 **No code changes found for today ({today_date})**\n\n❌ No contributors made commits today in this repository."
                return "❌ No results found for your question."
            
            if self.model:
                return self._generate_response_with_llm(question, query_results)
            else:
                return self._generate_response_with_templates(question, query_results)
                
        except Exception as e:
            self.logger.error(f"Response generation failed: {e}")
            return self._format_raw_results(query_results)
    
    def _generate_response_with_llm(self, question: str, query_results: List[Dict[str, Any]]) -> str:
        """Generate response using LLM"""
        prompt = f"""
Based on the following query results, provide a clear and informative answer to the user's question.

Question: {question}

Query Results:
{json.dumps(query_results, indent=2, default=str)}

Provide a natural language response that:
1. Directly answers the question
2. Highlights key findings
3. Uses emojis for better readability
4. Formats data in a user-friendly way

Keep the response concise but informative.
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            self.logger.error(f"LLM response generation failed: {e}")
            return self._generate_response_with_templates(question, query_results)
    
    def _generate_response_with_templates(self, question: str, query_results: List[Dict[str, Any]]) -> str:
        """Generate response using templates"""
        question_lower = question.lower()
        
        # Check if this is a contributor search query
        if ('contributor' in question_lower or 'developer' in question_lower or 'author' in question_lower or 
            'who' in question_lower or 'commits from' in question_lower or 'number of commits' in question_lower or
            'today' in question_lower or 'recent' in question_lower):
            return self._format_contributors_response(query_results, question_lower)
        
        elif any(word in question_lower for word in ['file', 'changes', 'modified']):
            return self._format_files_response(query_results)
        
        elif any(word in question_lower for word in ['commit', 'recent', 'latest']) and 'from' not in question_lower:
            return self._format_commits_response(query_results)
        
        elif any(word in question_lower for word in ['bug', 'fix', 'issue']):
            return self._format_bugfixes_response(query_results)
        
        elif any(word in question_lower for word in ['repository', 'repo', 'project', 'stats']):
            return self._format_repository_response(query_results)
        
        else:
            # Default to contributor format if we have contributor-like data
            if query_results and any(key in query_results[0] for key in ['name', 'email', 'commits', 'c.name', 'c.email', 'c.commits']):
                return self._format_contributors_response(query_results, question_lower)
            else:
                return self._format_raw_results(query_results)
    
    def _format_contributors_response(self, results: List[Dict[str, Any]], question_context: str = "") -> str:
        """Format contributors query results"""
        if not results:
            # Check if this was a today-specific query
            if any(word in question_context for word in ['today', 'আজ', 'আজকে']):
                return "📅 **No code changes found for today (October 30, 2025)**\n\n❌ No contributors made commits today in this repository."
            return "❌ No contributors found."
        
        # Customize response based on question context
        if any(word in question_context for word in ['today', 'আজ', 'আজকে']):
            response = "� **Contributors who changed code today (October 30, 2025):**\n\n"
        elif any(word in question_context for word in ['recent', 'recently', 'latest', 'last']):
            response = "🔍 **Recent Contributors:**\n\n"
        else:
            response = "👥 **Contributors:**\n\n"
        
        # Handle both regular contributor queries and search results
        if len(results) == 1 and ('commits' in results[0] or 'today_commits' in results[0]):
            # Single contributor result (likely a search)
            contributor = results[0]
            name = contributor.get('name', contributor.get('c.name', 'Unknown'))
            commits = contributor.get('commits', contributor.get('c.commits', contributor.get('today_commits', 0)))
            email = contributor.get('email', contributor.get('c.email', ''))
            last_commit = contributor.get('last_commit', contributor.get('c.last_commit', ''))
            today_commits = contributor.get('today_commits', 0)
            
            response = f"👤 **Contributor: {name}**\n\n"
            response += f"📧 **Email:** {email}\n"
            
            if today_commits > 0:
                response += f"📊 **Commits Today:** {today_commits}\n"
            else:
                response += f"📊 **Total Commits:** {commits}\n"
                
            if last_commit:
                response += f"🕐 **Last Activity:** {last_commit}\n"
            
            if commits == 0 and today_commits == 0:
                response += "\n❌ This contributor has no commits in the analyzed repository."
            
            return response
        
        # Multiple contributors (top contributors list)
        # Use all results, not just first 10
        for i, contributor in enumerate(results, 1):
            name = contributor.get('name', contributor.get('c.name', 'Unknown'))
            commits = contributor.get('commits', contributor.get('c.commits', 0))
            today_commits = contributor.get('today_commits', 0)
            email = contributor.get('email', contributor.get('c.email', ''))
            last_commit = contributor.get('last_commit', contributor.get('c.last_commit', ''))
            
            if email:
                response += f"{i}. **{name}** ({email})\n"
            else:
                response += f"{i}. **{name}**\n"
            
            if today_commits > 0:
                response += f"   📊 Commits Today: {today_commits}\n"
            else:
                response += f"   📊 Commits: {commits}\n"
                
            if last_commit:
                response += f"   🕐 Last Activity: {last_commit}\n"
            response += "\n"
        
        return response.strip()
    
    def _format_files_response(self, results: List[Dict[str, Any]]) -> str:
        """Format files query results"""
        if not results:
            return "❌ No files found."
        
        response = "📂 **File Analysis:**\n\n"
        for i, file_data in enumerate(results[:10], 1):
            filename = file_data.get('f.name', file_data.get('name', 'Unknown'))
            changes = file_data.get('changes', 0)
            size = file_data.get('f.size', file_data.get('size', 0))
            loc = file_data.get('f.lines_of_code', file_data.get('lines_of_code', 0))
            
            response += f"{i}. **{filename}**\n"
            if changes > 0:
                response += f"   🔄 Changes: {changes}\n"
            if size > 0:
                response += f"   📏 Size: {size} bytes\n"
            if loc > 0:
                response += f"   📝 Lines: {loc}\n"
            response += "\n"
        
        return response.strip()
    
    def _format_commits_response(self, results: List[Dict[str, Any]]) -> str:
        """Format commits query results"""
        if not results:
            return "❌ No commits found."
        
        response = "📝 **Recent Commits:**\n\n"
        for i, commit in enumerate(results[:10], 1):
            hash_val = commit.get('c.hash', commit.get('hash', 'Unknown'))[:8]
            message = commit.get('c.message', commit.get('message', 'No message'))
            author = commit.get('c.author_name', commit.get('author_name', 'Unknown'))
            date = commit.get('c.date', commit.get('date', 'Unknown'))
            
            response += f"{i}. **{hash_val}** by {author}\n"
            response += f"   💬 {message[:80]}{'...' if len(message) > 80 else ''}\n"
            response += f"   📅 {date[:10]}\n\n"
        
        return response.strip()
    
    def _format_bugfixes_response(self, results: List[Dict[str, Any]]) -> str:
        """Format bug fixes query results"""
        if not results:
            return "❌ No bug fix commits found."
        
        response = "🐛 **Bug Fix Commits:**\n\n"
        for i, commit in enumerate(results[:10], 1):
            hash_val = commit.get('c.hash', commit.get('hash', 'Unknown'))[:8]
            message = commit.get('c.message', commit.get('message', 'No message'))
            author = commit.get('c.author_name', commit.get('author_name', 'Unknown'))
            date = commit.get('c.date', commit.get('date', 'Unknown'))
            
            response += f"{i}. **{hash_val}** by {author}\n"
            response += f"   🔧 {message[:80]}{'...' if len(message) > 80 else ''}\n"
            response += f"   📅 {date[:10]}\n\n"
        
        return response.strip()
    
    def _format_repository_response(self, results: List[Dict[str, Any]]) -> str:
        """Format repository query results"""
        if not results:
            return "❌ No repository information found."
        
        repo = results[0]
        name = repo.get('r.name', repo.get('name', 'Unknown'))
        language = repo.get('r.language', repo.get('language', 'Unknown'))
        commits = repo.get('r.total_commits', repo.get('total_commits', 0))
        branches = repo.get('r.total_branches', repo.get('total_branches', 0))
        tags = repo.get('r.total_tags', repo.get('total_tags', 0))
        
        response = f"📊 **Repository: {name}**\n\n"
        response += f"💻 **Primary Language:** {language}\n"
        response += f"📝 **Total Commits:** {commits}\n"
        response += f"🌿 **Branches:** {branches}\n"
        response += f"🏷️ **Tags:** {tags}\n"
        
        return response
    
    def _format_raw_results(self, results: List[Dict[str, Any]]) -> str:
        """Format raw query results"""
        if not results:
            return "❌ No results found."
        
        response = "📊 **Query Results:**\n\n"
        
        for i, result in enumerate(results[:10], 1):
            response += f"{i}. "
            for key, value in result.items():
                response += f"**{key}:** {value}, "
            response = response.rstrip(", ") + "\n\n"
        
        if len(results) > 10:
            response += f"... and {len(results) - 10} more results"
        
        return response.strip()
    
    def _get_schema_description(self) -> str:
        """Get schema description for LLM prompt"""
        return """
Node Types:
- Repository: name, path, language, total_commits, total_branches, total_tags
- Contributor: name, email, commits, insertions, deletions, first_commit, last_commit
- Commit: hash, message, author_name, author_email, date, insertions, deletions, is_bug_fix, is_merge
- File: path, name, extension, size, language, lines_of_code
- Branch: name, last_commit, last_commit_date, author
- Tag: name, commit, date, message

Relationships:
- (Contributor)-[:AUTHORED]->(Commit)
- (Commit)-[:MODIFIED {change_type, added_lines, deleted_lines}]->(File)
"""