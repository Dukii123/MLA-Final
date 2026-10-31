"""Sinh dữ liệu JSON cho web demo từ kết quả tuần 11 (không sửa số của báo cáo)."""
from pathlib import Path
import csv, json, shutil, hashlib
import numpy as np

P = Path(__file__).parent
ROOT = P.parent
W10 = ROOT / 'docs' / 'report' / 'week10_work'
W11 = ROOT / 'docs' / 'report' / 'week11_work'
W9 = ROOT / 'docs' / 'report' / 'week09_work'
DATA = P / 'data'
OUT = DATA
OUT.mkdir(parents=True, exist_ok=True)
(DATA / 'worst5').mkdir(exist_ok=True)
(P / 'static' / 'figures').mkdir(parents=True, exist_ok=True)

LABELS = {
    'SVR log-mel': ('SVR log-mel', 'log-mel', '#2a78d6'),
    'RF log-mel': ('RF log-mel', 'log-mel', '#7ba7dd'),
    'SVR chỉ độ dài': ('SVR chỉ độ dài', 'length', '#1baf7a'),
    'SVR log-mel bỏ độ dài': ('SVR log-mel bỏ độ dài', 'log-mel', '#9bbfe8'),
    'SVR log-mel + trọng số': ('SVR log-mel + trọng số', 'log-mel', '#1f5fa8'),
    'LR phân loại cân bằng': ('LR phân loại cân bằng', 'classifier', '#6f6f6a'),
    'RF phân loại cân bằng': ('RF phân loại cân bằng', 'classifier', '#9a9a94'),
    'SVR wav2vec 2.0': ('SVR wav2vec 2.0', 'wav2vec', '#eb6834'),
    'SVR wav2vec + độ dài': ('SVR wav2vec + độ dài', 'wav2vec', '#f39a70'),
    'LR phân loại cân bằng (wav2vec)': ('LR phân loại cân bằng (wav2vec)', 'classifier', '#c98b6a'),
    'Ngẫu nhiên / hằng số': ('Ngẫu nhiên / hằng số', 'random', '#8a8a86'),
}
TEACHER_MODELS = ['SVR wav2vec 2.0', 'SVR log-mel', 'RF log-mel', 'SVR chỉ độ dài',
                  'SVR log-mel bỏ độ dài', 'SVR log-mel + trọng số', 'Ngẫu nhiên / hằng số']

manifest = list(csv.DictReader((W10 / 'split_manifest.csv').open()))
preds_rows = list(csv.DictReader((W11 / 'test_predictions_week11.csv').open()))
pub = json.loads((W9 / 'data' / 'speechocean762' / 'resource' / 'scores.json').read_text(encoding='utf-8'))
raw = json.loads((W9 / 'data' / 'speechocean762' / 'resource' / 'scores-detail.json').read_text(encoding='utf-8'))
res = json.loads((W11 / 'week11_results.json').read_text(encoding='utf-8'))

X = np.load(W10 / 'features_logmel_stats.npz')
ids_npz = list(X['utterance_id'])
assert ids_npz == [r['utterance_id'] for r in manifest], 'thứ tự npz lệch manifest'
dur = {u: float(v) for u, v in zip(ids_npz, X['X'][:, 80])}

WAVE = P / 'data' / 'speechocean762' / 'WAVE'
if not WAVE.exists():
    WAVE = W9 / 'data' / 'speechocean762' / 'WAVE'
audio_ids = {f.stem for f in WAVE.glob('SPEAKER*/*.WAV')}

model_keys = [k for k in preds_rows[0].keys() if k not in
              ('utterance_id', 'speaker_id', 'age', 'target_total', 'target_mean', 'sec_per_word')]

utterances = []
for r in preds_rows:
    u = r['utterance_id']
    text = pub[u]['text']
    five = [float(v) for v in raw[u]['total']]
    total = float(pub[u]['total'])
    pred = {k: float(r[k]) for k in model_keys}
    rand = int(hashlib.sha1(u.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    utterances.append({
        'id': u,
        'speaker': r['speaker_id'],
        'age': int(r['age']),
        'text': text,
        'words': len(text.split()),
        'five': five,
        'total': total,
        'below6': total < 6,
        'sec_per_word': float(r['sec_per_word']),
        'duration': dur[u],
        'pred': pred,
        'rand': rand,
        'audio': u in audio_ids,
    })
utterances.sort(key=lambda x: x['id'])
assert len(utterances) == 2500

(DATA / 'utterances.json').write_text(json.dumps(utterances, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
shutil.copyfile(W11 / 'week11_results.json', DATA / 'results.json')

models = []
for key, (label, family, color) in LABELS.items():
    m = res['models'].get(key, {})
    models.append({
        'key': key, 'label': label, 'family': family, 'color': color,
        'kind': 'classifier' if family == 'classifier' else ('random' if family == 'random' else 'regression'),
        'cv': m.get('cv'), 'test': m.get('test'), 'config': m.get('config'),
    })

worst_ids = [w['id'] for w in res['worst5']]
for u in worst_ids:
    src = W11 / 'worst5' / f'{u}.WAV'
    if src.exists():
        shutil.copyfile(src, DATA / 'worst5' / f'{u}.WAV')

for f in ['fig1_cv_test.png', 'fig2_halves.png', 'fig3_speed_dist.png']:
    src = W11 / f
    if src.exists():
        shutil.copyfile(src, P / 'static' / 'figures' / f)

meta = {
    'project': {
        'title': 'Ưu tiên nghe lại bài đọc điểm thấp',
        'subtitle': 'Dự đoán điểm phát âm mức câu trên speechocean762',
        'group': 'Nhóm 05', 'class': '61FIT4MLA', 'teacher': 'Thầy Khánh',
        'report': 'Báo cáo tuần 11', 'date': '27/10/2026',
    },
    'data': {
        'n_train': 2500, 'n_test': 2500, 'n_below6': 330,
        'base_rate': res['base_rate_test'], 'n_speakers_train': 125,
        'n_speakers_test': 125, 'n_audio': sum(1 for x in utterances if x['audio']), 'n_worst5': len(worst_ids),
    },
    'models': models,
    'teacher_models': TEACHER_MODELS,
    'samples': {'caught': '096230018', 'missed': '014040089', 'high': '023550123'},
    'worst5_ids': worst_ids,
    'figures': {
        'cv_test': 'figures/fig1_cv_test.png',
        'halves': 'figures/fig2_halves.png',
        'speed': 'figures/fig3_speed_dist.png',
    },
}
(DATA / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')

print('utterances:', len(utterances), '| audio found:', sum(1 for x in utterances if x['audio']), '/2500')
print('below6:', sum(1 for x in utterances if x['below6']))
print('sizes:', {p.name: round(p.stat().st_size / 1e6, 2) for p in [DATA / 'utterances.json', DATA / 'results.json', DATA / 'meta.json']})
print('worst5 copied:', len(list((DATA / 'worst5').glob('*.WAV'))))
