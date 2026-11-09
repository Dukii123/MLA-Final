# Week 11 - phan tich completeness: diem corpus + do am hoc tu dong cho nhom loi nang nhat.
# Nguon: parquet HF (off-prompt/score corpus), week11_results.json, test_predictions_week11.csv,
#        webapp/data/utterances.json (nam diem giam khao), worst5/*.WAV.
# Chay: python week11_completeness.py <thu_muc_parquet>
# Ket qua: week11_completeness.json + week11_completeness.log (dung cho Muc 6 bao cao tuan 11).
from pathlib import Path
import csv, json, sys, wave, platform, time
import numpy as np
import pyarrow
import pyarrow.parquet as pq

P = Path(__file__).parent
PARQ = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r'C:\Users\DucAnh\AppData\Local\Temp\opencode\sp762')
ROOT = P.parent.parent.parent                      # .../MLA-Final
SR = 16000
t0 = time.perf_counter()

R = json.loads((P / 'week11_results.json').read_text(encoding='utf-8'))
W5_IDS = [w['id'] for w in R['worst5']]

# --- du doan 11 mo hinh + giay/tu cua test (cung lan chay week11_analysis.py) ---
with (P / 'test_predictions_week11.csv').open(encoding='utf-8-sig', newline='') as f:
    rd = list(csv.reader(f))
hd, rows = rd[0], [r for r in rd[1:] if r and r[0].strip()]
assert hd[0].strip().lower() == 'utterance_id' and len(hd) == 17, hd
ix = {name.strip(): i for i, name in enumerate(hd)}
ILM, IW2, ITT, ISPW = ix['SVR log-mel'], ix['SVR wav2vec 2.0'], ix['target_total'], ix['sec_per_word']
pred = {r[0]: (float(r[ILM]), float(r[IW2]), float(r[ITT]), float(r[ISPW])) for r in rows}
assert len(pred) == 2500, len(pred)

# --- nam diem giam khao (webapp/data/utterances.json, ban copy y het week11_results) ---
utt = {u['id']: u for u in json.loads((ROOT / 'webapp' / 'data' / 'utterances.json').read_text(encoding='utf-8'))}
assert len(utt) == 2500

# --- parquet test: diem corpus muc cau (accuracy/completeness/fluency/prosodic/total) + tu ---
pf = pq.ParquetFile(PARQ / 'test-00000-of-00001.parquet')
corpus, n_test = {}, 0
for b in pf.iter_batches(batch_size=256,
                         columns=['text', 'accuracy', 'completeness', 'fluency', 'prosodic',
                                  'total', 'words', 'audio']):
    for r in b.to_pylist():
        uid = Path((r['audio'] or {}).get('path') or '').stem
        if not uid:
            raise RuntimeError('hang parquet khong co duong dan audio')
        n_test += 1
        y = r['words'] or []
        corpus[uid] = {'text': r['text'], 'acc': float(r['accuracy']), 'compl': float(r['completeness']),
                       'flu': float(r['fluency']), 'pros': float(r['prosodic']), 'total': float(r['total']),
                       'n_words': len(y), 'n_lt5': int(sum(1 for w in y if w['accuracy'] < 5))}
assert n_test == 2500, n_test
assert set(corpus) == set(pred)

# --- kiem chung ma nguon (Muc 2 bao cao): floor(trung vi nam diem) == total, khop tren toan bo test ---
def tt_from_csv(uid):
    return pred[uid][2]

for uid, u in utt.items():
    five = u['five']
    assert len(five) == 5, uid
    assert float(np.floor(np.median(five))) == corpus[uid]['total'] == tt_from_csv(uid), uid

# --- thang diem do duoc tren test (README corpus ghi completeness 0.0-1.0, du lieu can nguoc lai) ---
def mm(k):
    v = [c[k] for c in corpus.values()]
    return [float(min(v)), float(max(v))]
scale = {'accuracy': mm('acc'), 'completeness': mm('compl'), 'fluency': mm('flu'), 'prosodic': mm('pros'),
         'total': mm('total'), 'completeness_documented_range': '0.0-1.0 theo README corpus; du lieu tuan thu thi max den 10'}

# --- nhom completeness == 0 (corpus coi la khong doc du noi dung) ---
z = [uid for uid in corpus if corpus[uid]['compl'] == 0.0]
zt = np.array([corpus[uid]['total'] for uid in z])
zp = np.array([pred[uid][0] for uid in z]); zw = np.array([pred[uid][1] for uid in z])
zb = int(sum(1 for uid in z if corpus[uid]['total'] < 6))
n_all_low = R['below6']['test'][0]
compl_zero = {'n': len(z), 'n_test': n_test, 'mean_total': float(zt.mean()) if len(z) else None,
              'mean_pred_logmel': float(zp.mean()) if len(z) else None,
              'mean_pred_w2v': float(zw.mean()) if len(z) else None,
              'n_below6': zb, 'share_of_all_below6': float(zb / n_all_low)}
ids_zero = sorted(z)

# --- 12 cau total <= 2: nguyen nhan total thap la da dang ---
lt_ids = [r[0] for r in rows if float(r[ITT]) <= 2]
assert len(lt_ids) == R['low_total']['n'], (len(lt_ids), R['low_total']['n'])
low2 = []
for uid in lt_ids:
    c, u, p = corpus[uid], utt[uid], pred[uid]
    low2.append({'id': uid, 'text': c['text'], 'five': u['five'], 'total': c['total'],
                 'acc': c['acc'], 'compl': c['compl'], 'flu': c['flu'], 'pros': c['pros'],
                 'n_words': c['n_words'], 'n_lt5': c['n_lt5'], 'sec_per_word': p[3],
                 'pred_logmel': p[0], 'pred_w2v': p[1]})
low2.sort(key=lambda x: x['total'])
n_zero2 = int(sum(1 for x in low2 if x['compl'] == 0.0))

# --- 5 cau worst5: diem corpus + do am hoc tu dong tu WAV (KHONG phai nghe) ---
def read_wav(path):
    with wave.open(str(path), 'rb') as w:
        assert w.getnchannels() == 1 and w.getsampwidth() == 2 and w.getframerate() == SR
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0

def measure(path):
    x = read_wav(path)
    fl, hop = int(0.025 * SR), int(0.010 * SR)                     # khung 25 ms, buoc 10 ms
    n = 1 + max(0, (len(x) - fl) // hop)
    em = np.stack([x[i * hop:i * hop + fl] for i in range(n)])
    e = np.sqrt(np.mean(em ** 2, axis=1))
    pct_energy = float(np.mean(e > e.max() * 0.08)) if len(e) else 0.0
    return {'peak': float(np.max(np.abs(x))), 'rms_dbfs': float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)),
            'pct_frames': round(pct_energy * 100, 1), 'duration_s': round(len(x) / SR, 2)}

worst5 = []
for uid in W5_IDS:
    c, u, p = corpus[uid], utt[uid], pred[uid]
    rec = {'id': uid, 'text': c['text'], 'five': u['five'], 'total': c['total'],
           'acc': c['acc'], 'compl': c['compl'], 'flu': c['flu'], 'pros': c['pros'],
           'n_words': c['n_words'], 'n_lt5': c['n_lt5'], 'sec_per_word': p[3],
           'pred_logmel': p[0], 'pred_w2v': p[1], 'acoustic': measure(P / 'worst5' / (uid + '.WAV'))}
    old = next(x for x in R['worst5'] if x['id'] == uid)
    assert abs(rec['pred_logmel'] - old['pred_logmel']) < 1e-6 and abs(rec['pred_w2v'] - old['pred_w2v']) < 1e-6, uid
    assert rec['five'] == old['five'], uid
    worst5.append(rec)

# --- su kien corpus da do ngay 9/11/2026 (doc truc tiep tu parquet): 4/5 cau compl 0, 014040122 la 1.7 ---
zero911 = {'014040089', '069020059', '014040090', '069020075'}
assert all(abs(corpus[u]['compl']) < 1e-9 for u in zero911), {u: corpus[u]['compl'] for u in zero911}
assert abs(corpus['014040122']['compl'] - 1.7) < 1e-9, corpus['014040122']['compl']
assert sum(1 for u in W5_IDS if corpus[u]['compl'] == 0.0) == 4, 'worst5 phai gom 4 cau compl == 0 + 1 cau 1.7'

out = {'python': platform.python_version(), 'pyarrow': pyarrow.__version__, 'seconds': round(time.perf_counter() - t0, 1),
       'n_test': n_test, 'scale': scale, 'compl_zero': compl_zero, 'ids_compl_zero': ids_zero,
       'low_total2': low2, 'n_zero_in_low12': n_zero2, 'worst5': worst5, 'n_all_below6_test': n_all_low}
(P / 'week11_completeness.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')

pct = lambda v: f'{v * 100:.1f}%'
log = [f"Week 11 completeness analysis | Python {platform.python_version()} | CPU only | {out['seconds']} s",
       "--- [1] Thang diem corpus do duoc tren 2.500 cau test (min|max) ---",
       f"accuracy {scale['accuracy'][0]:.1f}|{scale['accuracy'][1]:.1f} | completeness {scale['completeness'][0]:.2f}|{scale['completeness'][1]:.2f} | "
       f"fluency {scale['fluency'][0]:.1f}|{scale['fluency'][1]:.1f} | prosodic {scale['prosodic'][0]:.1f}|{scale['prosodic'][1]:.1f} | total {scale['total'][0]:.1f}|{scale['total'][1]:.1f}",
       "(README corpus ghi completeness 0.0-1.0; du lieu thuc toi " + str(scale['completeness'][1]) + ")",
       f"--- [2] floor(median five) == total: ok tren {n_test}/{n_test} cau (sheet nguon: utterances.json + parquet + csv) ---",
       f"--- [3] Nhom completeness == 0: {compl_zero['n']}/{n_test} cau; mean total {compl_zero['mean_total']:.2f}; "
       f"mean pred: logmel {compl_zero['mean_pred_logmel']:.2f}, w2v {compl_zero['mean_pred_w2v']:.2f}; "
       f"below6 {compl_zero['n_below6']}/{len(z)} = {pct(compl_zero['share_of_all_below6'])} cua {n_all_low} bai under 6 ---",
       f"--- [4] Nhom total <= 2: n = {len(low2)}; trong do completeness == 0: {n_zero2} cau (so cau con lai la phat am sai nhung doc du) ---",
       "--- [5] Worst 5 (over = pred_logmel - target): corpus + do am hoc tu dong ---"]
for w in worst5:
    a = w['acoustic']
    log.append(f"{w['id']} total {w['total']:.0f} pred {w['pred_logmel']:.2f}/{w['pred_w2v']:.2f} | acc {w['acc']:.1f} compl {w['compl']:.1f} flu {w['flu']:.1f} pros {w['pros']:.1f} "
               f"| {w['n_lt5']}/{w['n_words']} tu <5 | {a['duration_s']} s | peak {a['peak']:.2f} rms {a['rms_dbfs']:.1f} dBFS | khung co nang luong {a['pct_frames']}%")
log.append("Chu y: do am hoc la SOC tu dong tu WAV, khong thay cho nghe cua nguoi trong nhom.")
(P / 'week11_completeness.log').write_text('\n'.join(log) + '\n', encoding='utf-8')
print('\n'.join(log))
print('COMPLETENESS OK')
