"""List available Gemini models"""
import google.generativeai as genai

# Configure with first key
with open('.env', 'r') as f:
    for line in f:
        if line.startswith('GEMINI_API_KEY='):
            api_key = line.split('=')[1].strip()
            break

genai.configure(api_key=api_key)

print("Available models:")
print("="*80)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"\nName: {model.name}")
        print(f"  Display: {model.display_name}")
        print(f"  Description: {model.description[:100] if model.description else 'N/A'}")
        print(f"  Methods: {model.supported_generation_methods}")
