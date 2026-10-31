"""Huấn luyện lại đúng pipeline tuần 11 trên split train và lưu model cho web demo.

Không thay đổi dữ liệu/chia tập/siêu tham số của báo cáo. Model lưu ở webapp/models/.
"""
from pathlib import Path
import csv, json, time
import joblib
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from sklearn.linear_model import LogisticRegression

P = Path(__file__).parent
ROOT = P.parent
W10 = ROOT / 'docs' / 'report' / 'week10_work'
W11 = ROOT / 'docs' / 'report' / 'week11_work'
W9 = ROOT / 'docs' / 'report' / 'week09_work'
MODELS = P / 'models'
MODELS.mkdir(exist_ok=True)

LOW = 6.0
rows = list(csv.DictReader((W10 / 'split_manifest.csv').open()))
uid = [r['utterance_id'] for r in rows]
spk = np.array([r['speaker_id'] for r in rows])
TR = np.array([r['split'] in ('train', 'validation') for r in rows])
TE = ~TR
pub = json.loads((W9 / 'data' / 'speechocean762' / 'resource' / 'scores.json').read_text(encoding='utf-8'))
y = np.array([float(pub[u]['total']) for u in uid])
words = np.array([len(pub[u]['text'].split()) for u in uid])

Xnpz = np.load(W10 / 'features_logmel_stats.npz')
assert list(Xnpz['utterance_id']) == uid
X81 = Xnpz['X'].astype(np.float64)
dur = X81[:, 80]
F_len = np.c_[dur, dur / words]
Wnpz = np.load(W10 / 'features_w2v_layers.npz')
assert list(Wnpz['utterance_id']) == uid
layers = [int(v) for v in Wnpz['layers']]
W2V = {l: Wnpz['E'][:, i].astype(np.float64) for i, l in enumerate(layers)}

print(f'train {TR.sum()} | test {TE.sum()} | below6 train {int((y[TR] < LOW).sum())} | layers {layers}')

t0 = time.perf_counter()
svr = lambda: make_pipeline(StandardScaler(), SVR(kernel='rbf', gamma='scale', epsilon=0.1, C=1))
m_logmel = svr().fit(X81[TR], y[TR])
m_w2v = svr().fit(W2V[8][TR], y[TR])
m_len = svr().fit(F_len[TR], y[TR])
m_lr = make_pipeline(StandardScaler(), LogisticRegression(C=0.01, class_weight='balanced', max_iter=5000)).fit(W2V[4][TR], y[TR] < LOW)

for name, model, X in [('svr_logmel', m_logmel, X81), ('svr_w2v', m_w2v, W2V[8]), ('svr_length', m_len, F_len)]:
    joblib.dump(model, MODELS / f'{name}.joblib', compress=3)
joblib.dump(m_lr, MODELS / 'lr_w2v.joblib', compress=3)

uid_arr = np.array(uid)
# Đối chiếu với dự đoán test của lần chạy tuần 11 đã có trong CSV (so khớp theo mã bài).
pr = list(csv.DictReader((W11 / 'test_predictions_week11.csv').open()))
prd = {r['utterance_id']: r for r in pr}
assert set(prd) == set(uid_arr[TE]), 'test predictions lệch split'
test_ids = list(uid_arr[TE])
checks = {
    'SVR log-mel': (m_logmel.predict(X81[TE]), np.array([float(prd[u]['SVR log-mel']) for u in test_ids])),
    'SVR wav2vec 2.0': (m_w2v.predict(W2V[8][TE]), np.array([float(prd[u]['SVR wav2vec 2.0']) for u in test_ids])),
    'SVR chỉ độ dài': (m_len.predict(F_len[TE]), np.array([float(prd[u]['SVR chỉ độ dài']) for u in test_ids])),
}
for name, (a, b) in checks.items():
    print(f'{name}: max|diff| = {np.abs(a - b).max():.6f}')

meta = {
    'trained_at': time.strftime('%Y-%m-%d %H:%M:%S'),
    'n_train': int(TR.sum()), 'n_test': int(TE.sum()),
    'features': {
        'logmel': '40 mel bands, mean+std theo frame, + độ dài giây (81 chiều)',
        'wav2vec': 'facebook/wav2vec2-base, trung bình theo thời gian của tầng 8 (768 chiều)',
        'length': 'giây và giây/từ (2 chiều)',
    },
    'configs': {
        'svr_logmel': {'C': 1}, 'svr_w2v': {'layer': 8, 'C': 1},
        'svr_length': {'C': 1}, 'lr_w2v': {'layer': 4, 'C': 0.01, 'class_weight': 'balanced'},
    },
    'seconds': time.perf_counter() - t0,
}
(MODELS / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'saved models in {MODELS} ({meta["seconds"]:.1f} s)')
