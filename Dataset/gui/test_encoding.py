#!/usr/bin/env python3
"""Test safe_print function"""

# Safe print function for Windows console (handles emoji encoding)
def safe_print(*args, **kwargs):
    """Print safely to console, handling emoji characters on Windows"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # If emoji fails, try to encode with 'replace' strategy
        try:
            message = ' '.join(str(arg) for arg in args)
            # Replace common emojis with text equivalents for console output
            emoji_map = {
                '✅': '[OK]',
                '❌': '[ERROR]',
                '⏱️': '[TIMEOUT]',
                '🔍': '[SEARCH]',
                '🤔': '[THINKING]',
                '⚠️': '[WARNING]',
                '📊': '[DATA]',
                '📈': '[CHART]',
                '🏛️': '[JURY]',
                '⚖️': '[VERDICT]',
                '🎉': '[SUCCESS]',
                '📝': '[NOTE]',
                '💾': '[SAVE]',
                '📁': '[FILES]',
                '🔄': '[PROCESSING]',
            }
            for emoji, text in emoji_map.items():
                message = message.replace(emoji, text)
            print(message, **kwargs)
        except:
            # Last resort: just print without the message
            pass

# Test the function
if __name__ == '__main__':
    print("Starting encoding test...")
    safe_print("✅ OK message")
    safe_print("❌ ERROR message")
    safe_print("🔍 SEARCH message")
    safe_print("✅ Applied: test_metric - added columns: {'col1', 'col2'}")
    safe_print("\n[SEARCH] GENERATED CODE FOR: test_formula")
    safe_print("[OK] Test complete!")
