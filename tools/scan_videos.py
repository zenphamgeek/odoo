#!/usr/bin/env python3
import os
import re

pat = re.compile(r'(?:youtube\.com|youtu\.be|vimeo\.com|dailymotion\.com)[^\s"\'<>]*', re.I)
matches = []

for folder in ['addons', 'enterprise']:
    for root, dirs, files in os.walk(folder):
        if any(x in root for x in ['.git', 'node_modules', '__pycache__', 'tests', 'test', 'l10n_']):
            continue
        for f in files:
            if f.endswith(('.xml', '.js', '.py')):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                        for lno, line in enumerate(fp, 1):
                            m = pat.findall(line)
                            if m:
                                matches.append((path, lno, m, line.strip()))
                except Exception:
                    pass

print("Total matches:", len(matches))
for p, lno, m, line in matches:
    if 'social_demo' not in p and 'test' not in p and 'event_track_demo' not in p:
        print(f"{p}:{lno} -> {m} | {line[:100]}")
