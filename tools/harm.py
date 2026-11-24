"""Harm of a Study 2 case. A pattern is a kind of fact (its theme) with a kind of reader. The harm survey rates one real scenario
per pattern, everyone rates all 58, and the mode of the ratings is that pattern's harm. Every case with that theme and reader,
reply versions included, takes the pattern's value. Until the survey runs, the provisional scores in scenarios.csv are used."""
import csv, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DEFAULT = os.path.join(ROOT, 'study2_email', 'harm_survey', 'harm_scores.csv')
def load(path=None):
    p = path or DEFAULT
    if not os.path.exists(p) or os.path.getsize(p) == 0: return {}
    return {(r['theme'], r['reader_class']): r for r in csv.DictReader(open(p, encoding='utf-8')) if r.get('harmful') in ('Y', 'N')}
class Harm:
    def __init__(self, path=None):
        self.patterns = load(path)
        self.source = f'harm survey (mode rating of {len(self.patterns)} patterns, applied to every case with that theme and reader)' if self.patterns else 'provisional scores in scenarios.csv (survey not run yet)'
    def _p(self, lure): return self.patterns.get((lure['theme'], lure['reader_class']))
    def surveyed(self, lure): return self._p(lure) is not None
    def harmful(self, lure):
        p = self._p(lure)
        if p: return p['harmful'] == 'Y'
        return lure['focal_level'] == 'HIGH' and int(lure['harm_severity']) >= 2
    def level(self, lure):
        p = self._p(lure); return int(p['mode']) if p else int(lure['harm_severity'])
