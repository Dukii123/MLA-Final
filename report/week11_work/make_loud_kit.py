import wave, numpy as np, json
from pathlib import Path

P = Path(__file__).parent
K = P / 'listen_kit'
sr = 16000


def read(f):
    with wave.open(str(f), 'rb') as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0


def write(f, x):
    y = np.clip(x, -1, 1)
    with wave.open(str(f), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((y * 32767).astype(np.int16).tobytes())


def beep(dur=0.15, freq=1000, amp=0.25):
    t = np.arange(int(dur * sr)) / sr
    env = np.minimum(1, np.minimum(t / 0.01, (dur - t) / 0.02))
    return (amp * env * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def trim(x):
    fl = int(0.02 * sr); n = len(x) // fl
    e = np.sqrt(np.mean(x[:n * fl].reshape(n, fl) ** 2, axis=1))
    thr = max(e.max() * 0.08, 10 ** (-45 / 20))
    idx = np.where(e > thr)[0]
    if len(idx) == 0:
        return x, 0, len(x)
    a = max(0, int(idx[0] * fl - 0.08 * sr)); b = min(len(x), int((idx[-1] + 1) * fl + 0.08 * sr))
    return x[a:b], a, b


rows = json.load(open(K / 'listen_times.json', encoding='utf-8'))
parts = [np.zeros(int(0.3 * sr), dtype=np.float32)]
for i, r in enumerate(rows, 1):
    x = read(P / 'worst5' / (r['id'] + '.WAV'))
    y, a, b = trim(x)
    y = y * (0.9 / max(float(np.max(np.abs(y))), 1e-6))
    print(r['id'], f'trim {a/sr:.2f}-{b/sr:.2f}s = {(b-a)/sr:.2f}s, peak 0.9')
    for k in range(3):
        parts += [beep(), np.zeros(int(0.15 * sr), dtype=np.float32), y, np.zeros(int(0.45 * sr), dtype=np.float32)]
    parts.append(np.zeros(int(0.8 * sr), dtype=np.float32))
out = np.concatenate(parts)
write(K / 'worst5_nghe_to.wav', out)
print('loud file', round(len(out) / sr, 2), 's')

t = np.arange(int(1.5 * sr)) / sr
tone = (0.5 * np.sin(2 * np.pi * 440 * t) * np.minimum(1, np.minimum(t / 0.01, (1.5 - t) / 0.02))).astype(np.float32)
write(K / 'test_tone.wav', tone)
print('tone 1.5 s')
