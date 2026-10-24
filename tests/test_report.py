import csv
import gzip
import hashlib
import json
import unittest
from pathlib import Path
import numpy as np
from nordcast.data import parse,available,day_slots,decision
from nordcast.models import metrics

ROOT=Path(__file__).resolve().parents[1]
class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=json.loads((ROOT/'reports/benchmark/results.json').read_text(encoding='utf-8'))
    def test_scope_and_source_audit(self):
        r=self.report;self.assertEqual(r['data_quality']['records'],70080);self.assertEqual(r['data_quality']['dst_day_quarters'],{'2025-10-26':100,'2026-03-29':92})
        self.assertEqual(r['protocol_sha256'],hashlib.sha256((ROOT/'docs/PROTOCOL.md').read_bytes()).hexdigest())
        for f in r['folds']:
            self.assertLessEqual(parse(f['max_label_available']),parse(f['issue']));self.assertGreaterEqual(f['min_feature_margin_hours'],0)
    def test_selection_comes_from_validation(self):
        for area,models in self.report['validation'].items():self.assertEqual(self.report['selection'][area],min(models,key=lambda name:models[name]['mae']))
    def test_metrics_recomputed_from_published_predictions(self):
        for area,r in self.report['areas'].items():
            self.assertEqual(len(r['days']),92);self.assertEqual(r['days'][0]['date'],'2026-07-01');self.assertEqual(r['days'][-1]['date'],'2026-09-30')
            y=np.concatenate([d['actual'] for d in r['days']])
            for name,expected in r['metrics'].items():
                p=np.concatenate([d['predictions'][name] for d in r['days']]);actual=metrics(y,p)
                for key,value in actual.items():self.assertAlmostEqual(value,expected[key],places=4)
    def test_energy_cost_and_hindsight_lower_bound(self):
        for r in self.report['areas'].values():
            for d in r['days']:
                self.assertEqual([parse(t) for t in d['times']],day_slots(d['date']));self.assertEqual(parse(d['issue']),decision(d['date']))
                self.assertAlmostEqual(d['uniform_cost'],4*(np.mean(d['actual'])+.5),places=4)
                for p in d['policies'].values():
                    self.assertAlmostEqual(sum(p['quantities']),4);self.assertLessEqual(max(p['quantities']),.25)
                    if p['status']=='SETTLED':self.assertAlmostEqual(p['cost'],np.dot(p['quantities'],np.array(d['actual'])+.5),places=4)
                    self.assertGreaterEqual(p['cost']+1e-4,d['oracle_cost']);self.assertAlmostEqual(p['savings_vs_uniform'],d['uniform_cost']-p['cost'],places=4)
    def test_full_csv_and_order_audit(self):
        with gzip.open(ROOT/'reports/benchmark/predictions.csv.gz','rt',encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),(92+27)*96*2*3)
        self.assertEqual(len({(r['area'],r['delivery_utc'],r['model']) for r in rows}),len(rows))
        with (ROOT/'reports/benchmark/orders.csv').open(encoding='utf-8',newline='') as f:orders=list(csv.DictReader(f))
        with (ROOT/'reports/benchmark/events.csv').open(encoding='utf-8',newline='') as f:events=list(csv.DictReader(f))
        self.assertEqual(len(orders),92*2*2*16)
        for e in events:
            if e['state']=='SETTLED':
                day=e['batch'].split('/')[1];self.assertGreaterEqual(parse(e['at']),available(day_slots(day)[-1]))
