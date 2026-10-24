"""Only delayed prices and known calendar values enter the information set."""
from datetime import timedelta
import numpy as np
from .data import DK,STEP,available,decision,stamp

LAG_HOURS=(72,96,168,336)
NAMES=[f'{zone}_lag_{h}h' for zone in ('own','other') for h in LAG_HOURS]+[
    'own_recent_mean','own_recent_std','own_recent_min','own_recent_max',
    'day_sin','day_cos','day_sin2','day_cos2','year_sin','year_cos',
    *[f'weekday_{d}' for d in range(7)],'utc_offset_hours','dst_fold']

def matrix(values,area):
    times=sorted(values[area]);other='DK2' if area=='DK1' else 'DK1'
    if times!=sorted(values[other]):raise ValueError('Zones are not aligned')
    if any(b-a!=STEP for a,b in zip(times,times[1:])):raise ValueError('Time gap')
    own=np.array([values[area][t] for t in times]);cross=np.array([values[other][t] for t in times])
    indices=np.arange(336*4,len(times));target=[times[i] for i in indices]
    cols=[prices[indices-h*4] for prices in (own,cross) for h in LAG_HOURS]
    windows=np.lib.stride_tricks.sliding_window_view(own,96)[indices-72*4-95]
    cols += [windows.mean(1),windows.std(1),windows.min(1),windows.max(1)]
    local=[t.astimezone(DK) for t in target];hours=np.array([t.hour+t.minute/60 for t in local]);annual=np.array([t.timetuple().tm_yday for t in local])
    cols += [np.sin(hours*2*np.pi/24),np.cos(hours*2*np.pi/24),np.sin(hours*4*np.pi/24),np.cos(hours*4*np.pi/24),np.sin(annual*2*np.pi/365.25),np.cos(annual*2*np.pi/365.25)]
    cols += [np.array([t.weekday()==d for t in local],dtype=float) for d in range(7)]
    cols += [np.array([t.utcoffset().total_seconds()/3600 for t in local]),np.array([t.fold for t in local])]
    cutoffs={t.date():decision(t.date()) for t in local}
    margins=[(cutoffs[l.date()]-available(t-timedelta(hours=72))).total_seconds()/3600 for t,l in zip(target,local)]
    if min(margins)<0:raise ValueError('Future price feature detected')
    X=np.column_stack(cols)
    if not np.isfinite(X).all():raise ValueError('Nonfinite features')
    return {'times':target,'X':X,'y':own[indices],'weekly':own[indices-168*4],
            'minimum_feature_availability_margin_hours':min(margins)}
