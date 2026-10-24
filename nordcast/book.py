"""A local paper procurement ledger; no exchange adapter or live orders."""
import json
import math
import sqlite3
from .data import parse,available,stamp,day_slots

ENERGY=4.
MAX_MW=1.
FEE=.5
BUDGET=1000.

def schedule(scores,energy=ENERGY,max_mw=MAX_MW):
    if not math.isfinite(energy) or not math.isfinite(max_mw) or energy<=0 or max_mw<=0:raise ValueError('Invalid energy/power')
    if not scores or not all(math.isfinite(float(s)) for s in scores):raise ValueError('Invalid scores')
    capacity=max_mw*.25
    if energy>len(scores)*capacity+1e-9:raise ValueError('Infeasible energy requirement')
    quantities=[0.]*len(scores);remaining=energy
    for i in sorted(range(len(scores)),key=lambda i:(scores[i],i)):
        quantities[i]=min(capacity,remaining);remaining-=quantities[i]
        if remaining<1e-10:break
    return quantities

class Book:
    def __init__(self,path):
        self.db=sqlite3.connect(path)
        self.db.row_factory=sqlite3.Row
        self.db.executescript('''CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY, area TEXT, day TEXT, policy TEXT, status TEXT, decision TEXT, gross REAL, reason TEXT);
        CREATE TABLE IF NOT EXISTS orders(batch TEXT, delivery TEXT, mwh REAL, upper REAL, actual REAL, cost REAL, PRIMARY KEY(batch,delivery));
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,batch TEXT,at TEXT,state TEXT,details TEXT);''')
    def close(self):self.db.close()
    def event(self,batch,at,state,details):self.db.execute('INSERT INTO events(batch,at,state,details) VALUES(?,?,?,?)',(batch,stamp(at),state,details))
    def propose(self,batch,area,day,policy,times,quantities,upper,at):
        if area not in ('DK1','DK2') or len(times)!=len(quantities) or len(times)!=len(upper) or not times or len(set(times))!=len(times):raise ValueError('Invalid order shape')
        if times!=day_slots(day):raise ValueError('Expected a complete local delivery day')
        if any(not math.isfinite(float(v)) for v in [*quantities,*upper]) or any(q<0 or q>MAX_MW*.25+1e-9 for q in quantities) or abs(sum(quantities)-ENERGY)>1e-8:raise ValueError('Energy or power limit')
        if at>=min(times):raise ValueError('Proposal must precede delivery')
        gross=sum(q*(abs(p)+FEE) for q,p in zip(quantities,upper))
        with self.db:
            self.db.execute('INSERT INTO batches VALUES(?,?,?,?,?,?,?,?)',(batch,area,day,policy,'PROPOSED',stamp(at),gross,''))
            self.db.executemany('INSERT INTO orders VALUES(?,?,?,?,NULL,NULL)',[(batch,stamp(t),q,u) for t,q,u in zip(times,quantities,upper) if q>0])
            self.event(batch,at,'PROPOSED','Energy-conserving paper purchase schedule')
    def transition(self,batch,at,desired,budget=BUDGET):
        if not math.isfinite(budget) or budget<0:raise ValueError('Invalid budget')
        with self.db:
            row=self.db.execute('SELECT * FROM batches WHERE id=?',(batch,)).fetchone()
            if row is None:raise ValueError('Unknown batch')
            if at<parse(row['decision']):raise ValueError('Event before decision')
            last=self.db.execute('SELECT at FROM events WHERE batch=? ORDER BY id DESC LIMIT 1',(batch,)).fetchone()
            if at<parse(last['at']):raise ValueError('Out-of-order event')
            if at>=day_slots(row['day'])[0]:raise ValueError('Approval/cancellation must precede delivery')
            if desired=='APPROVED' and row['status']=='PROPOSED':
                state='APPROVED' if row['gross']<=budget else 'REJECTED';reason='Within forecast budget' if state=='APPROVED' else 'Forecast gross budget exceeded'
            elif desired=='CANCELLED' and row['status'] in ('PROPOSED','APPROVED'):state='CANCELLED';reason='Cancelled before settlement'
            else:raise ValueError('Invalid lifecycle transition')
            self.db.execute('UPDATE batches SET status=?,reason=? WHERE id=?',(state,reason,batch));self.event(batch,at,state,reason)
        return state
    def settle(self,batch,prices,at):
        with self.db:
            row=self.db.execute('SELECT status FROM batches WHERE id=?',(batch,)).fetchone()
            if row is None or row['status']!='APPROVED':raise ValueError('Only approved batches settle once')
            orders=self.db.execute('SELECT * FROM orders WHERE batch=?',(batch,)).fetchall()
            for o in orders:
                if available(parse(o['delivery']))>at:raise ValueError('Settlement price unavailable')
                if o['delivery'] not in prices or not math.isfinite(prices[o['delivery']]):raise ValueError('Missing settlement price')
            for o in orders:
                price=prices[o['delivery']];self.db.execute('UPDATE orders SET actual=?,cost=? WHERE batch=? AND delivery=?',(price,o['mwh']*(price+FEE),batch,o['delivery']))
            self.db.execute("UPDATE batches SET status='SETTLED' WHERE id=?",(batch,));self.event(batch,at,'SETTLED','Assumed full fill at clearing price plus fee')
        return sum(o['mwh']*(prices[o['delivery']]+FEE) for o in orders)
    def export(self):
        return {table:[dict(r) for r in self.db.execute('SELECT * FROM '+table)] for table in ('batches','orders','events')}
