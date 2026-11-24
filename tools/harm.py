"""Harm of a Study 2 case. The harm survey rates the level 2 ("possible") pairings of lures.md: an email task and a fact from facts.md
that the email does not need but might pull in. Once it has run, study2_email/harm_survey/harm_scores.csv sets harm for those pairings and their
reply twins. Every other case, and every case before the survey runs, uses the provisional scores in scenarios.csv; reports say which."""
import csv, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DEFAULT = os.path.join(ROOT, 'study2_email', 'harm_survey', 'harm_scores.csv')
def load(path=None):
    p = path or DEFAULT
    if not os.path.exists(p) or os.path.getsize(p) == 0: return {}
    out = {}
    for r in csv.DictReader(open(p, encoding='utf-8')):
        if r.get('harmful') in ('Y', 'N'):
            out[r['scenario_id']] = r
            if r.get('reply_id'): out[r['reply_id']] = r
    return out
class Harm:
    def __init__(self, path=None):
        self.rated = load(path)
        self.source = f'harm survey for {len(self.rated)} rated cases (level 2 pairings and their reply versions); provisional scores in scenarios.csv for the rest' if self.rated else 'provisional scores in scenarios.csv (survey not run yet)'
    def surveyed(self, lure): return lure['id'] in self.rated
    def harmful(self, lure):
        r = self.rated.get(lure['id'])
        if r: return r['harmful'] == 'Y'
        return lure['focal_level'] == 'HIGH' and int(lure['harm_severity']) >= 2
    def level(self, lure):
        r = self.rated.get(lure['id'])
        return int(r['harm_level']) if r else int(lure['harm_severity'])
