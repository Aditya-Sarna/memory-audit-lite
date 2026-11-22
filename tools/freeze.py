#!/usr/bin/env python3
"""Hash the design files before any real data exist. python3 tools/freeze.py write [--force] | write-after-pilot [--force] | write-after-plan [--force] | verify
write, write-after-pilot and write-after-plan refuse to overwrite an existing freeze unless --force is given. Checkbooks are frozen by structure only: the ids and design columns, never the cells the operator fills in."""
import hashlib, os, sys
R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')); M = os.path.join(R, 'FREEZE.sha256')
START = ['DESIGN.md', 'study1_storage/facts.md', 'study1_storage/feed.py', 'study1_storage/score.py', 'study2_email/lures.md', 'study2_email/score.py', 'study3_delay/plan.py',
         'study3_delay/rules.md', 'study3_delay/filler_lines.txt', 'study3_delay/neutral_prompts.txt', 'study3_delay/score.py', 'adjudication/PROTOCOL.md', 'adjudication/kappa.py', 'adjudication/plant.py', 'tools/stats.py', 'tools/mdtable.py',
         'study3_delay/seed.py', 'study1_storage/checkbook.csv', 'study2_email/checkbook.csv']
STRUCT = {'study1_storage/checkbook.csv': ['id'], 'study2_email/checkbook.csv': ['run_id', 'run_order', 'scenario_id', 'arm'],
          'study3_delay/plan/checkbook.csv': ['run_id', 'store_id', 'run_order', 'fact_id', 'kind', 'scenario_id', 'task_id', 'rule_id', 'rule_match'],
          'study3_delay/plan/stores.csv': ['store_id', 'replicate', 'cell', 'p', 'w', 'n_facts', 'rule_id']}
PILOT = ['adjudication/rulebook.md', 'study2_email/prompt_library.md']      # these are written and rewritten by the pilot, so they freeze after it
PLAN = ['study3_delay/plan/stores.csv', 'study3_delay/plan/facts_by_store.csv', 'study3_delay/plan/checkbook.csv', 'study3_delay/plan/flagged.csv']   # written by study3_delay/plan.py from the Study 2 results, so they freeze after Study 2
M2 = os.path.join(R, 'FREEZE_AFTER_PILOT.sha256'); M3 = os.path.join(R, 'FREEZE_AFTER_PLAN.sha256')
import csv
def h(p):
    if p in STRUCT:   # headings plus the design columns only; filling in a result cell must not break the freeze
        rows = list(csv.DictReader(open(os.path.join(R, p), encoding='utf-8'))); body = [list(rows[0].keys()) if rows else []] + [[r[c] for c in STRUCT[p]] for r in rows]
        return hashlib.sha256(repr(body).encode()).hexdigest()
    return hashlib.sha256(open(os.path.join(R, p), 'rb').read()).hexdigest()
def refuse(m): print('REFUSED: ' + os.path.basename(m) + ' already exists. A freeze is written once, before any data. Use --force only if you mean to re-freeze, and record why.'); sys.exit(2)
if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if x != '--force']; force = '--force' in sys.argv[1:]
    tgt = {'write': M, 'write-after-pilot': M2, 'write-after-plan': M3}
    if len(a) == 1 and a[0] in tgt and os.path.exists(tgt[a[0]]) and not force: refuse(tgt[a[0]])
    if a == ['write']: open(M, 'w').write(''.join(f'{h(p)}  {p}\n' for p in START)); print('froze', len(START), 'files (design, data, scorers). Run before the pilot.')
    elif a == ['write-after-pilot']: open(M2, 'w').write(''.join(f'{h(p)}  {p}\n' for p in PILOT)); print('froze', len(PILOT), 'files (rulebook, prompt library). Run when the pilot ends.')
    elif a == ['write-after-plan']:
        miss = [p for p in PLAN if not os.path.exists(os.path.join(R, p))]
        if miss: print('REFUSED: no plan yet (' + ', '.join(miss) + '). Run python3 study3_delay/plan.py <Study 2 checkbook> first.'); sys.exit(2)
        open(M3, 'w').write(''.join(f'{h(p)}  {p}\n' for p in PLAN)); print('froze', len(PLAN), 'files (the Study 3 plan). Run when plan.py has written it from the Study 2 results.')
    elif a == ['verify']:
        bad = []
        for m in (M, M2, M3):
            if os.path.exists(m): bad += [p for l in open(m) for hh, p in [l.rstrip('\n').split('  ', 1)] if h(p) != hh]
        print('FROZEN FILES CHANGED: ' + ', '.join(bad) if bad else 'freeze intact'); sys.exit(1 if bad else 0)
    else: print(__doc__)
