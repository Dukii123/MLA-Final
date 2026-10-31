from pathlib import Path
import json, time, wave, hashlib, platform, csv, os, subprocess
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np

P = Path(__file__).parent
t0 = time.perf_counter()
def sysctl(key):
    try: return subprocess.run(['sysctl','-n',key],capture_output=True,text=True,check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError): return ''
cpu = sysctl('machdep.cpu.brand_string') or platform.processor() or platform.machine()
ram = int(sysctl('hw.memsize') or 0)/2**30
hardware = f"{cpu}, {os.cpu_count()} CPU cores, {ram:.0f} GiB RAM ({platform.system()} {platform.machine()}); no GPU used"
raw = json.loads((P/'scores-detail.json').read_text())
published = json.loads((P/'scores.json').read_text())
def mapping(name):
    return dict(line.split() for line in (P/name).read_text().splitlines())
tr, te = mapping('train_utt2spk'), mapping('test_utt2spk')
speakers = np.array(sorted(set(tr.values())))
val_spk = set(np.random.default_rng(42).permutation(speakers)[:25])
ids = {'train': sorted(k for k,v in tr.items() if v not in val_spk),
       'validation': sorted(k for k,v in tr.items() if v in val_spk),
       'test': sorted(te)}
spk = {s:set((tr|te)[k] for k in ks) for s,ks in ids.items()}
assert not (spk['train']&spk['validation'] or spk['train']&spk['test'] or spk['validation']&spk['test'])
assert len(set().union(*map(set,ids.values()))) == 5000
y = {s:np.array([np.mean(raw[k]['total']) for k in ks]) for s,ks in ids.items()}
c = float(y['train'].mean())
metrics = {s:{'MAE':float(np.mean(abs(a-c))), 'RMSE':float(np.sqrt(np.mean((a-c)**2))), 'PCC':None} for s,a in y.items() if s!='train'}
agreement={}
for aspect in ['accuracy','fluency','prosodic','total']:
    a=np.array([v[aspect] for v in raw.values()]); n,k=a.shape
    msb=k*np.var(a.mean(axis=1),ddof=1)
    msw=np.mean(np.var(a,axis=1,ddof=1))
    icc=(msb-msw)/(msb+(k-1)*msw)
    agreement[aspect]=[float(np.corrcoef(a.T)[np.triu_indices(k,1)].mean()),float(icc),float(k*icc/(1+(k-1)*icc)),float(np.std(a,axis=1,ddof=1).mean())]
mismatches=sum(not np.isclose(np.mean(v['total']),published[k]['total']) for k,v in raw.items())
sample=raw['000010011']
with wave.open(str(P/'000010011.WAV')) as w:
    sr,channels,width,nframes=w.getframerate(),w.getnchannels(),w.getsampwidth(),w.getnframes()
    x=np.frombuffer(w.readframes(nframes),dtype='<i2').astype(np.float64)/32768
assert sr==16000 and channels==1 and width==2
hashes={f:hashlib.sha256((P/f).read_bytes()).hexdigest() for f in ['scores-detail.json','scores.json','train_utt2spk','test_utt2spk','000010011.WAV']}
result={'date':datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat(),'hardware':hardware,'python':platform.python_version(),'numpy':np.__version__,'machine':platform.machine(),'split':{s:[len(spk[s]),len(ids[s])] for s in ids},'speaker_overlap':0,'constant':c,'metrics':metrics,'agreement':agreement,'mean_target_mismatches':int(mismatches),'sample':{'id':'000010011','text':sample['text'],'total':sample['total'],'target':float(np.mean(sample['total'])),'published':published['000010011']['total'],'sample_rate':sr,'duration_seconds':nframes/sr},'sha256':hashes}
with (P/'split_manifest.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['utterance_id','speaker_id','split','target_mean_total','constant_prediction'])
    for split, keys in ids.items():
        for uid, target in zip(keys,y[split]):
            w.writerow([uid,(tr|te)[uid],split,float(target),c])
(P/'sample_labels.json').write_text(json.dumps(result['sample'],ensure_ascii=False,indent=2))
result['total_script_seconds']=time.perf_counter()-t0
(P/'verified_results.json').write_text(json.dumps(result,indent=2))
s=result['sample']
log=[f"Run date: {result['date']} | CPU only",f"Hardware: {result['hardware']}",f"Python {platform.python_version()} | NumPy {np.__version__}",
     "--- [1] Sample audio and labels ---",f"Utterance: {s['id']} | reference text: {s['text']} | {sr} Hz mono, {nframes/sr:.2f} s",f"Five rater totals: {', '.join(map(str,s['total']))}",f"Target = mean of five = {s['target']:.2f} | scores.json total = {s['published']}",
     "--- [2] Rater agreement (5,000 utterances) ---"]
log += [f"{a}: pairwise PCC={v[0]:.3f} ICC(1,1)={v[1]:.3f} ICC(1,5)={v[2]:.3f} mean rater SD={v[3]:.3f}" for a,v in agreement.items()]
log += ["--- [3] Speaker split and constant baseline ---","Split speakers/utterances: "+", ".join(f"{k} {v[0]}/{v[1]}" for k,v in result['split'].items())+" | speaker overlap: 0",f"Raw-mean vs published target differences: {mismatches}/5000",f"Train-mean constant: {c:.6f}"]
log += [f"{k}: MAE={m['MAE']:.4f} RMSE={m['RMSE']:.4f} PCC=undefined" for k,m in metrics.items()]
log += [f"verify.py total time (after imports): {result['total_script_seconds']:.3f} s"]
(P/'verified_run.log').write_text('\n'.join(log)+'\n')
print('\n'.join(log))
