"""Chronological monthly refits; choose on June, evaluate on July–September."""
import csv
import gzip
import hashlib
import json
import platform
from datetime import date,datetime,timedelta
from pathlib import Path
import numpy as np
import sklearn
from .data import DK,UTC,available,decision,load,midnight,stamp
from .features import matrix,NAMES
from .models import ForecastModels,MODELS,HYPERPARAMETERS,metrics
from .book import Book,schedule,ENERGY,FEE,BUDGET

def bounds(first):
    cal_end=first-timedelta(days=2);cal_start=cal_end-timedelta(days=28);fit_start=cal_start-timedelta(days=120)
    return midnight(fit_start),midnight(cal_start),midnight(cal_end)

def mask(times,start,end):return np.array([start<=t<end for t in times])
def safe(value):
    if isinstance(value,dict):return {str(k):safe(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [safe(v) for v in value]
    if isinstance(value,np.ndarray):return safe(value.tolist())
    if isinstance(value,(float,np.floating)):
        if not np.isfinite(value):raise ValueError('Nonfinite report')
        return round(float(value),6)
    if isinstance(value,np.integer):return int(value)
    return value

def run(cache,out):
    out=Path(out)
    if out.exists() and any(out.iterdir()):raise ValueError('Use an empty output directory')
    out.mkdir(parents=True,exist_ok=True)
    values,source=load(cache)
    matrices={area:matrix(values,area) for area in ('DK1','DK2')}
    report={'title':'Nordcast','built_utc':stamp(datetime.now(UTC)),'source':source,'features':NAMES,
            'versions':{'python':platform.python_version(),'numpy':np.__version__,'sklearn':sklearn.__version__},
            'parameters':{'ridge_alpha':10,'boosted':HYPERPARAMETERS,'nominal_coverage':.8,'energy_mwh':ENERGY,'max_mw':1,'fee_eur_mwh':FEE,'forecast_gross_budget_eur':BUDGET},
            'data_quality':{'records':sum(len(v) for v in values.values()),'quarters_per_area':len(values['DK1']),'duplicates':0,'missing':0,'negative_prices':{a:sum(v<0 for v in series.values()) for a,series in values.items()},'dst_day_quarters':{d:sum(t.astimezone(DK).date().isoformat()==d for t in values['DK1']) for d in ('2025-10-26','2026-03-29')}},
            'validation':{},'selection':{},'folds':[],'areas':{}}
    protocol=Path(__file__).resolve().parents[1]/'docs/PROTOCOL.md'
    report['protocol_sha256']=hashlib.sha256(protocol.read_bytes()).hexdigest()
    predictions=[];book=Book(out/'paper.sqlite')
    for month in (6,7,8,9):
        first=date(2026,month,1);end=date(2026,month+1,1) if month<9 else date(2026,10,1)
        if month==6:end=date(2026,6,28)
        fit_start,cal_start,cal_end=bounds(first);cutoff=decision(first)
        for area,m in matrices.items():
            times=m['times'];fit=mask(times,fit_start,cal_start);cal=mask(times,cal_start,cal_end);test=mask(times,midnight(first),midnight(end))
            if not fit.any() or not cal.any() or not test.any() or np.any(fit&cal) or np.any(cal&test):raise ValueError('Invalid time split')
            cal_times=[t for t,b in zip(times,cal) if b];fit_times=[t for t,b in zip(times,fit) if b]
            if max(available(t) for t in cal_times+fit_times)>cutoff:raise ValueError('Training/calibration labels unavailable')
            model=ForecastModels().fit(m['X'][fit],m['y'][fit]).calibrate(m['X'][cal],m['y'][cal],m['weekly'][cal])
            result=model.predict(m['X'][test],m['weekly'][test]);target=[t for t,b in zip(times,test) if b];y=m['y'][test]
            fold_id=f'{area}-{first}'
            report['folds'].append({'id':fold_id,'area':area,'first_delivery':str(first),'issue':stamp(cutoff),'fit_start':stamp(fit_start),'fit_end_exclusive':stamp(cal_start),'calibration_end_exclusive':stamp(cal_end),'fit_rows':int(fit.sum()),'calibration_rows':int(cal.sum()),'max_label_available':stamp(max(available(t) for t in cal_times)), 'min_feature_margin_hours':m['minimum_feature_availability_margin_hours'],'corrections':model.offsets})
            scores={name:metrics(y,p) for name,p in result.items()}
            if month==6:
                report['validation'][area]=scores
                report['selection'][area]=min(MODELS,key=lambda name:scores[name]['mae'])
            else:
                record=report['areas'].setdefault(area,{'days':[],'monthly':[]})
                record['monthly'].append({'month':str(first)[:7],'models':scores})
                days=sorted({t.astimezone(DK).date() for t in target})
                for day in days:
                    take=np.array([t.astimezone(DK).date()==day for t in target]);dt=[t for t,b in zip(target,take) if b];actual=y[take]
                    preds={name:p[take] for name,p in result.items()};chosen=preds[report['selection'][area]]
                    uniform=float(ENERGY*(actual.mean()+FEE));oracle_q=schedule(actual.tolist());oracle=float(np.dot(oracle_q,actual+FEE))
                    policies={}
                    for policy,column in (('median',1),('upper',2)):
                        quantities=schedule(chosen[:,column].tolist());batch=f'{area}/{day}/{policy}';at=decision(day)
                        book.propose(batch,area,str(day),policy,dt,quantities,chosen[:,2].tolist(),at)
                        state=book.transition(batch,at,'APPROVED')
                        if state=='APPROVED':
                            cost=book.settle(batch,{stamp(t):float(v) for t,v in zip(dt,actual)},max(available(t) for t in dt));status='SETTLED'
                        else:cost=uniform;status=state
                        policies[policy]={'batch':batch,'quantities':quantities,'status':status,'cost':cost,'savings_vs_uniform':uniform-cost,'regret_vs_oracle':cost-oracle}
                    record['days'].append({'date':str(day),'issue':stamp(decision(day)),'fold':fold_id,'times':[stamp(t) for t in dt],
                        'local_labels':[t.astimezone(DK).strftime('%H:%M %z') for t in dt],'actual':actual,'predictions':preds,'uniform_cost':uniform,'oracle_cost':oracle,'policies':policies})
            for i,t in enumerate(target):
                for name,p in result.items():predictions.append({'area':area,'partition':'validation' if month==6 else 'test','delivery_utc':stamp(t),'delivery_local':t.astimezone(DK).isoformat(),'issue_utc':stamp(decision(t.astimezone(DK).date())),'model':name,'fold':fold_id,'actual':float(y[i]),'lower':float(p[i,0]),'forecast':float(p[i,1]),'upper':float(p[i,2])})
            print(f'{fold_id}: '+', '.join(f'{name} MAE {s["mae"]:.2f}' for name,s in scores.items()),flush=True)
    for area,record in report['areas'].items():
        y=np.concatenate([d['actual'] for d in record['days']]);ps={name:np.concatenate([d['predictions'][name] for d in record['days']]) for name in MODELS}
        record['metrics']={name:metrics(y,p) for name,p in ps.items()};base=record['metrics']['weekly']['mae']
        for v in record['metrics'].values():v['mae_skill_vs_weekly']=1-v['mae']/base if base else None
        chosen=ps[report['selection'][area]];record['negative_price_metrics']=metrics(y[y<0],chosen[y<0])
        hours=np.array([int(label[:2]) for d in record['days'] for label in d['local_labels']])
        record['hourly']=[{'hour':h,**metrics(y[hours==h],chosen[hours==h])} for h in range(24)]
        record['decision_summary']={p:{'cost':sum(d['policies'][p]['cost'] for d in record['days']),'savings_vs_uniform':sum(d['policies'][p]['savings_vs_uniform'] for d in record['days']),'regret_vs_oracle':sum(d['policies'][p]['regret_vs_oracle'] for d in record['days']),'rejected_days':sum(d['policies'][p]['status']=='REJECTED' for d in record['days'])} for p in ('median','upper')}
        record['decision_summary']['uniform_cost']=sum(d['uniform_cost'] for d in record['days']);record['decision_summary']['oracle_cost']=sum(d['oracle_cost'] for d in record['days'])
    ledger=book.export();book.close()
    for name,rows in {'predictions':predictions,**ledger}.items():
        with (out/f'{name}.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (out/'predictions.csv.gz').write_bytes(gzip.compress((out/'predictions.csv').read_bytes(),mtime=0))
    (out/'results.json').write_text(json.dumps(safe(report),ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8')
    print(json.dumps({'selection':report['selection'],'test':{a:r['metrics'] for a,r in report['areas'].items()}},indent=2),flush=True)
    return report
