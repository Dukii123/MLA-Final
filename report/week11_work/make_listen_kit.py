import json, wave, os, numpy as np
from pathlib import Path

P = Path(__file__).parent
OUT = P / 'listen_kit'
OUT.mkdir(exist_ok=True)
R = json.load(open(P / 'week11_results.json', encoding='utf-8'))
items = R['worst5']


def read_wav(path):
    with wave.open(str(path), 'rb') as w:
        assert w.getnchannels() == 1 and w.getsampwidth() == 2 and w.getframerate() == 16000
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    return x, 16000


def write_wav(path, x, sr):
    y = np.clip(x, -1, 1)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((y * 32767).astype(np.int16).tobytes())

sr = 16000
gap = np.zeros(int(2.0 * sr), dtype=np.float32)
lead = np.zeros(int(0.75 * sr), dtype=np.float32)
parts = [lead]
rows = []
t = 0.75
for i, it in enumerate(items, 1):
    src = P / 'worst5' / (it['id'] + '.WAV')
    x, _ = read_wav(src)
    peak = float(np.max(np.abs(x)))
    gain = 0.9 / peak if peak > 0 else 1.0
    y = x * gain
    dst = OUT / f'{i}_{it["id"]}_tang_am.wav'
    write_wav(dst, y, sr)
    dur = len(y) / sr
    rows.append(dict(order=i, id=it['id'], file=dst.name, start=round(t, 2), end=round(t + dur, 2),
                     gain=round(gain, 2), peak_in=round(peak, 3), dur=round(dur, 2),
                     text=it['text'], five=it['five'], total=it['total'],
                     pred_logmel=it['pred_logmel'], pred_w2v=it['pred_w2v'],
                     spw=it['words_per_s']))
    parts.append(y); parts.append(gap)
    t += dur + 2.0
combined = np.concatenate(parts)
write_wav(OUT / 'worst5_nghe_nhanh.wav', combined, sr)
json.dump(rows, open(OUT / 'listen_times.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for r in rows:
    print(f"{r['order']}. {r['id']}  {r['start']:5.2f}-{r['end']:5.2f}s  gain x{r['gain']:.1f}  | {r['text']}")
print('combined', round(len(combined) / sr, 2), 's ->', OUT / 'worst5_nghe_nhanh.wav')
