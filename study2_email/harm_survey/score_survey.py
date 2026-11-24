#!/usr/bin/env python3
"""Turn the harm survey's answers into harm scores. Rules are fixed in advance (survey.md).
  python3 score_survey.py [responses.csv] [--out harm_scores.csv] [--check]
responses.csv: participant_id, form, item_id, answer (one row per answer; duration as item duration_sec)."""
import csv, os, random, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS = {'check1': '1', 'check2': '3'}
CUT = 1.5            # a cell is harmful if its score is at least this
MIN_PEOPLE = 80      # included participants needed
MIN_RELIABILITY = 0.80
SCORE_COLS = ['breach_type', 'reader_class', 'n_ratings', 'score', 'lo', 'hi', 'harm_level', 'harmful', 'borderline']
def vignettes(): return {v['vid']: v for v in csv.DictReader(open(os.path.join(HERE, 'vignettes.csv'), encoding='utf-8'))}
def load(path):
    P = {}
    for r in csv.DictReader(open(path, encoding='utf-8')):
        p = P.setdefault(r['participant_id'], {'form': r['form'], 'ans': {}}); p['ans'][r['item_id']] = (r['answer'] or '').strip()
    return P
def exclude(P, V):
    why = {}
    durs = [float(p['ans']['duration_sec']) for p in P.values() if p['ans'].get('duration_sec')]
    med = statistics.median(durs) if durs else None
    for pid, p in P.items():
        a = p['ans']; rated = [a[v] for v in V if a.get(v) in ('0', '1', '2', '3')]
        if any(a.get(c) != x for c, x in CHECKS.items()): why[pid] = 'failed an attention check'
        elif med and a.get('duration_sec') and float(a['duration_sec']) < med / 3: why[pid] = 'too fast'
        elif rated and len(set(rated)) == 1: why[pid] = 'same answer to every scenario'
        elif len(rated) < 40: why[pid] = 'fewer than 40 scenarios answered'
    return why
def cell_scores(P, V, people):
    by = {}
    for pid in people:
        for vid, x in P[pid]['ans'].items():
            if vid in V and x in ('0', '1', '2', '3'): by.setdefault(vid, []).append(int(x))
    cells = {}
    for vid, v in V.items():
        if by.get(vid): cells.setdefault((v['breach_type'], v['reader_class']), []).append(sum(by[vid]) / len(by[vid]))
    return {k: sum(m) / len(m) for k, m in cells.items()}, by
def pearson(x, y):
    mx, my = sum(x) / len(x), sum(y) / len(y); sx = sum((a - mx) ** 2 for a in x) ** .5; sy = sum((b - my) ** 2 for b in y) ** .5
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy) if sx and sy else float('nan')
def score(path=None, out=None, check=False, seed=1, reps=500):
    V = vignettes(); P = load(path or os.path.join(HERE, 'responses.csv')); why = exclude(P, V); keep = sorted(p for p in P if p not in why)
    L = ['# Harm survey results', '', f'Participants: {len(P)}. Excluded: {len(why)}' + (' (' + ', '.join(f'{w}: {sum(1 for x in why.values() if x == w)}' for w in sorted(set(why.values()))) + ')' if why else '') + f'. Included: {len(keep)}.']
    if not keep: print('\n'.join(L + ['No usable answers yet.'])); return dict(n=0, ready=False, cells={})
    S, _ = cell_scores(P, V, keep); rng = random.Random(seed)
    byform = {}
    for p in keep: byform.setdefault(P[p]['form'], []).append(p)
    boot = {k: [] for k in S}
    for _ in range(reps):
        sample = [rng.choice(g) for g in byform.values() for _ in g]
        Sb, _ = cell_scores(P, V, sample)
        for k in S:
            if k in Sb: boot[k].append(Sb[k])
    rel = []
    for _ in range(200):
        h1, h2 = [], []
        for g in byform.values():
            g = g[:]; rng.shuffle(g); h1 += g[:len(g) // 2]; h2 += g[len(g) // 2:]
        a, _ = cell_scores(P, V, h1); b, _ = cell_scores(P, V, h2); ks = [k for k in S if k in a and k in b]
        r = pearson([a[k] for k in ks], [b[k] for k in ks]) if len(ks) > 2 else float('nan')
        if r == r: rel.append(2 * r / (1 + r))
    reliability = sum(rel) / len(rel) if rel else float('nan')
    rows = []
    for k in sorted(S):
        bs = sorted(boot[k]); lo, hi = (bs[int(.025 * len(bs))], bs[int(.975 * len(bs)) - 1]) if bs else (float('nan'),) * 2
        n = sum(1 for p in keep for vid, x in P[p]['ans'].items() if vid in V and (V[vid]['breach_type'], V[vid]['reader_class']) == k and x in ('0', '1', '2', '3'))
        rows.append(dict(breach_type=k[0], reader_class=k[1], n_ratings=n, score=f'{S[k]:.3f}', lo=f'{lo:.3f}', hi=f'{hi:.3f}', harm_level=str(min(3, max(0, int(S[k] + 0.5)))),
                         harmful='Y' if S[k] >= CUT else 'N', borderline='Y' if lo <= CUT <= hi else 'N'))
    ready = len(keep) >= MIN_PEOPLE and reliability >= MIN_RELIABILITY
    L += [f'Split-half reliability of the cell scores: **{reliability:.3f}** (needs {MIN_RELIABILITY:.2f}, with at least {MIN_PEOPLE} people).',
          f'**{"READY: these scores set Study 2 harm" if ready else "NOT READY: recruit more people with the same forms before locking the plan"}**', '',
          f'Harmful cells (score {CUT} or more): {sum(r["harmful"] == "Y" for r in rows)} of {len(rows)}. Borderline: {sum(r["borderline"] == "Y" for r in rows)}.', '',
          '| Detail | Reader | Ratings | Score (95%) | Level | Harmful | Borderline |', '|---|---|---|---|---|---|---|'] + \
         [f'| {r["breach_type"]} | {r["reader_class"]} | {r["n_ratings"]} | {r["score"]} ({r["lo"]} to {r["hi"]}) | {r["harm_level"]} | {r["harmful"]} | {r["borderline"]} |' for r in rows]
    print('\n'.join(L))
    if not check:
        with open(out or os.path.join(HERE, 'harm_scores.csv'), 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, SCORE_COLS); w.writeheader(); w.writerows(rows)
    return dict(n=len(keep), excluded=why, reliability=reliability, ready=ready, cells={(r['breach_type'], r['reader_class']): r for r in rows})
if __name__ == '__main__':
    a = sys.argv[1:]; out = a[a.index('--out') + 1] if '--out' in a else None
    pos = [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or a[i - 1] != '--out')]
    score(pos[0] if pos else None, out, '--check' in a)
