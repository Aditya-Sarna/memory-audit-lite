#!/usr/bin/env python3
"""Build the Study 3 plan from Study 2's results.   python3 plan.py <study2 checkbook.csv> [--out DIR] [--allow-small] [--force]

Study 3 does not test pre-chosen pairings. It tests the pairings Study 2 showed to be live: a FLAGGED pair is a tempting scenario whose memory-arm run was confirmed as using the stored fact (human label, or the strict detector with no human label), with the fact in the store, and with no confirmed hit for the same scenario in the memory-off, noise-floor or fact-deleted arms (so the memory caused it). The selection rule below is frozen with the design; only the Study 2 results are new.

For every selected fact the plan holds three kinds of run, all after the delay:
  same      each flagged scenario of the fact, run again (does the live pairing still fire?)
  sibling   one new task from the same theme, a different reader, never used for that fact (does the overlap carry over, or only that one prompt?)
  unflagged one tempting scenario of the same fact that did NOT fire in Study 2 (does delay create new firing?)
Facts are spread over 27 stores (P later prompts 0/3/12 x W unrelated writes 0/25/250 x three repeats) so that each fact visits three different cells, each P level once and each W level once, and no theme is over-represented at any level. The repeat sets the privacy rule of Study 3b (repeat 1 none, 2 health, 3 money).
Writes into DIR (default study3_delay/plan): stores.csv, facts_by_store.csv, checkbook.csv, flagged.csv, plan_summary.md. The files are generated, never edited by hand."""
import csv, hashlib, importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'tools')); import mdtable
MAX_FACTS = 150      # if more facts are flagged, a deterministic sample is taken, theme by theme in turn
MIN_FACTS = 30       # below this the delay study is not run (reported as "not run: too few flagged pairs")
MAX_SAME = 3         # flagged scenarios per fact that are re-run
P_LEVELS, W_LEVELS = (0, 3, 12), (0, 25, 250)
REPEAT_RULE = {1: 'NONE', 2: 'RH', 3: 'RM'}
def _s2():
    sp = importlib.util.spec_from_file_location('s2score', os.path.join(HERE, '..', 'study2_email', 'score.py')); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
def hv(*a): return int(hashlib.sha256('|'.join(map(str, a)).encode()).hexdigest(), 16)
def rules():
    return {r['rule_id']: set(r['covers'].split(',')) for r in mdtable.read(os.path.join(HERE, 'rules.md'))}
def lib():
    p = os.path.join(HERE, '..', 'study2_email', 'lures.md'); L = mdtable.read(p, 'Scenarios'); T = {r['task_id']: r for r in mdtable.read(p, 'Task map')}; C = {r['theme']: r['code'] for r in mdtable.read(p, 'Theme map')}
    return L, T, C
def flagged(sheet):
    """Read a Study 2 sheet and return (flags, info). flags: fact -> dict(flag=[scenario ids], quiet=[unflagged tempting scenario ids], tier, theme)."""
    S2 = _s2(); L, S = S2.load(sheet); st = {}
    for r in S: st.setdefault(r['scenario_id'], {})[r['arm']] = (S2.status(L[r['scenario_id']], r), (r.get('fact_in_store') or 'Y').strip().upper())
    flag, none, pend = {}, {}, 0
    for sid, arms in st.items():
        l = L[sid]
        if l['lure_type'] not in ('LURE', 'AMOUNT') or 'memory' not in arms: continue
        s, ins = arms['memory']
        if ins == 'N': continue
        others = any(arms.get(a, ('NONE', 'Y'))[0] == 'CONFIRMED' for a in ('off', 'off_b', 'ablate'))
        if s == 'CONFIRMED' and not others: flag.setdefault(l['focal_item'], []).append(sid)
        elif s == 'NONE': none.setdefault(l['focal_item'], []).append(sid)
        elif s == 'PENDING': pend += 1
    out = {}
    for f, ids in flag.items():
        l = L[ids[0]]; sens = l['focal_level'] == 'HIGH' and int(l['harm_severity']) >= 2
        out[f] = dict(flag=sorted(ids), quiet=sorted(none.get(f, [])), tier='SENSITIVE' if sens else 'EVERYDAY', theme=l['theme'])
    return out, dict(pending=pend, scenarios_with_memory_run=sum(1 for a in st.values() if 'memory' in a))
def select(flags, max_facts=MAX_FACTS):
    """Deterministic cap: theme by theme in turn, within a theme by a fixed hash of the fact id."""
    if len(flags) <= max_facts: return sorted(flags)
    by = {}
    for f in sorted(flags): by.setdefault(flags[f]['theme'], []).append(f)
    for t in by: by[t].sort(key=lambda f: hv('sel', f))
    out = []; themes = sorted(by)
    while len(out) < max_facts and any(by[t] for t in themes):
        for t in themes:
            if by[t] and len(out) < max_facts: out.append(by[t].pop(0))
    return sorted(out)
def sibling(fact, flags, L, T, C):
    """A fresh task: touches the fact's theme, its reader does not already hold the theme or the fact's group, no figure to fill in, never used for this fact in Study 2. Prefers the reader class of the flagged task; ties broken by a fixed hash."""
    rows = [r for r in L if r['focal_item'] == fact]; used = {r['task_id'] for r in rows}; fl = flags[fact]; first = next(r for r in rows if r['id'] == fl['flag'][0]); code = C[fl['theme']]; grp = first['group']
    cand = [t for t in T.values() if code in (t['touches'].split(',')) and code not in t['holds_already'].split(',') and grp not in t['holds_already'].split(',') and '«figure»' not in t['task'] and t['task_id'] not in used]
    cand.sort(key=lambda t: (t['reader_class'] != first['reader_class'], hv('sib', fact, t['task_id'])))
    return cand[0] if cand else None
def build(flags, facts, L, T, C, R=None):
    """Stores, facts per store, checkbook rows and the per-fact record, from the selected facts."""
    R = R or rules(); LI = {r['id']: r for r in L}
    order = sorted(facts, key=lambda f: (flags[f]['theme'], hv('asg', f))); where = {}
    for k, f in enumerate(order):
        a, b = k % 3, (k // 3) % 3
        where[f] = [(P_LEVELS[(a + r) % 3], W_LEVELS[(b + r) % 3]) for r in range(3)]      # repeat r+1: a diagonal, so P and W each appear once
    stores = []; fb = []; ck = []; rec = []
    sib = {f: sibling(f, flags, L, T, C) for f in facts}
    for f in facts:
        q = sorted(flags[f]['quiet'], key=lambda s: hv('ctl', f, s))
        rec.append(dict(fact_id=f, theme=flags[f]['theme'], tier=flags[f]['tier'], n_flagged=len(flags[f]['flag']), same=' '.join(flags[f]['flag'][:MAX_SAME]), unflagged=q[0] if q else '', sibling_task=sib[f]['task_id'] if sib[f] else '', sibling_reader=sib[f]['reader'] if sib[f] else '',
                       cells=' '.join(f'R{r + 1}:P{p}W{w}' for r, (p, w) in enumerate(where[f]))))
    for r in (1, 2, 3):
        for p in P_LEVELS:
            for w in W_LEVELS:
                sid = f'P1-R{r}-P{p}W{w}'; mem = [f for f in facts if where[f][r - 1] == (p, w)]
                stores.append(dict(store_id=sid, replicate=r, cell=f'P{p}W{w}', p=p, w=w, n_facts=len(mem), rule_id=REPEAT_RULE[r], rule_in_store='', p_actual='', w_actual='', items_after_seed='', items_before_test='', elapsed_h=''))
                first, last = [], []
                for f in sorted(mem):
                    fb.append(dict(store_id=sid, fact_id=f)); m_ = lambda f=f: 'NONE' if REPEAT_RULE[r] == 'NONE' else ('SAME' if flags[f]['theme'] in R[REPEAT_RULE[r]] else 'OTHER')
                    base = dict(store_id=sid, fact_id=f, rule_id=REPEAT_RULE[r], rule_match=m_(), fact_in_store='', store_changed='', response='', result='', note='')
                    for s in flags[f]['flag'][:MAX_SAME]: first.append(dict(base, run_id=f'{sid}:{f}:same:{s}', kind='same', scenario_id=s, task_id=LI[s]['task_id']))
                    q = sorted(flags[f]['quiet'], key=lambda s: hv('ctl', f, s))
                    if q: first.append(dict(base, run_id=f'{sid}:{f}:unflagged:{q[0]}', kind='unflagged', scenario_id=q[0], task_id=LI[q[0]]['task_id']))
                    if sib[f]: last.append(dict(base, run_id=f'{sid}:{f}:sibling:{sib[f]["task_id"]}', kind='sibling', scenario_id='SB-' + f, task_id=sib[f]['task_id']))
                first.sort(key=lambda x: hv('ord', sid, x['run_id'])); last.sort(key=lambda x: hv('ord', sid, x['run_id']))
                for i, x in enumerate(first + last, 1): x['run_order'] = i
                ck += first + last
    return stores, fb, ck, rec
COLS = dict(stores=['store_id', 'replicate', 'cell', 'p', 'w', 'n_facts', 'rule_id', 'rule_in_store', 'p_actual', 'w_actual', 'items_after_seed', 'items_before_test', 'elapsed_h'], fb=['store_id', 'fact_id'],
            ck=['run_id', 'store_id', 'run_order', 'fact_id', 'kind', 'scenario_id', 'task_id', 'rule_id', 'rule_match', 'fact_in_store', 'store_changed', 'response', 'result', 'note'],
            rec=['fact_id', 'theme', 'tier', 'n_flagged', 'same', 'unflagged', 'sibling_task', 'sibling_reader', 'cells'])
def write(out, stores, fb, ck, rec, summary):
    os.makedirs(out, exist_ok=True)
    for name, rows, k in (('stores.csv', stores, 'stores'), ('facts_by_store.csv', fb, 'fb'), ('checkbook.csv', ck, 'ck'), ('flagged.csv', rec, 'rec')):
        with open(os.path.join(out, name), 'w', newline='', encoding='utf-8') as fh: w = csv.DictWriter(fh, COLS[k]); w.writeheader(); w.writerows(rows)
    open(os.path.join(out, 'plan_summary.md'), 'w', encoding='utf-8').write(summary)
def make(sheet, out, allow_small=False, force=False):
    L, T, C = lib(); flags, info = flagged(sheet)
    if not flags or (len(flags) < MIN_FACTS and not allow_small):
        msg = f'NOT RUN: {len(flags)} facts have a flagged pair; Study 3 needs at least {MIN_FACTS}. Study 2 found too little firing to follow over a delay (that is itself a result; Study 2 pending-human-check runs: {info["pending"]}).'
        print(msg); return None, msg
    if os.path.exists(os.path.join(out, 'checkbook.csv')) and not force: raise SystemExit('REFUSED: ' + out + ' already holds a plan. A plan is generated once from the Study 2 results. Use --force only if you mean to regenerate it, and record why.')
    facts = select(flags); stores, fb, ck, rec = build(flags, facts, L, T, C)
    th = {}
    for f in facts: th[flags[f]['theme']] = th.get(flags[f]['theme'], 0) + 1
    kinds = {k: sum(1 for c in ck if c['kind'] == k) for k in ('same', 'unflagged', 'sibling')}
    summ = ['# Study 3 plan summary', '', f'Study 2 runs read: {info["scenarios_with_memory_run"]} scenarios with a memory-arm run. Pairs still pending a human check (not flagged): {info["pending"]}.',
            f'Facts with a flagged pair: {len(flags)}; selected for Study 3: {len(facts)} (cap {MAX_FACTS}). Sensitive facts {sum(1 for f in facts if flags[f]["tier"] == "SENSITIVE")}, everyday facts {sum(1 for f in facts if flags[f]["tier"] == "EVERYDAY")}.',
            f'Runs after the delay: {len(ck)} = {kinds["same"]} same + {kinds["unflagged"]} unflagged + {kinds["sibling"]} sibling, over {len(stores)} stores. Facts with no sibling task: {sum(1 for r in rec if not r["sibling_task"])}; facts with no unflagged control: {sum(1 for r in rec if not r["unflagged"])}.',
            '', '| theme | facts |', '|---|---|'] + [f'| {t} | {n} |' for t, n in sorted(th.items())] + ['']
    write(out, stores, fb, ck, rec, '\n'.join(summ)); print('\n'.join(summ)); return dict(facts=facts, stores=stores, fb=fb, ck=ck, rec=rec), ''
if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0].startswith('--'): print(__doc__); sys.exit(1)
    out = a[a.index('--out') + 1] if '--out' in a else os.path.join(HERE, 'plan')
    r, msg = make(a[0], out, '--allow-small' in a, '--force' in a); sys.exit(0 if r else 3)
