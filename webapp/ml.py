"""Trích đặc trưng và chấm thử một file audio bằng model đã export."""
from pathlib import Path
import bisect, csv, re, threading
import joblib
import numpy as np

P = Path(__file__).parent
MODELS = P / 'models'
DATA = P / 'data'
LOW = 6.0
LOCAL_W2V = MODELS / 'wav2vec2-base'
W2V_NAME = str(LOCAL_W2V) if (LOCAL_W2V / 'config.json').exists() else 'facebook/wav2vec2-base'
LAYERS = (4, 8)

MODEL_LABELS = {
    'wav2vec': 'SVR wav2vec 2.0',
    'logmel': 'SVR log-mel',
    'length': 'SVR chỉ độ dài',
}


def logmel(x, sr=16000):
    frame, hop, nfft, bands = 400, 160, 512, 40
    if len(x) < frame:
        x = np.pad(x, (0, frame - len(x)))
    frames = np.lib.stride_tricks.sliding_window_view(x, frame)[::hop]
    power = abs(np.fft.rfft(frames * np.hanning(frame), n=nfft)) ** 2
    mel = np.linspace(0, 2595 * np.log10(1 + (sr / 2) / 700), bands + 2)
    hz = 700 * (10 ** (mel / 2595) - 1)
    freqs = np.fft.rfftfreq(nfft, 1 / sr)
    lo, mid, hi = hz[:-2, None], hz[1:-1, None], hz[2:, None]
    bank = np.maximum(0, np.minimum((freqs - lo) / (mid - lo), (hi - freqs) / (hi - mid)))
    return np.log(np.maximum(power @ bank.T, 1e-10)).T


def read_audio(path):
    """Đọc WAV 16 kHz mono; fallback soundfile cho file đã convert."""
    import wave as wavelib
    try:
        with wavelib.open(str(path)) as w:
            sr, n = w.getframerate(), w.getnframes()
            ch, sw = w.getnchannels(), w.getsampwidth()
            raw = w.readframes(n)
        if sw == 2:
            x = np.frombuffer(raw, dtype='<i2').astype(np.float64) / 32768
        elif sw == 4:
            x = np.frombuffer(raw, dtype='<i4').astype(np.float64) / 2147483648
        else:
            raise ValueError('unsupported sample width')
        if ch > 1:
            x = x.reshape(-1, ch).mean(1)
    except Exception:
        import soundfile as sf
        x, sr = sf.read(str(path), dtype='float64', always_2d=True)
        x = x.mean(1)
    x = np.asarray(x, dtype=np.float64)
    if sr != 16000:
        t = np.arange(len(x)) / sr
        t2 = np.arange(0, t[-1] if len(t) else 0, 1 / 16000)
        x = np.interp(t2, t, x) if len(t) else x
        sr = 16000
    return x, sr


def analyze_speech(x, sr, transcript=''):
    """Đo tốc độ và các khoảng lặng — không suy đoán lỗi phát âm."""
    duration = len(x) / sr
    words = len(transcript.split()) if transcript and transcript.strip() else 0
    spw = duration / words if words else None
    median_ref = 0.578
    speed = {
        'sec_per_word': round(spw, 2) if spw else None,
        'median_ref': median_ref,
        'ratio': round(spw / median_ref, 2) if spw else None,
        'label': None,
    }
    if spw:
        ratio = spw / median_ref
        speed['label'] = 'nhanh' if ratio < 0.85 else ('chậm' if ratio > 1.15 else 'vừa')

    out = {
        'pauses': [], 'pause_count': 0, 'pause_total': 0.0, 'pause_min': 0.25,
        'words': words, 'speed': speed,
        'punctuation_marks': len(re.findall(r'[,.;:!?]', transcript or '')),
        'threshold_db': None,
    }
    if duration < 0.45 or len(x) < 400:
        return out

    frame, hop = 400, 160
    frames = np.lib.stride_tricks.sliding_window_view(x, frame)[::hop]
    rms = np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=1))
    db = 20 * np.log10(rms + 1e-9)
    p10, p90 = np.percentile(db, [10, 90])
    thr = max(float(p10) + 7.0, float(p90) - 26.0, -52.0)
    silent = db < thr
    out['threshold_db'] = round(thr, 1)

    voiced = np.flatnonzero(~silent)
    if not len(voiced):
        return out
    first, last = int(voiced[0]), int(voiced[-1])
    if last - first < 2:
        return out

    runs, start = [], None
    for i, is_silent in enumerate(silent[first:last + 1]):
        if is_silent and start is None:
            start = i
        elif not is_silent and start is not None:
            runs.append((start, i))
            start = None
    if start is not None:
        runs.append((start, last + 1 - first))

    offset = first * hop / sr
    raw = []
    for a, b in runs:
        start_s = offset + a * hop / sr
        end_s = offset + b * hop / sr
        if end_s - start_s >= out['pause_min']:
            raw.append([start_s, end_s])
    merged = []
    for start_s, end_s in raw:
        if merged and start_s - merged[-1][1] < 0.12:
            merged[-1][1] = end_s
        else:
            merged.append([start_s, end_s])
    pauses = [
        {'start': round(s, 2), 'end': round(e, 2), 'dur': round(e - s, 2)}
        for s, e in merged
    ]
    out['pauses'] = pauses
    out['pause_count'] = len(pauses)
    out['pause_total'] = round(sum(p['dur'] for p in pauses), 2)
    return out


class Scorer:
    def __init__(self):
        self.models = {}
        self.meta = {}
        self.dist = {}
        self.cutoffs = {}
        self.w2v = None
        self.fe = None
        self.w2v_ready = False
        self.w2v_error = None
        self.lock = threading.Lock()
        # RLock: load_w2v() giữ khóa rồi gọi _embed(); khóa thường sẽ tự khóa chính nó.
        self.w2v_lock = threading.RLock()

    def load_models(self):
        for key, fname in [('logmel', 'svr_logmel.joblib'), ('wav2vec', 'svr_w2v.joblib'),
                           ('length', 'svr_length.joblib')]:
            self.models[key] = joblib.load(MODELS / fname)
        self.models['lr'] = joblib.load(MODELS / 'lr_w2v.joblib')
        self.meta = __import__('json').loads((MODELS / 'meta.json').read_text(encoding='utf-8'))
        rows = list(csv.DictReader((DATA / 'test_predictions_week11.csv').open()))
        for key, col in [('wav2vec', 'SVR wav2vec 2.0'), ('logmel', 'SVR log-mel'), ('length', 'SVR chỉ độ dài')]:
            arr = np.sort(np.array([float(r[col]) for r in rows]))
            self.dist[key] = arr
            self.cutoffs[key] = {'p20': float(np.quantile(arr, .2)), 'p50': float(np.quantile(arr, .5))}
        return self

    def load_w2v(self):
        if self.w2v_ready:
            return
        with self.w2v_lock:
            if self.w2v_ready:
                return
            try:
                import torch
                from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2Model
                torch.set_num_threads(6)
                self.fe = Wav2Vec2FeatureExtractor.from_pretrained(W2V_NAME)
                model = Wav2Vec2Model.from_pretrained(W2V_NAME).eval()
                for p in model.parameters():
                    p.requires_grad_(False)
                self.w2v = model
                self.w2v_ready = True
                self.w2v_error = None
                # warm-up để lần chấm đầu không bị chậm
                self._embed(np.zeros(16000, dtype=np.float64))
            except Exception as e:  # pragma: no cover
                self.w2v_error = str(e)
                self.w2v_ready = False

    def _embed(self, x):
        import torch
        with self.w2v_lock, torch.inference_mode():
            inp = self.fe(x, sampling_rate=16000, return_tensors='pt').input_values
            hs = self.w2v(inp, output_hidden_states=True).hidden_states
            return {l: hs[l][0].mean(0).cpu().numpy().astype(np.float64) for l in LAYERS}

    def score_file(self, path, transcript='', speech_text=None):
        if not self.w2v_ready:
            self.load_w2v()
            if not self.w2v_ready:
                raise RuntimeError(f'wav2vec chưa sẵn sàng: {self.w2v_error}')
        x, sr = read_audio(path)
        duration = len(x) / sr
        if duration < 0.25:
            raise ValueError('Audio quá ngắn (dưới 0,25 giây).')
        if duration > 30:
            raise ValueError('Audio quá dài (tối đa 30 giây). Cắt bớt rồi thử lại.')
        m = logmel(x, sr)
        f_logmel = np.concatenate([m.mean(1), m.std(1), [duration]])
        emb = self._embed(x)
        words = len(transcript.split()) if transcript and transcript.strip() else 0
        preds = {
            'wav2vec': float(self.models['wav2vec'].predict([emb[8]])[0]),
            'logmel': float(self.models['logmel'].predict([f_logmel])[0]),
            'length': None,
        }
        if words:
            spw = duration / words
            preds['length'] = float(self.models['length'].predict([[duration, spw]])[0])
        proba = float(self.models['lr'].predict_proba([emb[4]])[0, 1])
        score = preds['wav2vec']
        arr = self.dist['wav2vec']
        pct = bisect.bisect_right(arr, score) / len(arr)
        if pct <= .2:
            priority, plabel = 'high', 'Ưu tiên cao — nằm trong 20% điểm dự đoán thấp nhất'
        elif pct <= .5:
            priority, plabel = 'medium', 'Theo dõi — nằm trong nửa thấp của danh sách'
        else:
            priority, plabel = 'low', 'Ưu tiên thấp — không nằm trong nhóm nghe trước'
        return {
            'score': round(score, 2),
            'percentile': round(pct * 100, 1),
            'priority': priority,
            'priority_label': plabel,
            'below6_prob': round(proba, 3),
            'predictions': {k: (round(v, 2) if v is not None else None) for k, v in preds.items()},
            'duration': round(duration, 2),
            'words': words,
            'sec_per_word': round(duration / words, 2) if words else None,
            'cutoffs': {k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in self.cutoffs.items()},
            'speech': analyze_speech(x, sr, transcript if speech_text is None else speech_text),
            'model': self.meta.get('trained_at'),
        }

    def status(self):
        return {'models': bool(self.models), 'wav2vec': self.w2v_ready, 'error': self.w2v_error}
