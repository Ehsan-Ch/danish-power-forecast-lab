import unittest
from datetime import timedelta
import numpy as np
from nordcast.data import midnight,STEP,decision,available,DK
from nordcast.features import matrix,NAMES
from nordcast.models import correction,metrics,ordered,ForecastModels

class FeatureModelTests(unittest.TestCase):
    def sample(self):
        start=midnight('2026-03-01');times=[start+i*STEP for i in range(35*96)]
        return {a:{t:float(i%300+(0 if a=='DK1' else 5)) for i,t in enumerate(times)} for a in ('DK1','DK2')}
    def test_future_mutation_cannot_change_issued_features(self):
        values=self.sample();initial=matrix(values,'DK1');cut=decision('2026-03-29')
        changed={a:{t:(v+10000 if available(t)>cut else v) for t,v in s.items()} for a,s in values.items()}
        after=matrix(changed,'DK1');take=[t.astimezone(DK).date().isoformat()=='2026-03-29' for t in initial['times']]
        np.testing.assert_array_equal(initial['X'][take],after['X'][take]);self.assertEqual(sum(take),92)
        self.assertEqual(initial['X'].shape[1],len(NAMES))
    def test_lags_and_statistics_have_exact_values(self):
        values=self.sample();m=matrix(values,'DK1');t=m['times'][0]
        self.assertEqual(m['X'][0,0],values['DK1'][t-timedelta(hours=72)])
        self.assertEqual(m['weekly'][0],values['DK1'][t-timedelta(hours=168)])
        window=[values['DK1'][t-timedelta(hours=72)-i*STEP] for i in range(96)]
        self.assertAlmostEqual(m['X'][0,8],np.mean(window))
    def test_calibration_finite_sample_rank(self):
        self.assertEqual(correction(range(10)),8)
        with self.assertRaises(ValueError):correction([1])
    def test_crossings_sorted_and_scores(self):
        np.testing.assert_array_equal(ordered([[3,1,2]]),[[1,2,3]])
        m=metrics([0,10],np.array([[-1,1,2],[3,4,5]]))
        self.assertEqual(m['mae'],3.5);self.assertEqual(m['coverage'],.5);self.assertEqual(m['interval_score'],27.5)
        self.assertIsNone(metrics([],np.empty((0,3))))
    def test_fit_calibrate_predict_without_refit(self):
        rng=np.random.default_rng(42);x=rng.normal(size=(400,4));y=x[:,0]*10+rng.normal(size=400)
        model=ForecastModels().fit(x[:200],y[:200]);before=model.ridge.predict(x[350:]).copy()
        model.calibrate(x[200:350],y[200:350],x[200:350,0]);p=model.predict(x[350:],x[350:,0])
        np.testing.assert_array_equal(before,model.ridge.predict(x[350:]))
        for v in p.values():self.assertTrue(np.all(v[:,0]<=v[:,1]));self.assertTrue(np.all(v[:,1]<=v[:,2]))
