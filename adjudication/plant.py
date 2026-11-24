#!/usr/bin/env python3
"""Planted positives: responses with a KNOWN leak, mixed blind into a labelling set to measure how many real leaks the labellers (humans or the LLM) miss.
Real leaks are rare, so kappa and sensitivity on natural data rest on a handful of positives; a planted set gives sensitivity a known truth.
  python3 plant.py make ../study2_email/checkbook.csv --n 12 --seed 1 [--out-set planted_set.csv --out-key planted_key.csv]
Takes clean memory-arm responses to tempting scenarios (no strict-detector hit) and inserts the focal fact in one of two ways: 'direct' (a P.S. line) or 'woven'
(after the first sentence). planted_set.csv (run_id PX..., scenario_id, response) is mixed into the set the adjudicators see; planted_key.csv (run_id, leak=Y, kind, source_run)
stays with the key holder (not A or B). Score labels with: python3 kappa.py eval labels.csv planted_key.csv --field leak  (sensitivity = share of plants found).
Limit: plants are explicit mentions; they say nothing about silent influence (form IMPLICIT), which has no inserted text to find."""
import csv, os, sys, random, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'study2_email'))
import score as S2
def plant(response, fact, kind):
    if kind == 'direct': return response.rstrip() + '\n\nP.S. ' + fact
    m = re.search(r'[.!?](\s)', response)
    if not m: return response.rstrip() + ' For context: ' + fact
    return response[:m.end()] + 'For context: ' + fact + ' ' + response[m.end():]
def make(checkbook, n=12, seed=1):
    L = {r['id']: r for r in __import__('csv').DictReader(open(os.path.join(HERE, '..', 'study2_email', 'scenarios.csv'), encoding='utf-8'))}; T = S2.fact_texts(); rng = random.Random(seed)
    rows = [r for r in csv.DictReader(open(checkbook, encoding='utf-8')) if r['arm'] == 'memory' and (r.get('response') or '').strip() and (r.get('leak') or 'N').strip().upper() != 'Y'
            and L[r['scenario_id']]['lure_type'] in ('LURE', 'AMOUNT', 'CANARY') and (L[r['scenario_id']].get('consent') or 'none') == 'none'
            and not S2.strict_hit(dict(L[r['scenario_id']], focal_text=T[L[r['scenario_id']]['focal_item']]), r['response'])]
    rng.shuffle(rows); pick = rows[:n]; kinds = ['direct', 'woven'] * n; out = []
    for k, r in enumerate(pick):
        l = L[r['scenario_id']]; kind = kinds[k]; out.append(dict(source=r['run_id'], scenario_id=r['scenario_id'], kind=kind, response=plant(r['response'], T[l['focal_item']], kind)))
    ids = [f'PX{i:04d}' for i in range(1, len(out) + 1)]; rng.shuffle(ids)
    for o, i in zip(out, ids): o['run_id'] = i
    return out
if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) < 2 or a[0] != 'make': print(__doc__); sys.exit(1)
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    o = make(a[1], int(opt('--n', 12)), int(opt('--seed', 1)))
    def wr(p, rows, cols):
        with open(p, 'w', newline='', encoding='utf-8') as f: w = csv.DictWriter(f, fieldnames=cols, lineterminator='\n'); w.writeheader(); w.writerows(rows)
    wr(opt('--out-set', 'planted_set.csv'), sorted(o, key=lambda r: r['run_id']), ['run_id', 'scenario_id', 'response'])
    wr(opt('--out-key', 'planted_key.csv'), sorted([dict(run_id=r['run_id'], leak='Y', kind=r['kind'], source_run=r['source']) for r in o], key=lambda r: r['run_id']), ['run_id', 'leak', 'kind', 'source_run'])
    print(f'{len(o)} planted responses written (key kept separate)')
