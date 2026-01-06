"""
AWS Bedrock LLM Provider
- Uses Claude models (Anthropic) via AWS Bedrock
- No quota limits (pay-as-you-go)
- Fallback when Gemini quota exceeded
"""

import boto3
import json
from typing import Dict, Any, Optional
import os

class AWSBedrockProvider:
    """AWS Bedrock provider for Claude models"""
    
    def __init__(self, 
                 aws_access_key: str = None,
                 aws_secret_key: str = None, 
                 region: str = 'us-east-1'):
        """
        Initialize AWS Bedrock client
        
        Args:
            aws_access_key: AWS access key ID (from .env)
            aws_secret_key: AWS secret access key (from .env)
            region: AWS region (default: us-east-1)
        """
        try:
            # Debug: Check if credentials provided
            has_keys = bool(aws_access_key and aws_secret_key)
            print(f"[DEBUG] AWS init - Has credentials: {has_keys}")
            
            # Use provided credentials or fall back to environment/boto3 default
            if aws_access_key and aws_secret_key:
                print(f"[DEBUG] Using provided AWS credentials (first 8 chars: {aws_access_key[:8]}...)")
                self.client = boto3.client(
                    service_name='bedrock-runtime',
                    region_name=region,
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key
                )
            else:
                # Use default AWS credentials (from ~/.aws/credentials or env vars)
                print(f"[DEBUG] Using environment/system AWS credentials")
                self.client = boto3.client(
                    service_name='bedrock-runtime',
                    region_name=region
                )
            
            self.region = region
            self.available = True
            print(f"[OK] AWS Bedrock initialized (region: {region})")
            
        except Exception as e:
            print(f"[WARNING] AWS Bedrock init failed: {e}")
            import traceback
            print(f"[DEBUG] AWS error trace: {traceback.format_exc()}")
            self.available = False
            self.client = None
    
    def generate_content(self, prompt: str, model: str = 'claude-3-haiku') -> Dict[str, Any]:
        """
        Generate content using AWS Bedrock Claude
        
        Args:
            prompt: User prompt
            model: Model to use (claude-3-haiku, claude-3-sonnet, claude-3-opus)
        
        Returns:
            Dict with 'text' key containing response
        """
        if not self.available:
            raise Exception("AWS Bedrock not available. Check credentials.")
        
        # Map short names to full model IDs
        model_map = {
            'claude-3-haiku': 'anthropic.claude-3-haiku-20240307-v1:0',
            'claude-3-sonnet': 'anthropic.claude-3-sonnet-20240229-v1:0',
            'claude-3-opus': 'anthropic.claude-3-opus-20240229-v1:0',
            'claude-3.5-sonnet': 'anthropic.claude-3-5-sonnet-20240620-v1:0'
        }
        
        model_id = model_map.get(model, model_map['claude-3-haiku'])
        
        # Prepare request body (Claude format)
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7
        })
        
        try:
            # Invoke model
            response = self.client.invoke_model(
                modelId=model_id,
                body=body
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            text = response_body['content'][0]['text']
            
            return {'text': text}
            
        except Exception as e:
            # Handle quota/throttling errors
            if 'ThrottlingException' in str(e):
                raise Exception(f"AWS Bedrock throttling: {e}")
            raise Exception(f"AWS Bedrock error: {e}")
    
    def is_available(self) -> bool:
        """Check if AWS Bedrock is available"""
        return self.available


class MultiProviderLLM:
    """
    Multi-provider LLM with automatic fallback
    Priority: Gemini -> AWS Bedrock
    """
    
    def __init__(self):
        """Initialize all available providers"""
        import google.generativeai as genai
        
        # Load credentials from environment
        self.gemini_key = os.environ.get('GEMINI_API_KEY', '')
        self.aws_access = os.environ.get('AWS_ACCESS_KEY_ID', '')
        self.aws_secret = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
        self.aws_region = os.environ.get('AWS_REGION', 'us-east-1')
        
        # Initialize Gemini (primary)
        self.gemini_available = False
        if self.gemini_key:
            try:
                genai.configure(api_key=self.gemini_key)
                self.gemini_model = genai.GenerativeModel('models/gemini-2.5-flash-lite-preview-09-2025')
                self.gemini_available = True
                print("[OK] Gemini primary provider ready")
            except Exception as e:
                print(f"[WARNING] Gemini init failed: {e}")
        
        # Initialize AWS Bedrock (fallback)
        self.aws_provider = None
        if self.aws_access and self.aws_secret:
            self.aws_provider = AWSBedrockProvider(
                aws_access_key=self.aws_access,
                aws_secret_key=self.aws_secret,
                region=self.aws_region
            )
            if self.aws_provider.is_available():
                print("[OK] AWS Bedrock fallback provider ready")
        else:
            print("[INFO] AWS credentials not found. Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY in .env")
    
    def generate_content(self, prompt: str) -> Dict[str, Any]:
        """
        Generate content with automatic fallback
        1. Try Gemini first
        2. If quota exceeded, fall back to AWS Bedrock
        """
        
        # Try Gemini first
        if self.gemini_available:
            try:
                response = self.gemini_model.generate_content(prompt)
                return {'text': response.text, 'provider': 'gemini'}
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if it's a quota error
                if 'quota' in error_msg or '429' in error_msg or 'resource_exhausted' in error_msg:
                    print(f"[INFO] Gemini quota exceeded. Falling back to AWS Bedrock...")
                    
                    # Fall back to AWS
                    if self.aws_provider and self.aws_provider.is_available():
                        try:
                            response = self.aws_provider.generate_content(prompt, model='claude-3-haiku')
                            return {'text': response['text'], 'provider': 'aws-bedrock-claude'}
                        except Exception as aws_error:
                            raise Exception(f"Both providers failed. Gemini: quota exceeded. AWS: {aws_error}")
                    else:
                        raise Exception(f"Gemini quota exceeded and AWS Bedrock not configured. Set AWS credentials in .env")
                else:
                    # Non-quota error, re-raise
                    raise e
        
        # If Gemini not available, try AWS directly
        if self.aws_provider and self.aws_provider.is_available():
            response = self.aws_provider.generate_content(prompt, model='claude-3-haiku')
            return {'text': response['text'], 'provider': 'aws-bedrock-claude'}
        
        raise Exception("No LLM providers available. Check API keys in .env")
    
    def get_active_provider(self) -> str:
        """Get currently active provider name"""
        if self.gemini_available:
            return "Gemini (primary)"
        elif self.aws_provider and self.aws_provider.is_available():
            return "AWS Bedrock Claude (fallback)"
        return "None"


# Quick test function
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n=== Testing Multi-Provider LLM ===\n")
    
    llm = MultiProviderLLM()
    print(f"\nActive provider: {llm.get_active_provider()}\n")
    
    try:
        result = llm.generate_content("Say 'Hello from LLM' in one sentence.")
        print(f"Response: {result['text']}")
        print(f"Provider used: {result['provider']}")
    except Exception as e:
        print(f"Error: {e}")
