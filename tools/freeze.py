#!/usr/bin/env python3
"""Hash the design files before any real data exist. python3 tools/freeze.py write [--force] | write-after-pilot [--force] | write-before-study3 [--force] | verify
write and write-after-pilot refuse to overwrite an existing freeze unless --force is given. Checkbooks are frozen by structure only: the ids and design columns, never the cells the operator fills in."""
import hashlib, os, sys
R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')); M = os.path.join(R, 'FREEZE.sha256')
START = ['DESIGN.md', 'study1_storage/facts.md', 'study1_storage/feed.py', 'study1_storage/score.py', 'study2_email/lures.md', 'study2_email/scenarios.csv', 'study2_email/score.py', 'study2_email/harm_check.py',
         'study3_correction/correction.md', 'study3_correction/bland_saves.txt', 'study3_correction/neutral_prompts.txt', 'study3_correction/build.py', 'study3_correction/score.py',
         'adjudication/PROTOCOL.md', 'adjudication/kappa.py', 'adjudication/plant.py', 'tools/stats.py', 'tools/mdtable.py', 'study1_storage/checkbook.csv', 'study2_email/checkbook.csv']
STRUCT = {'study1_storage/checkbook.csv': ['id'], 'study2_email/checkbook.csv': ['run_id', 'run_order', 'scenario_id', 'arm'],
          'study3_correction/cases.csv': ['case_id', 'case_kind', 'scenario_id', 'fact_id', 'transfer_ids'], 'study3_correction/checkbook.csv': ['run_id', 'run_order', 'account_id', 'correction', 'sessions', 'saves', 'kind', 'scenario_id']}
PILOT = ['adjudication/rulebook.md', 'study2_email/prompt_library.md', 'study2_email/post_pilot_prompt.md']      # these are written and rewritten by the pilot, so they freeze after it
M2 = os.path.join(R, 'FREEZE_AFTER_PILOT.sha256')
STUDY3 = ['study3_correction/cases.csv', 'study3_correction/checkbook.csv']   # built from Study 2's results, so they freeze after Study 2 and before Study 3 starts
M3 = os.path.join(R, 'FREEZE_BEFORE_STUDY3.sha256')
import csv
def h(p):
    if p in STRUCT:   # headings plus the design columns only; filling in a result cell must not break the freeze
        rows = list(csv.DictReader(open(os.path.join(R, p), encoding='utf-8'))); body = [list(rows[0].keys()) if rows else []] + [[r[c] for c in STRUCT[p]] for r in rows]
        return hashlib.sha256(repr(body).encode()).hexdigest()
    return hashlib.sha256(open(os.path.join(R, p), 'rb').read()).hexdigest()
def refuse(m): print('REFUSED: ' + os.path.basename(m) + ' already exists. A freeze is written once, before any data. Use --force only if you mean to re-freeze, and record why.'); sys.exit(2)
if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if x != '--force']; force = '--force' in sys.argv[1:]
    TARGET = {'write': (M, START), 'write-after-pilot': (M2, PILOT), 'write-before-study3': (M3, STUDY3)}
    if len(a) == 1 and a[0] in TARGET and os.path.exists(TARGET[a[0]][0]) and not force: refuse(TARGET[a[0]][0])
    if a == ['write']: open(M, 'w').write(''.join(f'{h(p)}  {p}\n' for p in START)); print('froze', len(START), 'files (design, data, scorers). Run before the pilot.')
    elif a == ['write-after-pilot']: open(M2, 'w').write(''.join(f'{h(p)}  {p}\n' for p in PILOT)); print('froze', len(PILOT), 'files (rulebook, prompt library). Run when the pilot ends.')
    elif a == ['write-before-study3']: open(M3, 'w').write(''.join(f'{h(p)}  {p}\n' for p in STUDY3)); print('froze', len(STUDY3), 'files (Study 3 case list and run list). Run after build.py cases, before the first Study 3 account.')
    elif a == ['verify']:
        bad = []
        for m in (M, M2, M3):
            if os.path.exists(m): bad += [p for l in open(m) for hh, p in [l.rstrip('\n').split('  ', 1)] if h(p) != hh]
        print('FROZEN FILES CHANGED: ' + ', '.join(bad) if bad else 'freeze intact'); sys.exit(1 if bad else 0)
    else: print(__doc__)
