import unittest
from datetime import date,timedelta
from nordcast.data import day_slots,decision,available,validate,stamp
from nordcast.pipeline import bounds

class TimeDataTests(unittest.TestCase):
    def test_short_long_and_normal_days(self):
        for d,n in [('2026-03-29',92),('2025-10-26',100),('2026-07-01',96)]:
            slots=day_slots(d);self.assertEqual(len(slots),n);self.assertEqual(len(set(slots)),n)
    def test_decisions_use_local_clock(self):
        self.assertEqual(decision('2026-07-01').hour,8)
        self.assertEqual(decision('2026-01-01').hour,9)
    def test_fold_labels_mature_before_fit(self):
        for month in (6,7,8,9):
            first=date(2026,month,1);fit,cal,end=bounds(first)
            self.assertLess(fit,cal);self.assertLess(cal,end)
            self.assertLessEqual(available(end-timedelta(minutes=15)),decision(first))
    def test_validation_labels_mature_before_selection(self):
        self.assertLessEqual(available(day_slots('2026-06-27')[-1]),decision('2026-07-01'))
    def records(self):
        return [{'PriceArea':a,'TimeUTC':stamp(t),'DayAheadPriceEUR':-10.} for a in ('DK1','DK2') for t in day_slots('2026-03-29')]
    def test_validation_keeps_negative_prices(self):
        v=validate(self.records(),'2026-03-29','2026-03-30');self.assertEqual(len(v['DK1']),92);self.assertEqual(min(v['DK2'].values()),-10)
    def test_missing_duplicate_nonfinite_rejected(self):
        rows=self.records()
        for bad in (rows[:-1],rows+[rows[0]],rows[:-1]+[{**rows[-1],'DayAheadPriceEUR':float('nan')}],rows[:-1]+[{**rows[-1],'TimeUTC':'2026-03-29T21:46:00Z'}]):
            with self.assertRaises(ValueError):validate(bad,'2026-03-29','2026-03-30')
