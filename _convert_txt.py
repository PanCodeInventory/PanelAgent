import re
from pathlib import Path

_BASE = Path(__file__).parent

with open(_BASE / 'PROMOTION.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Keep bold markers (convert **bold** to 【bold】)
content = re.sub(r'\*\*(.+?)\*\*', r'【\1】', content)

# Keep italic markers (convert *italic* to 『italic』)
content = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'『\1』', content)

# Remove heading markers
content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)

# Remove horizontal rules
content = re.sub(r'^---+$', '', content, flags=re.MULTILINE)

# Remove blockquote markers
content = re.sub(r'^>\s+', '', content, flags=re.MULTILINE)

# Remove code block fences
content = re.sub(r'^```.*$', '', content, flags=re.MULTILINE)

# Remove inline code backticks
content = re.sub(r'`([^`]+)`', r'\1', content)

# Clean up excessive blank lines
content = re.sub(r'\n{3,}', '\n\n', content)

with open(_BASE / 'PROMOTION.txt', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
