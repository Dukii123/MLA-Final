"""Web demo nội bộ cho kết quả tuần 11 — chạy local, không gửi dữ liệu ra ngoài."""
from pathlib import Path
import json, re, shutil, subprocess, tempfile, threading, time, uuid
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ml import Scorer

P = Path(__file__).parent
DATA = P / 'data'
STATIC = P / 'static'
AUDIO_DIR = DATA / 'speechocean762' / 'WAVE'
WORST_DIR = DATA / 'worst5'
UPLOAD_DIR = DATA / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def _prune_uploads(keep=60, max_age=24 * 3600):
    """Giữ tối đa 60 file nghe lại gần nhất, xoá file cũ hơn 24 giờ."""
    now = time.time()
    files = sorted(UPLOAD_DIR.glob('*.wav'), key=lambda p: p.stat().st_mtime, reverse=True)
    for i, p in enumerate(files):
        try:
            if i >= keep or now - p.stat().st_mtime > max_age:
                p.unlink()
        except OSError:
            pass


app = FastAPI(title='MLA Nhóm 05 — Demo tuần 11')
scorer = Scorer()
audio_map = {}
audio_ready = threading.Event()

def _index_audio():
    for f in AUDIO_DIR.glob('SPEAKER*/*.WAV'):
        audio_map[f.stem] = f
    audio_ready.set()

@app.on_event('startup')
def startup():
    _prune_uploads()
    scorer.load_models()
    threading.Thread(target=_index_audio, daemon=True).start()
    threading.Thread(target=scorer.load_w2v, daemon=True).start()

app.mount('/static', StaticFiles(directory=str(STATIC)), name='static')

def json_file(name):
    p = DATA / name
    if not p.exists():
        raise HTTPException(404, f'Thiếu {name}')
    return FileResponse(p, media_type='application/json')

@app.get('/')
def index():
    return FileResponse(STATIC / 'index.html')

@app.get('/api/meta')
def api_meta():
    return json_file('meta.json')

@app.get('/api/results')
def api_results():
    return json_file('results.json')

@app.get('/api/utterances')
def api_utterances():
    return json_file('utterances.json')

@app.get('/api/status')
def status():
    return {'ok': True, 'audio': len(audio_map), **scorer.status()}

@app.get('/audio/{utt_id}')
def audio(utt_id: str):
    if not re.fullmatch(r'\d{9}', utt_id):
        raise HTTPException(404, 'Mã bài không hợp lệ')
    audio_ready.wait(timeout=10)
    p = audio_map.get(utt_id)
    if not p:
        raise HTTPException(404, 'Không có file audio cho bài này')
    return FileResponse(p, media_type='audio/wav', filename=f'{utt_id}.WAV')

@app.get('/audio/worst5/{utt_id}')
def worst_audio(utt_id: str):
    if not re.fullmatch(r'\d{9}', utt_id):
        raise HTTPException(404, 'Mã bài không hợp lệ')
    p = WORST_DIR / f'{utt_id}.WAV'
    if not p.exists():
        raise HTTPException(404, 'Không có file audio')
    return FileResponse(p, media_type='audio/wav', filename=f'{utt_id}.WAV')

@app.get('/audio/upload/{token}')
def uploaded_audio(token: str):
    if not re.fullmatch(r'[a-f0-9]{32}', token):
        raise HTTPException(404, 'Mã audio không hợp lệ')
    p = UPLOAD_DIR / f'{token}.wav'
    if not p.exists():
        raise HTTPException(404, 'File nghe lại đã bị xoá')
    return FileResponse(p, media_type='audio/wav', filename='upload.wav')

@app.get('/api/score-sample/{utt_id}')
def score_sample(utt_id: str, transcript: str = ''):
    if not re.fullmatch(r'\d{9}', utt_id):
        raise HTTPException(404, 'Mã bài không hợp lệ')
    audio_ready.wait(timeout=10)
    p = audio_map.get(utt_id)
    if not p:
        raise HTTPException(404, 'Không có file audio cho bài này')
    u = _utterances().get(utt_id)
    speech_text = transcript.strip() or (u['text'] if u else '')
    try:
        out = scorer.score_file(p, transcript, speech_text=speech_text)
    except Exception as e:
        raise HTTPException(500, f'Không chấm được: {e}')
    out['audio_url'] = f'/audio/{utt_id}'
    if u:
        out['ground_truth'] = {
            'id': u['id'], 'text': u['text'], 'five': u['five'], 'total': u['total'],
            'below6': u['below6'], 'pred_report': {
                'wav2vec': u['pred'].get('SVR wav2vec 2.0'),
                'logmel': u['pred'].get('SVR log-mel'),
                'length': u['pred'].get('SVR chỉ độ dài'),
            },
        }
    return out

def _utterances():
    cache = getattr(_utterances, '_cache', None)
    if cache is None:
        rows = json.loads((DATA / 'utterances.json').read_text(encoding='utf-8'))
        cache = {r['id']: r for r in rows}
        _utterances._cache = cache
    return cache

@app.post('/api/score')
async def score(file: UploadFile = File(...), transcript: str = Form('')):
    raw = await file.read()
    if len(raw) > 25 * 1024 * 1024:
        raise HTTPException(413, 'File quá lớn (giới hạn 25 MB).')
    if len(raw) < 2000:
        raise HTTPException(400, 'File audio quá nhỏ hoặc rỗng.')
    if len(transcript) > 300:
        transcript = transcript[:300]
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / 'upload'
        dst = Path(td) / 'audio.wav'
        src.write_bytes(raw)
        ffmpeg = shutil.which('ffmpeg')
        try:
            if ffmpeg:
                subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(src),
                                '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(dst)],
                               check=True, timeout=90)
            else:
                shutil.copyfile(src, dst)
            out = scorer.score_file(dst, transcript)
            token = uuid.uuid4().hex
            shutil.copyfile(dst, UPLOAD_DIR / f'{token}.wav')
            out['audio_url'] = f'/audio/upload/{token}'
            _prune_uploads()
        except subprocess.TimeoutExpired:
            raise HTTPException(400, 'Xử lý audio quá lâu, thử file ngắn hơn.')
        except subprocess.CalledProcessError:
            raise HTTPException(400, 'Không đọc được file audio. Thử WAV/MP3/M4A.')
        except Exception as e:
            raise HTTPException(400, f'Không chấm được file: {e}')
    return out

@app.exception_handler(404)
def not_found(request, exc):  # pragma: no cover
    return JSONResponse({'detail': str(exc.detail)}, status_code=404)
