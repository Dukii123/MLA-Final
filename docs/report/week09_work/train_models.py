from pathlib import Path
import sys, csv, json, time, wave, platform
import numpy as np, sklearn
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor

# Dung split va target trong split_manifest.csv do verify.py tao; audio lay tu speechocean762 (OpenSLR SLR101).
P = Path(__file__).parent
root = Path(sys.argv[1]) if len(sys.argv) > 1 else P/'data'/'speechocean762'
t0 = time.perf_counter()
rows = list(csv.DictReader((P/'split_manifest.csv').open()))
wavs = {f.stem: f for f in (root/'WAVE').glob('SPEAKER*/*.WAV')}
assert all(r['utterance_id'] in wavs for r in rows), 'missing WAV files'

def logmel(x, sr):
    frame,hop,nfft,bands=400,160,512,40
    frames=np.lib.stride_tricks.sliding_window_view(x,frame)[::hop]
    power=abs(np.fft.rfft(frames*np.hanning(frame),n=nfft))**2
    mel=np.linspace(0,2595*np.log10(1+(sr/2)/700),bands+2)
    hz=700*(10**(mel/2595)-1); freqs=np.fft.rfftfreq(nfft,1/sr)
    lo,mid,hi=hz[:-2,None],hz[1:-1,None],hz[2:,None]
    bank=np.maximum(0,np.minimum((freqs-lo)/(mid-lo),(hi-freqs)/(hi-mid)))
    return np.log(np.maximum(power@bank.T,1e-10)).T

def features(path):
    with wave.open(str(path)) as w:
        sr,n=w.getframerate(),w.getnframes()
        assert sr==16000 and w.getnchannels()==1 and w.getsampwidth()==2
        x=np.frombuffer(w.readframes(n),dtype='<i2').astype(np.float64)/32768
    m=logmel(x,sr)
    return np.concatenate([m.mean(1), m.std(1), [n/sr]])

t=time.perf_counter()
X=np.array([features(wavs[r['utterance_id']]) for r in rows]); feature_seconds=time.perf_counter()-t
assert np.isfinite(X).all()
np.savez_compressed(P/'features_logmel_stats.npz', utterance_id=[r['utterance_id'] for r in rows], X=X.astype(np.float32))
y=np.array([float(r['target_mean_total']) for r in rows]); split=np.array([r['split'] for r in rows])
tr,va,te=(split==s for s in ['train','validation','test'])

def score(pred, target):
    pcc=None if np.ptp(pred)==0 else float(np.corrcoef(pred,target)[0,1])
    return {'MAE':float(np.mean(abs(pred-target))),'RMSE':float(np.sqrt(np.mean((pred-target)**2))),'PCC':pcc}

grids={'SVR':[{'C':C} for C in [0.3,1,3,10]], 'RF':[{'min_samples_leaf':k} for k in [1,5,20]]}
build={'SVR':lambda g: make_pipeline(StandardScaler(), SVR(kernel='rbf', gamma='scale', epsilon=0.1, **g)),
       'RF':lambda g: RandomForestRegressor(n_estimators=300, max_features='sqrt', random_state=42, n_jobs=-1, **g)}
results={'constant':{'config':'mean(y_train)','validation':score(np.full(va.sum(),y[tr].mean()),y[va]),'test':score(np.full(te.sum(),y[tr].mean()),y[te])}}
preds={'constant':np.full(te.sum(),y[tr].mean())}
for name in grids:
    t=time.perf_counter(); tried=[]
    for g in grids[name]:
        model=build[name](g).fit(X[tr],y[tr]); tried.append((score(model.predict(X[va]),y[va]),g,model))
    val,g,model=min(tried,key=lambda r:r[0]['MAE'])
    preds[name]=model.predict(X[te])
    results[name]={'config':g,'tried':[[gg,v] for v,gg,_ in tried],'validation':val,'test':score(preds[name],y[te]),'train_select_seconds':time.perf_counter()-t}
with (P/'test_predictions.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['utterance_id','target']+list(preds))
    for i,(r,target) in enumerate(zip([r for r in rows if r['split']=='test'],y[te])):
        w.writerow([r['utterance_id'],float(target)]+[float(preds[n][i]) for n in preds])
total=time.perf_counter()-t0
out={'python':platform.python_version(),'numpy':np.__version__,'sklearn':sklearn.__version__,'device':'CPU only; RF n_jobs=-1','n_utterances':len(rows),'feature_dim':X.shape[1],'feature':'log-mel 40 bands: per-band mean and std over frames + duration (s)','feature_seconds':feature_seconds,'results':results,'total_script_seconds':total}
(P/'model_results.json').write_text(json.dumps(out,indent=2))
fmt=lambda m:f"MAE={m['MAE']:.4f} RMSE={m['RMSE']:.4f} PCC="+('undefined' if m['PCC'] is None else f"{m['PCC']:.3f}")
log=["--- [4] Fixed features on all audio ---",f"WAV files read: {len(rows)} | feature: {out['feature']}",f"Feature matrix: {X.shape[0]} x {X.shape[1]} | read + extract time: {feature_seconds:.1f} s (CPU)",
     f"--- [5] Model selection on validation (lowest MAE) | scikit-learn {sklearn.__version__} ---"]
log+=[f"{n}: tried {[list(g.values())[0] for g in grids[n]]} -> chose {results[n]['config']} | val {fmt(results[n]['validation'])} | {results[n]['train_select_seconds']:.1f} s" for n in grids]
log+=["--- [6] Test set, final configs evaluated once ---"]+[f"{n}: {fmt(results[n]['test'])}" for n in results]
log+=[f"train_models.py total time (after imports): {total:.1f} s | CPU only, no GPU"]
(P/'model_run.log').write_text('\n'.join(log)+'\n')
print('\n'.join(log))
