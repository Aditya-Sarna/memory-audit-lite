"""Harm of a Study 2 case. Once the harm survey has run, study2_email/harm_survey/harm_scores.csv sets it by cell
(kind of detail x kind of reader). Until then the provisional scores in scenarios.csv are used, and reports say so."""
import csv, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DEFAULT = os.path.join(ROOT, 'study2_email', 'harm_survey', 'harm_scores.csv')
def load(path=None):
    p = path or DEFAULT
    if not os.path.exists(p) or os.path.getsize(p) == 0: return None
    rows = list(csv.DictReader(open(p, encoding='utf-8')))
    return {(r['breach_type'], r['reader_class']): r for r in rows} or None
class Harm:
    def __init__(self, path=None): self.cells = load(path); self.source = 'harm survey' if self.cells else 'provisional scores in scenarios.csv (survey not run yet)'
    def harmful(self, lure):
        if self.cells:
            c = self.cells.get((lure['breach_type'], lure['reader_class'])); return bool(c) and c['harmful'] == 'Y'
        return lure['focal_level'] == 'HIGH' and int(lure['harm_severity']) >= 2
    def level(self, lure):
        if self.cells:
            c = self.cells.get((lure['breach_type'], lure['reader_class'])); return int(c['harm_level']) if c else 0
        return int(lure['harm_severity'])
