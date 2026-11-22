#!/usr/bin/env python3
"""Print the lines to seed into one store, in the store's own order: python3 seed.py P1-R2-P3W25 [--plan DIR]
The plan (stores.csv, facts_by_store.csv) is written by plan.py from the Study 2 results; by default it is read from study3_delay/plan.
Fact wording lives only in the libraries (study1_storage/facts.md); the plan lists ids. Rule stores (repeat 2 and 3) get one more line, the privacy rule from rules.md, after the facts."""
import csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'tools')); import mdtable
PLAN = os.path.join(HERE, 'plan')
def texts():
    p = os.path.join(HERE, '..', 'study1_storage', 'facts.md')
    return {r['id']: r['fact'] for r in mdtable.read(p)}
def lines(store, plan=None):
    T = texts(); return [(r['fact_id'], T[r['fact_id']]) for r in csv.DictReader(open(os.path.join(plan or PLAN, 'facts_by_store.csv'), encoding='utf-8')) if r['store_id'] == store]
def rule_line(store, plan=None):
    """The one privacy-rule line of a rule store (None for a no-rule store). It is saved after the facts."""
    rid = [r['rule_id'] for r in csv.DictReader(open(os.path.join(plan or PLAN, 'stores.csv'), encoding='utf-8')) if r['store_id'] == store][0]
    if rid in ('', 'NONE'): return None
    return [r['text'] for r in mdtable.read(os.path.join(HERE, 'rules.md')) if r['rule_id'] == rid][0]
if __name__ == '__main__':
    a = sys.argv[1:]; plan = a[a.index('--plan') + 1] if '--plan' in a else None; a = [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or a[i - 1] != '--plan')]
    if len(a) != 1: print(__doc__); sys.exit(1)
    for i, t in lines(a[0], plan): print(f'Please remember this: {t}')
    if rule_line(a[0], plan): print(f'Please remember this: {rule_line(a[0], plan)}')
