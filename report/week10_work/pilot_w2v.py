from pathlib import Path
import sys, csv, time, wave, json
import numpy as np, torch
from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2Model

# Chay thu wav2vec 2.0 base tren 50 cau de do thoi gian that truoc khi chay ca 5.000 cau (CPU va GPU Apple MPS).
P = Path(__file__).parent
root = Path(sys.argv[1]) if len(sys.argv) > 1 else P.parent/'week09_work'/'data'/'speechocean762'
NAME, N, WARM = 'facebook/wav2vec2-base', 50, 3
torch.set_num_threads(8)
fe = Wav2Vec2FeatureExtractor.from_pretrained(NAME); base = Wav2Vec2Model.from_pretrained(NAME).eval()
rows = list(csv.DictReader((P/'split_manifest.csv').open()))[:N+WARM]
wavs = {f.stem: f for f in (root/'WAVE').glob('SPEAKER*/*.WAV')}
def load(u):
    with wave.open(str(wavs[u])) as w: return np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(np.float32)/32768
audio = [load(r['utterance_id']) for r in rows]
out = {'model': NAME, 'n': N, 'warmup': WARM, 'audio_seconds': float(sum(len(x) for x in audio[WARM:])/16000)}
devices = ['cpu'] + (['mps'] if torch.backends.mps.is_available() else [])
for dev in devices:
    m = base.to(dev)
    with torch.inference_mode():
        times = []
        for i, x in enumerate(audio):
            t = time.perf_counter(); hs = m(fe(x, sampling_rate=16000, return_tensors='pt').input_values.to(dev), output_hidden_states=True).hidden_states
            _ = hs[8][0].mean(0).cpu(); times.append(time.perf_counter() - t)
    sec = float(np.sum(times[WARM:])); out[dev] = {'seconds': sec, 'ms_per_utt': sec/N*1000, 'estimate_5000_minutes': sec/N*5000/60}
(P/'pilot_w2v.json').write_text(json.dumps(out, indent=2))
print(f"--- [0] Pilot: wav2vec 2.0 base on {N} utterances ({out['audio_seconds']:.0f} s audio, {WARM} warm-up not timed) ---")
for dev in devices:
    d = out[dev]; print(f"{dev.upper():4s}: {d['seconds']:.1f} s = {d['ms_per_utt']:.0f} ms/utt -> estimate for 5,000 utt: {d['estimate_5000_minutes']:.1f} min")
