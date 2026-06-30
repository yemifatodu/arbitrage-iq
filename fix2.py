content = open(r'C:\Users\HP\crypto-arbitrage-tracker\scanner.py', encoding='utf-8').read()
replacements = [
    ('━━ SCAN STARTED ━━', '-- SCAN STARTED --'),
    ('ℹ️  No opportunities', '[INFO] No opportunities'),
    ('✅', '[OK]'),
    ('logging.FileHandler(\'scanner.log\'),', 'logging.FileHandler(\'scanner.log\', encoding=\'utf-8\'),'),
    ('logging.StreamHandler()', 'logging.StreamHandler(open(1, "w", encoding="utf-8", closefd=False))'),
]
for old, new in replacements:
    content = content.replace(old, new)
open(r'C:\Users\HP\crypto-arbitrage-tracker\scanner.py', 'w', encoding='utf-8').write(content)
print('Done')
