"""Read and write the markdown tables that hold the data libraries (facts, lures). A literal pipe inside a cell is written \\| ."""
import re
def _split(line):
    cells = re.split(r'(?<!\\)\|', line.strip()); cells = cells[1:-1]
    return [c.strip().replace('\\|', '|') for c in cells]
def read(path, section=None):
    """Rows of the first table (or the first table after the heading line that starts with `section`) as a list of dicts."""
    lines = open(path, encoding='utf-8').read().split('\n'); i = 0
    if section:
        while not (lines[i].startswith('#') and lines[i].lstrip('# ').startswith(section)): i += 1
    while not lines[i].startswith('|'): i += 1
    head = _split(lines[i]); i += 2; rows = []
    while i < len(lines) and lines[i].startswith('|'):
        v = _split(lines[i]); rows.append(dict(zip(head, v + [''] * (len(head) - len(v))))); i += 1
    return rows
def table(rows, cols):
    esc = lambda x: str(x).replace('|', '\\|').replace('\n', ' ')
    return '\n'.join(['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)] + ['| ' + ' | '.join(esc(r[c]) for c in cols) + ' |' for r in rows]) + '\n'
