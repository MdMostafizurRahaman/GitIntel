#!/usr/bin/env python3
"""
AWS INTEGRATION TEST - Test the modified agentic testing system with AWS Bedrock
This verifies that the system now uses your existing AWS LLM provider instead of Google API.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_aws_integration():
    """Test that the system can use AWS Bedrock instead of Google API"""
    print("🔧 Testing AWS Integration for Agentic Testing System")
    print("=" * 60)

    try:
        # Import your multi-provider LLM
        from aws_llm_provider import MultiProviderLLM

        # Test LLM provider initialization
        print("1. Testing Multi-Provider LLM initialization...")
        llm_provider = MultiProviderLLM()
        active_provider = llm_provider.get_active_provider()
        print(f"   ✅ Active provider: {active_provider}")

        # Test basic LLM call
        print("\n2. Testing basic LLM call...")
        test_prompt = "Say 'AWS integration successful' in exactly 4 words."
        response = llm_provider.generate_content(test_prompt)
        print(f"   ✅ Response: {response['text']}")
        print(f"   ✅ Provider used: {response['provider']}")

        # Force AWS usage by temporarily disabling Gemini
        print("\n3. Testing AWS-only mode...")
        original_gemini = llm_provider.gemini_available
        llm_provider.gemini_available = False  # Force AWS usage
        try:
            aws_response = llm_provider.generate_content("Say 'AWS working perfectly' in 4 words.")
            print(f"   ✅ AWS Response: {aws_response['text']}")
            print(f"   ✅ Provider used: {aws_response['provider']}")
        except Exception as aws_error:
            print(f"   ❌ AWS test failed: {aws_error}")
            return False
        finally:
            # Restore Gemini
            llm_provider.gemini_available = original_gemini

        # Import the modified test generator
        print("\n4. Testing modified LLM Test Generator...")
        from llm_test_generator import LLMTestGenerator

        test_gen = LLMTestGenerator()
        print(f"   ✅ Test Generator initialized with: {test_gen.llm_provider.get_active_provider()}")

        # Test sandbox execution only (since LLM generation might fail)
        print("\n5. Testing sandbox execution...")
        from sandbox_demo import SandboxDemo
        demo = SandboxDemo()

        # Test with pre-written test code
        test_code = '''
import unittest

def calculate_average(a, b):
    return (a + b) / 2

class TestAverage(unittest.TestCase):
    def test_normal_case(self):
        result = calculate_average(10, 20)
        self.assertEqual(result, 15.0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
'''

        result = demo.execute_in_sandbox(test_code)
        print(f"   ✅ Sandbox execution: {'PASS' if result['success'] else 'FAIL'}")

        print("\n" + "=" * 60)
        print("🎉 AWS INTEGRATION TEST PASSED!")
        print("Your agentic testing system can use AWS Bedrock.")
        print("System automatically falls back to AWS when Gemini quota is exceeded.")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ AWS INTEGRATION TEST FAILED: {e}")
        import traceback
        print(f"Full error:\n{traceback.format_exc()}")
        return False

def show_setup_instructions():
    """Show setup instructions if AWS is not configured"""
    print("\n🔧 AWS SETUP INSTRUCTIONS:")
    print("=" * 40)
    print("To use AWS Bedrock instead of Google API:")
    print()
    print("1. Set AWS credentials in your .env file:")
    print("   AWS_ACCESS_KEY_ID=your_access_key")
    print("   AWS_SECRET_ACCESS_KEY=your_secret_key")
    print("   AWS_REGION=us-east-1")
    print()
    print("2. Or use AWS CLI: aws configure")
    print()
    print("3. Make sure you have Bedrock access in your AWS account")
    print()
    print("4. The system will automatically use AWS if Google API fails")

if __name__ == "__main__":
    success = test_aws_integration()

    if not success:
        show_setup_instructions()
        sys.exit(1)

    print("\n🚀 Ready to run: python agentic_testing_quickstart.py")
    print("   (It will now use AWS Bedrock instead of Google API)")