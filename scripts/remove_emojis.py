"""
Remove all emoji from Python source files
"""
import re
from pathlib import Path

# Common emoji mappings for logging contexts
EMOJI_REPLACEMENTS = {
    '🚀': '[START]',
    '📁': '[DIR]',
    '⚙️': '[CONFIG]',
    '⏱️': '[TIME]',
    '🔍': '[SCAN]',
    '✅': '[OK]',
    '❌': '[ERROR]',
    '📡': '[DISC]',
    '🔄': '[UPDATE]',
    '📦': '[INSTANCE]',
    '📚': '[LOAD]',
    '⚠️': '[WARN]',
    '🆕': '[NEW]',
    '👋': '[STOP]',
    '🛑': '[SHUTDOWN]',
}

def remove_emojis_from_file(file_path: Path):
    """Remove emojis from a Python file"""
    content = file_path.read_text(encoding='utf-8')
    original = content
    
    # Replace known emojis with text equivalents
    for emoji, replacement in EMOJI_REPLACEMENTS.items():
        content = content.replace(emoji, replacement)
    
    # Remove any remaining emoji using regex (emoji are in specific Unicode ranges)
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    
    content = emoji_pattern.sub('', content)
    
    if content != original:
        file_path.write_text(content, encoding='utf-8')
        return True
    return False

def main():
    base_dir = Path(__file__).parent.parent / 'software' / 'homeamp-config-manager'
    
    modified_files = []
    for py_file in base_dir.rglob('*.py'):
        if remove_emojis_from_file(py_file):
            modified_files.append(py_file.relative_to(base_dir))
            print(f"Modified: {py_file.relative_to(base_dir)}")
    
    print(f"\nTotal files modified: {len(modified_files)}")

if __name__ == '__main__':
    main()
