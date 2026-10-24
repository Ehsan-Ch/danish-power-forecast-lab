"""Fixed recipes and disjoint residual calibration."""
import math
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

MODELS=('weekly','ridge','boosted')
HYPERPARAMETERS={'max_iter':100,'learning_rate':.05,'max_leaf_nodes':15,'min_samples_leaf':80,'l2_regularization':1.,'early_stopping':False,'random_state':42}

def correction(scores,coverage=.8):
    scores=np.asarray(scores,float)
    if scores.ndim!=1 or not len(scores) or not np.isfinite(scores).all() or not 0<coverage<1:raise ValueError('Invalid calibration')
    rank=math.ceil((len(scores)+1)*coverage)
    if rank>len(scores):raise ValueError('Insufficient calibration sample')
    return float(np.sort(scores)[rank-1])

def ordered(pred):
    pred=np.asarray(pred,float)
    if pred.ndim!=2 or pred.shape[1]!=3 or not np.isfinite(pred).all():raise ValueError('Invalid quantiles')
    return np.sort(pred,axis=1)

class ForecastModels:
    def fit(self,X,y):
        with threadpool_limits(limits=2):
            self.ridge=make_pipeline(StandardScaler(),Ridge(alpha=10.)).fit(X,y)
            self.boosted=[HistGradientBoostingRegressor(loss='quantile',quantile=q,**HYPERPARAMETERS).fit(X,y) for q in (.1,.5,.9)]
        return self
    def raw(self,X,weekly):
        with threadpool_limits(limits=2):
            ridge=self.ridge.predict(X)
            boosted=ordered(np.column_stack([m.predict(X) for m in self.boosted]))
        return {'weekly':np.column_stack([weekly]*3),'ridge':np.column_stack([ridge]*3),'boosted':boosted}
    def calibrate(self,X,y,weekly):
        raw=self.raw(X,weekly);self.offsets={}
        for name,p in raw.items():self.offsets[name]=correction(np.maximum.reduce([p[:,0]-y,y-p[:,2],np.zeros(len(y))]))
        return self
    def predict(self,X,weekly):
        results=self.raw(X,weekly)
        for name,p in results.items():p[:,0]-=self.offsets[name];p[:,2]+=self.offsets[name]
        return results

def metrics(y,p):
    y=np.asarray(y,float);p=np.asarray(p,float)
    if len(y)==0:return None
    if p.shape!=(len(y),3) or not np.isfinite(p).all() or not np.isfinite(y).all() or np.any(p[:,0]>p[:,1]) or np.any(p[:,1]>p[:,2]):raise ValueError('Invalid scoring input')
    error=p[:,1]-y;lo,hi=p[:,0],p[:,2]
    score=hi-lo+10*np.maximum(lo-y,0)+10*np.maximum(y-hi,0)
    return {'n':len(y),'mae':float(np.abs(error).mean()),'rmse':float(np.sqrt((error**2).mean())),
            'bias':float(error.mean()),'coverage':float(((y>=lo)&(y<=hi)).mean()),'width':float((hi-lo).mean()),
            'interval_score':float(score.mean()),'median_pinball':float(np.abs(error).mean()/2)}
