from pathlib import Path
import sys, csv, json, time, platform, shutil
import numpy as np, sklearn
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import GroupKFold

# Tuan 10 theo nhan xet cua thay:
# target chinh = total trong scores.json (trung vi lam tron xuong); trung binh nam diem la phan tich phu.
# Chi so chinh = recall/precision bai duoi 6 trong 10%/20% du doan thap nhat. Chon tham so bang GroupKFold 5 phan
# theo nguoi noi tren 125 nguoi train chinh thuc; test chay mot lan. Them tach do dai cau, phan loai can bang,
# embedding wav2vec 2.0, sai so theo nguoi noi, 5 cau doan sai nang nhat, va phan tich giam khao lech.
P = Path(__file__).parent
root = Path(sys.argv[1]) if len(sys.argv) > 1 else P.parent/'week09_work'/'data'/'speechocean762'
t0 = time.perf_counter()
rows = list(csv.DictReader((P/'split_manifest.csv').open()))
uid = [r['utterance_id'] for r in rows]; spk = np.array([r['speaker_id'] for r in rows])
TR = np.array([r['split'] in ('train', 'validation') for r in rows]); TE = ~TR
raw = json.loads((P/'scores-detail.json').read_text()); pub = json.loads((P/'scores.json').read_text())
five = np.array([raw[u]['total'] for u in uid], dtype=float)
y_tot = np.array([pub[u]['total'] for u in uid], dtype=float)          # target chinh
y_mean = np.array([float(r['target_mean_total']) for r in rows])        # phan tich phu
words = np.array([len(pub[u]['text'].split()) for u in uid])
LOW = 6.0
age = {}
for s in ['train', 'test']:
    for line in (root/s/'spk2age').read_text().split('\n'):
        if line.strip(): a, b = line.split(); age[a.zfill(4)] = int(b)
spk_age = np.array([age[s.zfill(4)] for s in spk])

# [1] Kiem tra target
med = np.median(five, 1)
check = {'floor_median': int(np.sum(np.floor(med) == y_tot)), 'round_median': int(np.sum(np.round(med) == y_tot)),
         'median_exact': int(np.sum(np.isclose(med, y_tot))), 'mean_exact': int(np.sum(np.isclose(five.mean(1), y_tot))), 'n': len(uid)}

# Dac trung
def load(name, key):
    d = np.load(P/name); assert list(d['utterance_id']) == uid; return d[key].astype(np.float64)
X81 = load('features_logmel_stats.npz', 'X'); dur = X81[:, 80]
F = {'log-mel 81': X81, 'log-mel 80 (bỏ độ dài)': X81[:, :80], 'độ dài 2': np.c_[dur, dur/words]}
W = np.load(P/'features_w2v_layers.npz'); assert list(W['utterance_id']) == uid
W2V = {int(l): W['E'][:, i].astype(np.float64) for i, l in enumerate(W['layers'])}

def budget(score, y, mask, frac):  # score thap = uu tien nghe lai
    low = y[mask] < LOW; k = int(round(frac*mask.sum())); top = np.argsort(score, kind='stable')[:k]
    return float(low[top].sum()/low.sum()), float(low[top].mean())
def metrics(score, y, mask, regression=True):
    r10, p10 = budget(score, y, mask, .10); r20, p20 = budget(score, y, mask, .20)
    out = {'recall10': r10, 'precision10': p10, 'recall20': r20, 'precision20': p20}
    if regression:
        e = score - y[mask]; out |= {'MAE': float(np.mean(abs(e))), 'PCC': None if np.ptp(score) == 0 else float(np.corrcoef(score, y[mask])[0, 1]),
                                     'bias_low': float(e[y[mask] < LOW].mean())}
    return out

def svr(C, alpha=1): return lambda X, y: make_pipeline(StandardScaler(), SVR(kernel='rbf', gamma='scale', epsilon=0.1, C=C)).fit(X, y, svr__sample_weight=np.where(y < LOW, alpha, 1.0))
def rfr(leaf): return lambda X, y: RandomForestRegressor(n_estimators=300, max_features='sqrt', min_samples_leaf=leaf, random_state=42, n_jobs=-1).fit(X, y)
def lrc(C): return lambda X, y: make_pipeline(StandardScaler(), LogisticRegression(C=C, class_weight='balanced', max_iter=5000)).fit(X, y < LOW)
def rfc(leaf): return lambda X, y: RandomForestClassifier(n_estimators=300, max_features='sqrt', min_samples_leaf=leaf, class_weight='balanced', random_state=42, n_jobs=-1).fit(X, y < LOW)
def score_of(model, X, regression):  # diem dung de xep hang: hoi quy = diem du doan; phan loai = 1 - P(duoi 6)
    return model.predict(X) if regression else 1 - model.predict_proba(X)[:, 1]

gkf = GroupKFold(n_splits=5); folds = list(gkf.split(np.zeros(TR.sum()), groups=spk[TR]))
def cv(fit, X, y, regression=True):
    Xt, yt = X[TR], y[TR]; res = []
    for a, b in folds:
        m = fit(Xt[a], yt[a]); s = score_of(m, Xt[b], regression); fold_mask = np.zeros(len(y), bool); fold_mask[np.where(TR)[0][b]] = True
        res.append(metrics(s, y, fold_mask, regression))
    keys = res[0].keys(); return {k: [float(np.mean([r[k] for r in res])), float(np.std([r[k] for r in res]))] for k in keys if res[0][k] is not None}

models, preds, grids = {}, {}, {}
def run(name, cands, criterion, regression=True, y=y_tot):
    # cands: list of (config, fit, X). criterion 'MAE' (thap nhat) hoac 'recall20' (cao nhat) tren CV
    t = time.perf_counter(); scored = [(cv(fit, X, y, regression), cfg, fit, X) for cfg, fit, X in cands]
    best = (min if criterion == 'MAE' else max)(scored, key=lambda s: s[0][criterion][0])
    cvres, cfg, fit, X = best; m = fit(X[TR], y[TR]); s = score_of(m, X[TE], regression)
    preds[name] = s
    models[name] = {'config': cfg, 'criterion': criterion, 'cv': cvres, 'test': metrics(s, y, TE, regression), 'seconds': time.perf_counter()-t,
                    'grid': [[c, r] for r, c, _, _ in scored]}
CS, LEAVES = [0.3, 1, 3, 10], [1, 5, 20]
run('SVR log-mel', [({'C': C}, svr(C), F['log-mel 81']) for C in CS], 'MAE')
run('RF log-mel', [({'min_samples_leaf': k}, rfr(k), F['log-mel 81']) for k in LEAVES], 'MAE')
run('SVR chỉ độ dài', [({'C': C}, svr(C), F['độ dài 2']) for C in CS], 'MAE')
run('SVR log-mel bỏ độ dài', [({'C': C}, svr(C), F['log-mel 80 (bỏ độ dài)']) for C in CS], 'MAE')
Cb = models['SVR log-mel']['config']['C']
run('SVR log-mel + trọng số', [({'C': Cb, 'alpha': a}, svr(Cb, a), F['log-mel 81']) for a in [2, 4, 8]], 'recall20')
run('LR phân loại cân bằng', [({'C': C}, lrc(C), F['log-mel 81']) for C in [0.01, 0.1, 1]], 'recall20', regression=False)
run('RF phân loại cân bằng', [({'min_samples_leaf': k}, rfc(k), F['log-mel 81']) for k in LEAVES], 'recall20', regression=False)
run('SVR wav2vec 2.0', [({'layer': l, 'C': C}, svr(C), W2V[l]) for l in W2V for C in [1, 3, 10]], 'MAE')
base = float(np.mean(y_tot[TE] < LOW)); const = np.full(TE.sum(), y_tot[TR].mean())
models['Ngẫu nhiên / hằng số'] = {'config': 'mean(y_train) = %.3f' % y_tot[TR].mean(), 'test': {**metrics(const, y_tot, TE), 'recall10': .10, 'recall20': .20, 'precision10': base, 'precision20': base}}
preds['Ngẫu nhiên / hằng số'] = const
# Phan tich phu: target trung binh nam diem
second = {}
for name, cfg_src, X in [('SVR log-mel', 'SVR log-mel', F['log-mel 81']), ('SVR wav2vec 2.0', 'SVR wav2vec 2.0', None)]:
    c = models[cfg_src]['config']; Xs = W2V[c['layer']] if X is None else X
    m = svr(c['C'])(Xs[TR], y_mean[TR]); second[name] = metrics(m.predict(Xs[TE]), y_mean, TE)

# Sai so theo nguoi noi va tuoi (target chinh)
yt, st, at = y_tot[TE], spk[TE], spk_age[TE]; ids = sorted(set(st))
spk_rows = []
for k in ids:
    m = st == k
    spk_rows.append([k, int(at[m][0]), int(m.sum()), float(yt[m].mean()), int((yt[m] < LOW).sum()),
                     float(abs(preds['SVR log-mel'][m]-yt[m]).mean()), float(abs(preds['SVR wav2vec 2.0'][m]-yt[m]).mean())])
with (P/'speaker_errors_test.csv').open('w', newline='') as f:
    w = csv.writer(f); w.writerow(['speaker_id', 'age', 'n_utt', 'mean_target', 'n_below6', 'MAE_svr_logmel', 'MAE_svr_w2v']); w.writerows(spk_rows)
S = np.array(spk_rows, dtype=object)
def spk_summary(col):
    mae = S[:, col].astype(float); tot = np.array([abs(preds[['SVR log-mel', 'SVR wav2vec 2.0'][col-5]][st == k]-yt[st == k]).sum() for k in ids])
    top = int(round(0.1*len(ids))); return {'median_MAE': float(np.median(mae)), 'max_MAE': float(mae.max()), 'top_n': top, 'top_share': float(np.sort(tot)[::-1][:top].sum()/tot.sum())}
speakers = {'SVR log-mel': spk_summary(5), 'SVR wav2vec 2.0': spk_summary(6),
            'corr_mae_meantarget': float(np.corrcoef(S[:, 3].astype(float), S[:, 5].astype(float))[0, 1])}
ages = {}
for g, gm in [('child', at <= 12), ('adult', at > 12)]:
    ages[g] = {'speakers': int(len(set(st[gm]))), 'utterances': int(gm.sum()), 'below6': int((yt[gm] < LOW).sum()),
               'MAE_logmel': float(abs(preds['SVR log-mel'][gm]-yt[gm]).mean()), 'MAE_w2v': float(abs(preds['SVR wav2vec 2.0'][gm]-yt[gm]).mean())}

# 5 cau diem that duoi 6 bi SVR log-mel doan cao nhat (so voi diem that)
te_idx = np.where(TE)[0]; over = preds['SVR log-mel'] - yt; cand = np.where(yt < LOW)[0]
worst = cand[np.argsort(-over[cand])[:5]]; (P/'worst5').mkdir(exist_ok=True); wavs = {f.stem: f for f in (root/'WAVE').glob('SPEAKER*/*.WAV')}
worst5 = []
for i in worst:
    j = te_idx[i]; u = uid[j]; shutil.copy2(wavs[u], P/'worst5'/(u+'.WAV'))
    worst5.append({'id': u, 'speaker': spk[j], 'age': int(spk_age[j]), 'text': pub[u]['text'], 'five': five[j].tolist(), 'total': float(y_tot[j]),
                   'pred_logmel': float(preds['SVR log-mel'][i]), 'pred_w2v': float(preds['SVR wav2vec 2.0'][i]), 'duration': float(dur[j]),
                   'words_per_s': float(words[j]/dur[j])})

# Mot giam khao lech han bon nguoi con lai: trung binh va trung vi phan ung the nao
dev = np.array([[abs(five[i, r] - np.median(np.delete(five[i], r))) for r in range(5)] for i in range(len(uid))]).max(1)
odd = dev >= 3
ex = int(np.argmax(dev))
raters = {'n_odd3': int(odd.sum()), 'mean_shift_odd': float(np.mean(abs(five[odd].mean(1) - np.median(five[odd], 1)))),
          'mean_shift_all': float(np.mean(abs(five.mean(1) - med))), 'example': {'id': uid[ex], 'five': five[ex].tolist(), 'mean': float(five[ex].mean()),
          'median': float(med[ex]), 'total': float(y_tot[ex])}}

with (P/'test_predictions_week10.csv').open('w', newline='') as f:
    w = csv.writer(f); w.writerow(['utterance_id', 'speaker_id', 'age', 'target_total', 'target_mean'] + list(preds))
    for i, j in enumerate(te_idx): w.writerow([uid[j], spk[j], int(spk_age[j]), float(y_tot[j]), float(y_mean[j])] + [float(preds[n][i]) for n in preds])
total = time.perf_counter() - t0
out = {'python': platform.python_version(), 'sklearn': sklearn.__version__, 'target': 'scores.json total', 'low_threshold': LOW, 'target_check': check,
       'below6': {'train125': [int((y_tot[TR] < LOW).sum()), int(TR.sum())], 'test': [int((y_tot[TE] < LOW).sum()), int(TE.sum())]}, 'base_rate_test': base,
       'max_recall10': int(round(.1*TE.sum()))/int((y_tot[TE] < LOW).sum()), 'models': models, 'secondary_mean_target': second,
       'speakers': speakers, 'ages': ages, 'worst5': worst5, 'raters': raters, 'w2v': json.loads((P/'w2v_run.json').read_text()),
       'pilot': json.loads((P/'pilot_w2v.json').read_text()), 'total_script_seconds': total}
(P/'week10_results.json').write_text(json.dumps(out, indent=2, ensure_ascii=False))

pct = lambda v: f'{v*100:.0f}%'; ms = lambda v: f'{v[0]:.3f}±{v[1]:.3f}'
log = [f"Week 10 | target = scores.json total | Python {platform.python_version()} | scikit-learn {sklearn.__version__} | CPU only",
       "--- [1] Target check (5,000 utterances) ---",
       f"floor(median) == total: {check['floor_median']}/5000 | round(median): {check['round_median']} | median exact: {check['median_exact']} | mean exact: {check['mean_exact']}",
       f"Below 6: train125 {out['below6']['train125'][0]}/2500, test {out['below6']['test'][0]}/2500 (base rate {pct(base)}) | max R@10 = {pct(out['max_recall10'])}",
       "--- [2] Hyper-parameters by GroupKFold-5 over 125 train speakers (CV MAE mean±SD) ---"]
for n in ['SVR log-mel', 'RF log-mel']:
    log.append(f"{n}: " + ' | '.join(f"{list(c.values())[0]}: {ms(r['MAE'])}" for c, r in models[n]['grid']) + f" -> chose {models[n]['config']}")
log.append(f"Chosen by CV: length-only C={models['SVR chỉ độ dài']['config']['C']}, no-duration C={models['SVR log-mel bỏ độ dài']['config']['C']}, "
           f"weight alpha={models['SVR log-mel + trọng số']['config']['alpha']}, LR C={models['LR phân loại cân bằng']['config']['C']}, "
           f"RFc leaf={models['RF phân loại cân bằng']['config']['min_samples_leaf']}, w2v {models['SVR wav2vec 2.0']['config']}")
log.append("--- [3] Test (run once): R@10 P@10 R@20 P@20 | MAE PCC ---")
order = ['Ngẫu nhiên / hằng số', 'SVR log-mel', 'RF log-mel', 'SVR chỉ độ dài', 'SVR log-mel bỏ độ dài', 'SVR log-mel + trọng số', 'LR phân loại cân bằng', 'RF phân loại cân bằng', 'SVR wav2vec 2.0']
short = {'Ngẫu nhiên / hằng số': 'random/constant', 'SVR log-mel': 'SVR log-mel', 'RF log-mel': 'RF log-mel', 'SVR chỉ độ dài': 'SVR length only', 'SVR log-mel bỏ độ dài': 'SVR log-mel no length',
         'SVR log-mel + trọng số': 'SVR log-mel + weight', 'LR phân loại cân bằng': 'LR balanced (cls)', 'RF phân loại cân bằng': 'RF balanced (cls)', 'SVR wav2vec 2.0': 'SVR wav2vec2'}
for n in order:
    t = models[n]['test']; reg = 'MAE' in t
    log.append(f"{short[n]:22s} {pct(t['recall10']):>4} {pct(t['precision10']):>4} {pct(t['recall20']):>4} {pct(t['precision20']):>4} | " +
               (f"{t['MAE']:.3f} {'n/a' if t['PCC'] is None else format(t['PCC'], '.3f')}" if reg else 'classifier'))
log.append(f"Secondary (mean-of-5 target) R@20: SVR log-mel {pct(second['SVR log-mel']['recall20'])}, SVR wav2vec2 {pct(second['SVR wav2vec 2.0']['recall20'])}")
log += ["--- [4] Speakers, age, worst cases, raters ---",
        f"Speaker MAE median: log-mel {speakers['SVR log-mel']['median_MAE']:.2f}, w2v {speakers['SVR wav2vec 2.0']['median_MAE']:.2f} | worst {speakers['SVR log-mel']['top_n']} spk = {pct(speakers['SVR log-mel']['top_share'])} of error | r(MAE, spk mean) = {speakers['corr_mae_meantarget']:.2f}",
        f"Child: {ages['child']['speakers']} spk, {ages['child']['below6']} below 6, MAE {ages['child']['MAE_logmel']:.2f}->{ages['child']['MAE_w2v']:.2f} | Adult: {ages['adult']['speakers']} spk, {ages['adult']['below6']} below 6, MAE {ages['adult']['MAE_logmel']:.2f}->{ages['adult']['MAE_w2v']:.2f}",
        "Worst 5 (total<6, SVR log-mel): " + ', '.join(f"{w['id']} {w['total']:.0f}->{w['pred_logmel']:.1f}" for w in worst5),
        f"One rater >= 3 points from other four: {raters['n_odd3']} utt | |mean - median| there: {raters['mean_shift_odd']:.2f} vs all: {raters['mean_shift_all']:.2f}",
        f"Analysis total {total:.1f} s | wav2vec2 full extraction (CPU): {out['w2v']['extract_seconds']:.0f} s"]
(P/'week10_run.log').write_text('\n'.join(log)+'\n')
print('\n'.join(log))
