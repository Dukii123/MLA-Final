from pathlib import Path
import sys, csv, time, wave, json, platform
import numpy as np, torch, transformers
from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2Model

# Embedding wav2vec 2.0 base (huan luyen san, khong fine-tune): trung binh theo thoi gian cua tang 4, 8, 12.
P = Path(__file__).parent
root = Path(sys.argv[1]) if len(sys.argv) > 1 else P.parent/'week09_work'/'data'/'speechocean762'
device = sys.argv[2] if len(sys.argv) > 2 else 'cpu'
NAME, LAYERS = 'facebook/wav2vec2-base', [4, 8, 12]
torch.set_num_threads(8)
t0 = time.perf_counter()
fe = Wav2Vec2FeatureExtractor.from_pretrained(NAME); model = Wav2Vec2Model.from_pretrained(NAME).eval().to(device)
load_seconds = time.perf_counter() - t0
rows = list(csv.DictReader((P/'split_manifest.csv').open()))
wavs = {f.stem: f for f in (root/'WAVE').glob('SPEAKER*/*.WAV')}
E = np.zeros((len(rows), len(LAYERS), 768), dtype=np.float32); audio_seconds = 0
t = time.perf_counter()
with torch.inference_mode():
    for i, r in enumerate(rows):
        with wave.open(str(wavs[r['utterance_id']])) as w:
            x = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(np.float32)/32768; audio_seconds += len(x)/16000
        inp = fe(x, sampling_rate=16000, return_tensors='pt').input_values.to(device)
        hs = model(inp, output_hidden_states=True).hidden_states
        E[i] = torch.stack([hs[l][0].mean(0) for l in LAYERS]).cpu().numpy()
        if (i+1) % 1000 == 0: print(f'{i+1}/{len(rows)} utterances, {time.perf_counter()-t:.0f} s', flush=True)
extract_seconds = time.perf_counter() - t
np.savez_compressed(P/'features_w2v_layers.npz', utterance_id=[r['utterance_id'] for r in rows], layers=LAYERS, E=E.astype(np.float16))
info = {'model': NAME, 'layers': LAYERS, 'device': device, 'torch': torch.__version__, 'transformers': transformers.__version__, 'python': platform.python_version(),
        'n_utterances': len(rows), 'audio_hours': audio_seconds/3600, 'model_load_seconds': load_seconds, 'extract_seconds': extract_seconds}
(P/'w2v_run.json').write_text(json.dumps(info, indent=2))
print(f"wav2vec 2.0 base ({NAME}) on {device}: {len(rows)} utterances, {audio_seconds/3600:.2f} h audio, extract {extract_seconds:.0f} s ({extract_seconds/len(rows)*1000:.0f} ms/utt)")
