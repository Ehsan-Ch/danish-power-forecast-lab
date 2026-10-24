export const names={weekly:'Weekly seasonal',ridge:'Ridge regression',boosted:'Quantile boosting'};
export function score(y,p){if(!y.length)return null;const n=y.length;let mae=0,se=0,bias=0,hit=0,width=0,is=0;for(let i=0;i<n;i++){const [l,m,u]=p[i],e=m-y[i];mae+=Math.abs(e);se+=e*e;bias+=e;hit+=y[i]>=l&&y[i]<=u?1:0;width+=u-l;is+=u-l+10*Math.max(l-y[i],0)+10*Math.max(y[i]-u,0);}return {mae:mae/n,rmse:Math.sqrt(se/n),bias:bias/n,coverage:hit/n,width:width/n,interval_score:is/n};}
export function cost(y,q,fee=.5){if(y.length!==q.length)throw Error('Mismatched quantities');return y.reduce((sum,p,i)=>sum+q[i]*(p+fee),0);}
export function csv(rows){return rows.map(row=>row.map(x=>'"'+String(x??'').replaceAll('"','""')+'"').join(',')).join('\r\n');}
export function orderStatus(final,phase){if(phase==='PROPOSED')return 'PROPOSED';if(final==='REJECTED')return 'REJECTED';return phase;}
export function chartDomain(y,p){const all=[...y,...p.flat(),0];let lo=Math.min(...all),hi=Math.max(...all);const pad=Math.max((hi-lo)*.08,1);return [lo-pad,hi+pad];}
