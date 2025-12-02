import re

with open(r'src\ui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove docstrings
content = re.sub(r'"""[^"]*"""', '', content, flags=re.DOTALL)
content = re.sub(r"'''[^']*'''", '', content, flags=re.DOTALL)

# Remove comments
lines = content.split('\n')
cleaned = []
for line in lines:
    if line.strip().startswith('#'):
        continue
    if ' #' in line and '"#' not in line and "'#" not in line:
        line = line.split(' #')[0]
    cleaned.append(line)

content = '\n'.join(cleaned)

# Remove help parameters
content = re.sub(r',\s*help="[^"]*"', '', content)
content = re.sub(r",\s*help='[^']*'", '', content)

# Remove st.caption lines
content = re.sub(r'\s*st\.caption\([^)]*\)\s*\n', '\n', content)

# Remove st.info lines
content = re.sub(r'\s*st\.info\([^)]*\)\s*\n', '\n', content)

# Remove empty lines (keep max 1)
lines = content.split('\n')
cleaned = []
prev_empty = False
for line in lines:
    if not line.strip():
        if not prev_empty:
            cleaned.append(line)
            prev_empty = True
    else:
        cleaned.append(line)
        prev_empty = False

content = '\n'.join(cleaned)

with open(r'src\ui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("File stripped successfully")
