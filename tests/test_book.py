import sqlite3
import unittest
from datetime import timedelta
from nordcast.book import Book,schedule,ENERGY
from nordcast.data import day_slots,decision,available,stamp

class BookTests(unittest.TestCase):
    def setUp(self):self.book=Book(':memory:');self.times=day_slots('2026-07-01');self.at=decision('2026-07-01')
    def tearDown(self):self.book.close()
    def propose(self,batch='x',upper=10):
        self.book.propose(batch,'DK1','2026-07-01','upper',self.times,schedule([1.]*96),[upper]*96,self.at)
    def test_schedule_conserves_energy_and_power(self):
        for n in (92,96,100):
            q=schedule(list(range(n)));self.assertAlmostEqual(sum(q),4);self.assertLessEqual(max(q),.25);self.assertEqual(sum(x>0 for x in q),16)
        with self.assertRaises(ValueError):schedule([1]*4)
    def test_lifecycle_negative_cost_and_duplicate_settlement(self):
        self.propose();self.assertEqual(self.book.transition('x',self.at,'APPROVED'),'APPROVED')
        cost=self.book.settle('x',{stamp(t):-10. for t in self.times},available(self.times[-1]))
        self.assertEqual(cost,-38.)
        with self.assertRaises(ValueError):self.book.settle('x',{},available(self.times[-1]))
        self.assertEqual([e['state'] for e in self.book.export()['events']],['PROPOSED','APPROVED','SETTLED'])
    def test_budget_rejection_and_cancellation(self):
        self.propose(upper=300);self.assertEqual(self.book.transition('x',self.at,'APPROVED'),'REJECTED')
        with self.assertRaises(ValueError):self.book.settle('x',{},available(self.times[-1]))
        self.propose('y');self.book.transition('y',self.at,'CANCELLED')
        with self.assertRaises(ValueError):self.book.transition('y',self.at,'APPROVED')
    def test_duplicate_proposal_rolls_back(self):
        self.propose()
        with self.assertRaises(sqlite3.IntegrityError):self.propose()
        self.assertEqual(len(self.book.export()['orders']),16)
    def test_missing_price_settlement_atomic(self):
        self.propose();self.book.transition('x',self.at,'APPROVED')
        with self.assertRaises(ValueError):self.book.settle('x',{stamp(self.times[0]):1.},available(self.times[-1]))
        self.assertTrue(all(o['cost'] is None for o in self.book.export()['orders']))
        self.assertEqual(self.book.export()['batches'][0]['status'],'APPROVED')
    def test_future_settlement_and_late_approval_rejected(self):
        self.propose()
        with self.assertRaises(ValueError):self.book.transition('x',self.times[0],'APPROVED')
        self.book.transition('x',self.at,'APPROVED')
        with self.assertRaises(ValueError):self.book.settle('x',{stamp(t):1. for t in self.times},self.at)
