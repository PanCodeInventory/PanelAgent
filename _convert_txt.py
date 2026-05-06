import re

with open('/home/user/PanChongshi/Repo/PanelAgent/PROMOTION.md', 'r') as f:
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

with open('/home/user/PanChongshi/Repo/PanelAgent/PROMOTION.txt', 'w') as f:
    f.write(content)

print('Done')
