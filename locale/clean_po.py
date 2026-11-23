import os
import re

locales = ['th', 'vi', 'ko', 'zh_Hans', 'lo']
base_dir = '/Users/thavone/vangviengview/advisor/locale'

print("🧹 Starting to clean duplicate translations...\n")

for lang in locales:
    po_file = os.path.join(base_dir, lang, 'LC_MESSAGES', 'django.po')
    if not os.path.exists(po_file):
        print(f"⚠️ Skipped {lang}: File not found")
        continue
    
    with open(po_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by 'msgid ' to isolate entries
    parts = content.split('msgid ')
    header = parts[0]
    entries = ['msgid ' + part for part in parts[1:] if part.strip()]
    
    seen = {}
    order = []
    
    for entry in entries:
        # Extract the msgid block (everything before msgstr) to use as a unique key
        match = re.search(r'^(msgid.*?)(?=\nmsgstr)', entry, re.DOTALL)
        if match:
            key = match.group(1).strip()
            # Overwrite to keep the LAST occurrence (which contains your new translations)
            seen[key] = entry
            if key not in order:
                order.append(key)
    
    # Rebuild the file
    final_entries = [header.strip()]
    for key in order:
        final_entries.append(seen[key].strip())
        
    final_content = '\n\n'.join(final_entries) + '\n'
    
    with open(po_file, 'w', encoding='utf-8') as f:
        f.write(final_content)
        
    print(f"✅ Cleaned {lang} ({len(order)} unique entries)")

print("\n🎉 All done! The duplicate definitions have been removed.")
print("👉 Now run: django-admin compilemessages")