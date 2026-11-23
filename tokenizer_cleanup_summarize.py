"""Summarize matrix artifacts produced by tokenizer-cleanup-check.yml (stdlib only)."""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'matrix-artifacts')
rows = []
versions = {}
for file in sorted(root.rglob('results.jsonl')):
    for line in file.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        vers = record.get('matrix_version', '')
        if record.get('status') != 'ok':
            rows.append({'version': vers,'model': record.get('model','<environment>'),
                         'status': record.get('status'), 'error':record.get('error',''),
                         'detail':record.get('detail','')})
            continue
        for c in record['cases']:
            rows.append({
                'version':vers, 'model':record['model'], 'revision':record.get('revision',''),
                'status':c.get('status','ok'), 'error':c.get('error',''),
                'config_present':record.get('config_field_present'),
                'config_value':record.get('config_field_value'),
                'effective_cleanup':record.get('effective_cleanup'),
                'class':record.get('tokenizer_class'), 'is_fast':record.get('is_fast'),
                'input':c.get('raw'), 'decoded_default':c.get('default'),
                'decoded_true':c.get('cleanup_true'), 'decoded_false':c.get('cleanup_false'),
                'cleanup_matters':c.get('effect_from_cleanup'),
                'default_equals_input':c.get('default_equals_raw'),
            })
        versions[vers] = True

out = Path('tokenizer-cleanup-matrix.csv')
fields = ['version','model','revision','status','error','detail','config_present',
          'config_value','effective_cleanup','class','is_fast','input',
          'decoded_default','decoded_true','decoded_false','cleanup_matters','default_equals_input']
with out.open('w',newline='',encoding='utf-8') as f:
    w = csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
print('Results files:', len(list(root.rglob('results.jsonl'))))
print('Rows:',len(rows))
print('Versions with valid model results:',', '.join(sorted(versions)))
for r in rows:
    if r['status']=='ok' and r.get('cleanup_matters'):
        print(f"DELTA version={r['version']} model={r['model']} input={r['input']!r} "
              f"default={r['decoded_default']!r} true={r['decoded_true']!r} false={r['decoded_false']!r}")
    elif r['status']!='ok':
        print(f"ERROR version={r['version']} model={r['model']} error={r['error']}")
print('CSV:',out)
