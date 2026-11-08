"""听懂群友/主人的语音：本地 faster-whisper 转写，转完立刻删临时音频。"""
import asyncio
import os
import threading

from astrbot.api import logger

MODEL_NAME = os.environ.get('LUOXUE_ASR_MODEL', 'Systran/faster-whisper-small')
MODEL_ROOT = os.environ.get('LUOXUE_ASR_ROOT', '/AstrBot/data/plugin_data/luoxue_social/asr-models')

_model = None
_lock = threading.Lock()


def _load():
    global _model
    with _lock:
        if _model is not None:
            return _model
        from faster_whisper import WhisperModel
        os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
        os.environ.setdefault('HF_HUB_DISABLE_XET', '1')
        _model = WhisperModel(MODEL_NAME, device='cpu', compute_type='int8',
                              download_root=MODEL_ROOT, cpu_threads=4)
        logger.info('[luoxue_asr] model loaded: %s', MODEL_NAME)
        return _model


def transcribe_file(path):
    model = _load()
    segments, _info = model.transcribe(path, language='zh', vad_filter=True,
                                       beam_size=1, condition_on_previous_text=False)
    text = ''.join(segment.text for segment in segments).strip()
    return text


def _cleanup(*paths):
    for path in paths:
        if not path:
            continue
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception:
            pass


async def transcribe_record(record):
    """把一个语音组件转成文字，并删除下载/转换产生的临时文件。"""
    local = ''
    try:
        local = await record.convert_to_file_path()
        text = await asyncio.to_thread(transcribe_file, local)
        return (text or '').strip()
    except Exception as exc:
        logger.info('[luoxue_asr] transcribe failed: %s', type(exc).__name__)
        return ''
    finally:
        _cleanup(local)
