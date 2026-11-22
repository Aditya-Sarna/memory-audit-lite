#!/usr/bin/env python3
"""Agreement tools. Label files are CSVs with a run_id column and the fields leak, location, form.
  python3 kappa.py pair A.csv B.csv [--field leak]     two humans (or blind vs anchored): kappa with 95% bootstrap interval, positive/negative agreement, PABAK, AC1, every disagreement
  python3 kappa.py eval LLM.csv GOLD.csv [--field leak]  LLM against gold: the same, plus sensitivity, specificity, precision, and every false negative / false positive
Rare leaks make plain kappa unstable (the kappa paradox), so positive agreement, PABAK and AC1 are always printed beside it."""
import csv, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))
from stats import cohen_kappa, pabak, gwet_ac1, boot_ci, confusion
def load(p, field): return {(r.get('run_id') or r.get('id')): (r.get(field) or '').strip().upper() for r in csv.DictReader(open(p, encoding='utf-8')) if (r.get(field) or '').strip()}
def agree(a, b, field='leak', pos='Y'):
    ids = sorted(set(a) & set(b)); x = [a[i] for i in ids]; y = [b[i] for i in ids]; n = len(ids)
    tp = sum(1 for u, v in zip(x, y) if u == pos and v == pos); fp = sum(1 for u, v in zip(x, y) if u == pos and v != pos); fn = sum(1 for u, v in zip(x, y) if u != pos and v == pos); tn = n - tp - fp - fn
    out = dict(n=n, ids=ids, x=x, y=y, tp=tp, fp=fp, fn=fn, tn=tn, kappa=cohen_kappa(x, y), pabak=pabak(x, y), ac1=gwet_ac1(x, y),
               pa=2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else float('nan'), na=2 * tn / (2 * tn + fp + fn) if 2 * tn + fp + fn else float('nan'))
    out['ci'] = boot_ci(cohen_kappa, list(zip(x, y)), reps=1000) if n >= 10 else (float('nan'),) * 2
    return out
def report(a, b, field, gold=False):
    r = agree(a, b, field); f = lambda v: f'{v:.3f}'
    L = [f'field {field}: {r["n"]} items in common', f'kappa {f(r["kappa"])} (95% {f(r["ci"][0])} to {f(r["ci"][1])}); PABAK {f(r["pabak"])}; AC1 {f(r["ac1"])}; positive agreement {f(r["pa"])}; negative agreement {f(r["na"])}']
    if r['n'] and (r['tp'] + r['fn']) / r['n'] < 0.1 or r['n'] and (r['tp'] + r['fp']) / r['n'] < 0.1: L.append('Prevalence is under 10%: trust positive agreement, PABAK and AC1 over kappa.')
    if gold:
        L.append(f'sensitivity {f(r["tp"] / (r["tp"] + r["fn"])) if r["tp"] + r["fn"] else "n/a"} ({r["tp"]}/{r["tp"] + r["fn"]}); specificity {f(r["tn"] / (r["tn"] + r["fp"])) if r["tn"] + r["fp"] else "n/a"} ({r["tn"]}/{r["tn"] + r["fp"]}); precision {f(r["tp"] / (r["tp"] + r["fp"])) if r["tp"] + r["fp"] else "n/a"}')
        L += [f'MISSED by the LLM (gold Y): {[i for i, u, v in zip(r["ids"], r["x"], r["y"]) if u != "Y" and v == "Y"]}', f'FALSE ALARM (LLM Y, gold not): {[i for i, u, v in zip(r["ids"], r["x"], r["y"]) if u == "Y" and v != "Y"]}']
    else: L.append(f'disagreements: {[i for i, u, v in zip(r["ids"], r["x"], r["y"]) if u != v]}')
    labs, m = confusion(r['x'], r['y']); L.append('confusion (rows first file, columns second): ' + str(labs) + ' ' + str(m.astype(int).tolist()))
    print('\n'.join(L)); return r
if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) < 3 or a[0] not in ('pair', 'eval'): print(__doc__); sys.exit(1)
    fld = a[a.index('--field') + 1] if '--field' in a else 'leak'
    report(load(a[1], fld), load(a[2], fld), fld, gold=a[0] == 'eval')
