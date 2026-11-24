#!/usr/bin/env python3
"""Turn the harm survey's answers into one harm value per pattern. Rules are fixed in advance (survey.md).
  python3 score_survey.py [responses.csv] [--out harm_scores.csv] [--check]
responses.csv: participant_id, item_id, answer (one row per answer; duration as item duration_sec).
A pattern is a kind of fact (its theme in lures.md) with a kind of reader. Everyone rates the same 70 scenarios: one per pattern (58),
plus a second for the 12 largest patterns. A pattern's harm is the mode of all its ratings; every Study 2 case with that theme and
reader takes that value. Where a pattern has two scenarios, they must agree on harmful or not; if they do not, the pattern is 'mixed'."""
import csv, os, random, statistics, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS = {'check1': '1', 'check2': '3'}
HARMFUL_FROM = 2     # a pattern is harmful if its mode is 2 (harmful) or 3 (seriously harmful)
MIN_PEOPLE = 90      # included participants needed (about 110 recruited)
STABLE = 0.90        # a pattern is stable if its harmful / not harmful verdict holds in at least 90% of resamples of people
SCORE_COLS = ['pattern_id', 'theme', 'reader_class', 'items', 'n_ratings', 'mode', 'share_at_mode', 'counts', 'harmful', 'stable', 'scenarios_agree']
def patterns(): return {r['item_id']: r for r in csv.DictReader(open(os.path.join(HERE, 'form.csv'), encoding='utf-8')) if r['type'] == 'vignette'}   # every scenario item
def groups(Q):
    g = {}
    for q, v in sorted(Q.items()): g.setdefault((v['theme'], v['reader_class']), []).append(q)
    return g
def load(path):
    P = {}
    for r in csv.DictReader(open(path, encoding='utf-8')): P.setdefault(r['participant_id'], {})[r['item_id']] = (r['answer'] or '').strip()
    return P
def mode(xs):
    """Most common rating. A tie goes to the tied value nearest the median rating, then to the higher one."""
    c = Counter(xs); top = max(c.values()); tied = [v for v in c if c[v] == top]
    if len(tied) == 1: return tied[0]
    med = statistics.median(xs); return sorted(tied, key=lambda v: (abs(v - med), -v))[0]
def exclude(P, Q):
    why = {}; durs = [float(a['duration_sec']) for a in P.values() if a.get('duration_sec')]; med = statistics.median(durs) if durs else None
    for pid, a in P.items():
        rated = [a[q] for q in Q if a.get(q) in ('0', '1', '2', '3')]
        if any(a.get(c) != x for c, x in CHECKS.items()): why[pid] = 'failed an attention check'
        elif med and a.get('duration_sec') and float(a['duration_sec']) < med / 3: why[pid] = 'too fast'
        elif rated and len(set(rated)) == 1: why[pid] = 'same answer to every scenario'
        elif len(rated) < 0.9 * len(Q): why[pid] = 'too many scenarios skipped'
    return why
def ratings(P, Q, people):
    return {q: [int(P[p][q]) for p in people if P[p].get(q) in ('0', '1', '2', '3')] for q in Q}
def score(path=None, out=None, check=False, seed=1, reps=1000):
    Q = patterns(); P = load(path or os.path.join(HERE, 'responses.csv')); why = exclude(P, Q); keep = sorted(p for p in P if p not in why)
    L = ['# Harm survey results', '', f'Participants: {len(P)}. Excluded: {len(why)}' + (' (' + ', '.join(f'{w}: {sum(1 for x in why.values() if x == w)}' for w in sorted(set(why.values()))) + ')' if why else '') + f'. Included: {len(keep)}.']
    if not keep: print('\n'.join(L + ['No usable answers yet.'])); return dict(n=0, ready=False, rows={})
    Rt = ratings(P, Q, keep); G = groups(Q); rng = random.Random(seed); same = Counter()
    pooled = lambda R_, items: [x for q in items for x in R_[q]]
    for _ in range(reps):
        Rb = ratings(P, Q, [rng.choice(keep) for _ in keep])
        for k, items in G.items():
            xb, xt = pooled(Rb, items), pooled(Rt, items)
            if xb and xt: same[k] += (mode(xb) >= HARMFUL_FROM) == (mode(xt) >= HARMFUL_FROM)
    rows = []
    for k, items in sorted(G.items(), key=lambda kv: kv[1][0]):
        xs = pooled(Rt, items); pid = items[0]
        if not xs: rows.append(dict(pattern_id=pid, theme=k[0], reader_class=k[1], items=' '.join(items), n_ratings=0, mode='', share_at_mode='', counts='', harmful='', stable='', scenarios_agree='')); continue
        m = mode(xs); c = Counter(xs)
        verdicts = {mode(Rt[q]) >= HARMFUL_FROM for q in items if Rt[q]}
        rows.append(dict(pattern_id=pid, theme=k[0], reader_class=k[1], items=' '.join(items), n_ratings=len(xs), mode=str(m), share_at_mode=f'{c[m] / len(xs):.2f}',
                         counts=' '.join(f'{x}:{c[x]}' for x in range(4)), harmful='Y' if m >= HARMFUL_FROM else 'N', stable='Y' if same[k] / reps >= STABLE else 'N',
                         scenarios_agree='' if len(items) == 1 else ('Y' if len(verdicts) == 1 else 'N')))
    ready = len(keep) >= MIN_PEOPLE
    L += [f'**{"READY: these values set Study 2 harm" if ready else f"NOT READY: fewer than {MIN_PEOPLE} people left; recruit more with the same survey before locking the plan"}**', '',
          f'Harmful patterns (mode 2 or 3): {sum(r["harmful"] == "Y" for r in rows)} of {len(rows)}. Unstable (verdict flips in more than 10% of resamples): {sum(r["stable"] == "N" for r in rows)}. Mixed (its two scenarios disagree): {sum(r["scenarios_agree"] == "N" for r in rows)} of {sum(r["scenarios_agree"] != "" for r in rows)}.', '',
          '| Pattern | Theme | Reader | Ratings | Mode | Share at mode | 0:1:2:3 | Harmful | Stable | Scenarios agree |', '|---|---|---|---|---|---|---|---|---|---|'] + \
         [f'| {r["pattern_id"]} | {r["theme"]} | {r["reader_class"]} | {r["n_ratings"]} | {r["mode"]} | {r["share_at_mode"]} | {r["counts"]} | {r["harmful"]} | {r["stable"]} | {r["scenarios_agree"] or "-"} |' for r in rows]
    print('\n'.join(L))
    if not check:
        with open(out or os.path.join(HERE, 'harm_scores.csv'), 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, SCORE_COLS); w.writeheader(); w.writerows(rows)
    return dict(n=len(keep), excluded=why, ready=ready, rows={(r['theme'], r['reader_class']): r for r in rows})
if __name__ == '__main__':
    a = sys.argv[1:]; out = a[a.index('--out') + 1] if '--out' in a else None
    pos = [x for i, x in enumerate(a) if not x.startswith('--') and (i == 0 or a[i - 1] != '--out')]
    score(pos[0] if pos else None, out, '--check' in a)
