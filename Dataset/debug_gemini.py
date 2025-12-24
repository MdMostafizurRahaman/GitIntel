#!/usr/bin/env python3
"""Debug Gemini API initialization"""

import os

print("Checking Gemini setup...")
print(f"API Key: {os.getenv('GEMINI_API_KEY', 'NOT SET')[:20]}...")

try:
    import google.generativeai as genai
    print("✅ google.generativeai imported")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print(f"✅ API Key found: {api_key[:20]}...")
        genai.configure(api_key=api_key)
        print("✅ Genai configured")
        
        # Test generation
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content("Say hello")
        print(f"✅ Test generation successful: {response.text[:50]}...")
    else:
        print("❌ API Key NOT found in environment")
        
except Exception as e:
    print(f"❌ Error: {e}")
