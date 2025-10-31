#!/usr/bin/env python3
"""
RepoChat Query Generator - Natural Language to Cypher Query Translation
Supports both Bengali and English with Gemini AI and pattern-based fallback
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
            'bug_fixes': {
                'patterns': ['bug fixes', 'bug fix', 'fixes', 'debugging', 'errors fixed'],
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
                'cypher': 'MATCH (r:Repository) RETURN r.name, r.total_commits, r.size_mb, r.active_branch, r.branches, r.tags'
            },
            'file_languages': {
                'patterns': ['file languages', 'programming languages', 'languages used', 'language stats'],
                'cypher': 'MATCH (f:File) WHERE f.language <> "Unknown" RETURN f.language, count(f) as file_count, sum(f.lines_of_code) as total_lines ORDER BY file_count DESC'
            },
            'large_files': {
                'patterns': ['large files', 'biggest files', 'largest files', 'file sizes'],
                'cypher': 'MATCH (f:File) RETURN f.name, f.path, f.size_bytes, f.lines_of_code ORDER BY f.size_bytes DESC LIMIT 10'
            },
            'search_contributor': {
                'patterns': ['find user', 'search user', 'find contributor', 'search contributor'],
                'cypher': 'MATCH (c:Contributor) WHERE toLower(c.name) CONTAINS toLower($search_term) OR toLower(c.email) CONTAINS toLower($search_term) RETURN c.name, c.email, c.commits'
            }
        }
        
        # Bengali keyword translations
        self.bengali_translations = {
            'contributors': ['অবদানকারী', 'কন্ট্রিবিউটর', 'ডেভেলপার'],
            'commits': ['কমিট', 'পরিবর্তন', 'চেঞ্জ'],
            'files': ['ফাইল', 'নথি'],
            'recent': ['সাম্প্রতিক', 'নতুন', 'হালনাগাদ'],
            'top': ['শীর্ষ', 'সেরা', 'বেশি'],
            'most': ['সবচেয়ে', 'অধিক'],
            'show': ['দেখাও', 'দেখান', 'প্রদর্শন'],
            'list': ['তালিকা', 'লিস্ট'],
            'find': ['খুঁজে', 'খোঁজ', 'অনুসন্ধান'],
            'search': ['সার্চ', 'অনুসন্ধান', 'খোঁজ']
        }
    
    def setup_gemini(self):
        """Setup Google Gemini AI for query generation"""
        self.model = None
        
        if GEMINI_AVAILABLE:
            try:
                api_key = os.getenv('GEMINI_API_KEY')
                if api_key:
                    genai.configure(api_key=api_key)
                    self.model = genai.GenerativeModel('gemini-pro')
                    self.logger.info("Gemini AI initialized successfully")
                else:
                    self.logger.warning("GEMINI_API_KEY not found in environment")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini AI: {e}")
    
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

Question: "Show me recent commits"
Query: MATCH (c:Commit) RETURN c.hash, c.message, c.author_name, c.date ORDER BY c.date DESC LIMIT 10

Question: "Find files with most lines of code"
Query: MATCH (f:File) RETURN f.name, f.lines_of_code, f.language ORDER BY f.lines_of_code DESC LIMIT 10

Generate the Cypher query:
"""

        try:
            response = self.model.generate_content(prompt)
            cypher_query = self._extract_cypher_from_response(response.text)
            return cypher_query
        except Exception as e:
            self.logger.error(f"LLM query generation failed: {e}")
            return self._generate_query_with_patterns(question)
    
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
                return f"MATCH (c:Commit) WHERE c.date STARTS WITH '{today_date}' RETURN c.hash, c.message, c.author_name, c.date ORDER BY c.date DESC"
        
        # Handle this week/month queries
        if any(word in question_lower for word in ['this week', 'week', 'এই সপ্তাহে']):
            if any(word in question_lower for word in ['change', 'commit', 'code', 'modify', 'update']):
                # Show recent commits (last 7 days)
                return "MATCH (commit:Commit) WHERE commit.date >= date() - duration('P7D') RETURN commit.hash, commit.message, commit.author_name, commit.date ORDER BY commit.date DESC LIMIT 20"
            elif any(word in question_lower for word in ['who', 'contributor', 'author', 'developer']):
                return "MATCH (c:Contributor) WHERE c.last_commit IS NOT NULL RETURN c.name, c.email, c.commits, c.last_commit ORDER BY c.last_commit DESC LIMIT 10"
        
        # Handle this week/month queries - fallback to most recent contributors
        if any(word in question_lower for word in ['this month', 'month', 'এই মাসে']):
            if any(word in question_lower for word in ['who', 'contributor', 'author', 'developer']):
                return "MATCH (c:Contributor) RETURN c.name, c.email, c.commits, c.last_commit ORDER BY c.last_commit DESC LIMIT 15"
        
        # Handle search queries (find specific contributor)
        if any(word in question_lower for word in ['find', 'search', 'খুঁজে', 'সার্চ']):
            # Extract potential search term
            search_patterns = [
                r'find\s+([a-z]+)',
                r'search\s+([a-z]+)', 
                r'খুঁজে\s+([^\s]+)',
                r'সার্চ\s+([^\s]+)'
            ]
            
            for pattern in search_patterns:
                match = re.search(pattern, question_lower)
                if match:
                    search_term = match.group(1)
                    if len(search_term) > 2:  # Only search for meaningful terms
                        return f"MATCH (c:Contributor) WHERE toLower(c.name) CONTAINS '{search_term}' OR toLower(c.email) CONTAINS '{search_term}' RETURN c.name, c.email, c.commits, c.last_commit"
        
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
        for english, bengali_words in self.bengali_translations.items():
            for bengali in bengali_words:
                if bengali in question:
                    question = question.replace(bengali, english)
        return question
    
    def _extract_cypher_from_response(self, response_text: str) -> Optional[str]:
        """Extract Cypher query from LLM response"""
        # Look for MATCH statements
        import re
        
        # Try to find a complete MATCH query
        match_pattern = r'MATCH\s+.*?(?=\n|$)'
        matches = re.findall(match_pattern, response_text, re.IGNORECASE | re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # Fallback: look for any line that starts with MATCH
        lines = response_text.split('\n')
        for line in lines:
            if line.strip().upper().startswith('MATCH'):
                return line.strip()
        
        return None
    
    def generate_response(self, question: str, query_results: List[Dict[str, Any]]) -> str:
        """Generate natural language response from query results"""
        try:
            if self.model:
                return self._generate_response_with_llm(question, query_results)
            else:
                return self._generate_response_with_templates(question, query_results)
                
        except Exception as e:
            self.logger.error(f"Response generation failed: {e}")
            return self._generate_response_with_templates(question, query_results)
    
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
        if not query_results:
            return "❌ No results found for your query."
        
        question_lower = question.lower()
        
        # Determine response type based on query results structure
        if self._is_contributor_query(query_results):
            return self._format_contributors_response(query_results, question_lower)
        elif self._is_commit_query(query_results):
            return self._format_commits_response(query_results)
        elif self._is_file_query(query_results):
            return self._format_files_response(query_results)
        elif self._is_repository_query(query_results):
            return self._format_repository_response(query_results)
        else:
            return self._format_raw_results(query_results)
    
    def _is_contributor_query(self, results: List[Dict[str, Any]]) -> bool:
        """Check if results are from contributor query"""
        if not results:
            return False
        sample = results[0]
        return any(key in sample for key in ['c.name', 'c.email', 'c.commits', 'name', 'email', 'commits'])
    
    def _is_commit_query(self, results: List[Dict[str, Any]]) -> bool:
        """Check if results are from commit query"""
        if not results:
            return False
        sample = results[0]
        return any(key in sample for key in ['c.hash', 'c.message', 'hash', 'message', 'author_name'])
    
    def _is_file_query(self, results: List[Dict[str, Any]]) -> bool:
        """Check if results are from file query"""
        if not results:
            return False
        sample = results[0]
        return any(key in sample for key in ['f.name', 'f.path', 'f.language', 'lines_of_code'])
    
    def _is_repository_query(self, results: List[Dict[str, Any]]) -> bool:
        """Check if results are from repository query"""
        if not results:
            return False
        sample = results[0]
        return any(key in sample for key in ['r.name', 'r.total_commits', 'total_commits', 'active_branch'])
    
    def _format_contributors_response(self, results: List[Dict[str, Any]], question_context: str = "") -> str:
        """Format contributors query results"""
        if 'recent' in question_context or 'today' in question_context or 'week' in question_context:
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
            
            response += f"**{name}**"
            if email:
                response += f" ({email})"
            response += f"\n📊 **Total Commits:** {commits}"
            if today_commits > 0:
                response += f"\n🔥 **Today's Commits:** {today_commits}"
            if last_commit:
                response += f"\n📅 **Last Commit:** {last_commit}"
            response += "\n"
        else:
            # Multiple contributors
            for i, contributor in enumerate(results[:10], 1):
                name = contributor.get('name', contributor.get('c.name', 'Unknown'))
                commits = contributor.get('commits', contributor.get('c.commits', 0))
                email = contributor.get('email', contributor.get('c.email', ''))
                
                response += f"{i}. **{name}**"
                if email:
                    response += f" ({email})"
                response += f" - {commits} commits\n"
            
            if len(results) > 10:
                response += f"\n... and {len(results) - 10} more contributors"
        
        return response.strip()
    
    def _format_commits_response(self, results: List[Dict[str, Any]]) -> str:
        """Format commits query results"""
        response = "📝 **Commits:**\n\n"
        
        for i, commit in enumerate(results[:10], 1):
            hash_val = commit.get('c.hash', commit.get('hash', 'Unknown'))[:8]
            message = commit.get('c.message', commit.get('message', 'No message'))
            author = commit.get('c.author_name', commit.get('author_name', 'Unknown'))
            date = commit.get('c.date', commit.get('date', 'Unknown'))
            
            response += f"{i}. **{hash_val}** by {author}\n"
            response += f"   📅 {date}\n"
            response += f"   💬 {message[:100]}{'...' if len(message) > 100 else ''}\n\n"
        
        if len(results) > 10:
            response += f"... and {len(results) - 10} more commits"
        
        return response.strip()
    
    def _format_files_response(self, results: List[Dict[str, Any]]) -> str:
        """Format files query results"""
        response = "📁 **Files:**\n\n"
        
        for i, file_info in enumerate(results[:10], 1):
            name = file_info.get('f.name', file_info.get('name', 'Unknown'))
            language = file_info.get('f.language', file_info.get('language', 'Unknown'))
            lines = file_info.get('f.lines_of_code', file_info.get('lines_of_code', 0))
            size = file_info.get('f.size_bytes', file_info.get('size_bytes', 0))
            
            response += f"{i}. **{name}** ({language})\n"
            response += f"   📊 {lines:,} lines"
            if size > 0:
                size_kb = size / 1024
                response += f", {size_kb:.1f} KB"
            response += "\n\n"
        
        if len(results) > 10:
            response += f"... and {len(results) - 10} more files"
        
        return response.strip()
    
    def _format_repository_response(self, results: List[Dict[str, Any]]) -> str:
        """Format repository query results"""
        if not results:
            return "❌ No repository information found."
        
        repo = results[0]
        name = repo.get('r.name', repo.get('name', 'Unknown'))
        total_commits = repo.get('r.total_commits', repo.get('total_commits', 0))
        size_mb = repo.get('r.size_mb', repo.get('size_mb', 0))
        active_branch = repo.get('r.active_branch', repo.get('active_branch', 'Unknown'))
        branches = repo.get('r.branches', repo.get('branches', []))
        tags = repo.get('r.tags', repo.get('tags', []))
        
        response = f"📊 **Repository Overview: {name}**\n\n"
        response += f"🔹 **Total Commits:** {total_commits:,}\n"
        response += f"🔹 **Size:** {size_mb:.2f} MB\n"
        response += f"🔹 **Active Branch:** {active_branch}\n"
        response += f"🔹 **Total Branches:** {len(branches)}\n"
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
        """Get knowledge graph schema description"""
        return """
Repository Knowledge Graph Schema:

Nodes:
- Repository: name, path, active_branch, total_commits, size_mb, branches, tags
- Contributor: name, email, commits, first_commit, last_commit, total_additions, total_deletions  
- Commit: hash, message, author_name, author_email, date, is_bug_fix, additions, deletions
- File: name, path, extension, language, size_bytes, lines_of_code, last_modified

Relationships:
- (Contributor)-[:AUTHORED]->(Commit)
- (Commit)-[:MODIFIED]->(File)
"""

# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize query generator
    query_gen = CypherQueryGenerator()
    
    # Test queries
    test_questions = [
        "Who are the top contributors?",
        "Show me recent commits",
        "Find files with most lines of code",
        "শীর্ষ অবদানকারী কারা?",  # Bengali: Who are the top contributors?
        "find rakib",
        "who committed today?"
    ]
    
    print("🧪 Testing Query Generation:")
    print("=" * 50)
    
    for question in test_questions:
        print(f"\n❓ Question: {question}")
        cypher_query = query_gen.generate_query(question)
        print(f"🔧 Generated Query: {cypher_query}")
        
        # Simulate some results for response generation
        mock_results = [
            {'c.name': 'John Doe', 'c.email': 'john@example.com', 'c.commits': 150},
            {'c.name': 'Jane Smith', 'c.email': 'jane@example.com', 'c.commits': 120}
        ]
        
        response = query_gen.generate_response(question, mock_results)
        print(f"💬 Response: {response[:200]}...")
        print("-" * 50)