"""把搜索结果里的图片、音频、视频真的"看/听"一遍。

- 图片：下载 -> dataURL，交给视觉模型
- 音频：下载 -> 本地 faster-whisper 转写 -> 文字
- 视频：ffmpeg 抽 5 帧 -> 当图片
"""
import asyncio
import os
import re
import subprocess
import tempfile
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0 Safari/537.36"
IMG_EXT = (".jpg", ".jpeg", ".png", ".gif", ".webp")
AUD_EXT = (".mp3", ".m4a", ".wav", ".aac", ".ogg", ".flac")
VID_EXT = (".mp4", ".webm", ".mov", ".mkv")


def _download(url, timeout=15, limit=12 * 1024 * 1024):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(limit)


def _kind(url):
    low = url.lower().split("?")[0]
    if low.endswith(IMG_EXT):
        return "image"
    if low.endswith(AUD_EXT):
        return "audio"
    if low.endswith(VID_EXT):
        return "video"
    return ""


def _frames(path, count=5):
    out = []
    for i in range(count):
        target = path + ".%d.jpg" % i
        try:
            subprocess.run(["ffmpeg", "-y", "-ss", str(i * 3), "-i", path, "-frames:v", "1", "-q:v", "4", target],
                           capture_output=True, timeout=25)
            if os.path.exists(target) and os.path.getsize(target) > 1000:
                out.append(target)
        except Exception:
            break
    return out


def _transcribe(path):
    try:
        from faster_whisper import WhisperModel
        import pathlib as _p
        model_dir = "/AstrBot/data/plugin_data/luoxue_social/asr-models"
        model = WhisperModel(model_dir, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(path, language="zh", vad_filter=True)
        return " ".join(s.text.strip() for s in segments)[:800]
    except Exception:
        return ""


async def enrich(text, max_items=3, max_images=3):
    """返回 (额外文字, 图片 dataURL 列表)。"""
    from .vision import to_data_url
    urls = re.findall(r"https?://[^\s\)\]\"'<>]+", str(text or ""))[:max_items]
    notes, images = [], []
    for url in urls:
        kind = _kind(url)
        if not kind:
            continue
        try:
            raw = await asyncio.to_thread(_download, url)
        except Exception:
            continue
        if kind == "image":
            try:
                data_url = await asyncio.to_thread(to_data_url, raw, 768)
                if data_url and len(images) < max_images:
                    images.append(data_url)
                    notes.append("看了一张图：" + url[:80])
            except Exception:
                pass
        elif kind == "video":
            path = None
            try:
                fd, path = tempfile.mkstemp(suffix=".mp4")
                os.write(fd, raw)
                os.close(fd)
                frames = await asyncio.to_thread(_frames, path, 4)
                for frame in frames:
                    if len(images) >= max_images:
                        break
                    with open(frame, "rb") as handle:
                        data_url = await asyncio.to_thread(to_data_url, handle.read(), 768)
                    if data_url:
                        images.append(data_url)
                notes.append("看了一段视频（抽了 %d 帧）" % len(frames))
            except Exception:
                pass
            finally:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass
        elif kind == "audio":
            path = None
            try:
                fd, path = tempfile.mkstemp(suffix=".mp3")
                os.write(fd, raw)
                os.close(fd)
                spoken = await asyncio.to_thread(_transcribe, path)
                if spoken:
                    notes.append("听了一段音频，内容是：「%s」" % spoken[:200])
            except Exception:
                pass
            finally:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass
    return "\n".join(notes), images
