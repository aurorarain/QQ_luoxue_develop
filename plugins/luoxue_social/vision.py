"""Bounded inbound image extraction for one event.

Only components attached to the current message are read. Nothing here scans caches,
private diaries or other conversations, so a group call can never reach private media.
"""
import asyncio
import base64
import io

from astrbot.api import logger

MAX_IMAGES = 2
MAX_SIDE = 1280
MAX_DECODED = 4_000_000  # bytes accepted before compression
JPEG_QUALITY = 82


def attachment_note(count, private=False):
    """Instruction text; counted attachments are the only images the model may claim to see."""
    if count <= 0:
        return ''
    if private:
        return ('\n本轮私聊附带%d张图片，你可以据实描述画面内容。这些图片属于私人内容，'
                '不得出现在群聊、群表情或公开说说里。没有附带的图片不能声称看过。' % count)
    return ('\n本轮随消息附带%d张公开群图片，你可以据实描述画面内容；'
            '没有附带的图片、视频和群历史仍不能声称看过。' % count)


def _decode(encoded):
    """convert_to_base64 may return raw base64, base64:// or a data: URL."""
    if not isinstance(encoded, str) or not encoded:
        return None
    if encoded.startswith('data:'):
        encoded = encoded.split(',', 1)[-1]
    if encoded.startswith('base64://'):
        encoded = encoded[len('base64://'):]
    try:
        return base64.b64decode(encoded, validate=False)
    except Exception:
        return None


def _to_jpeg_data_url(raw, max_side=MAX_SIDE):
    """Downscale in a worker thread; return None when the bytes are not a usable image."""
    from PIL import Image as PILImage
    with PILImage.open(io.BytesIO(raw)) as image:
        image.load()
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        image.thumbnail((max_side, max_side))
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=JPEG_QUALITY, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode()


def to_data_url(raw, max_side=MAX_SIDE):
    """Public helper for other modules (e.g. reviewing a generated picture)."""
    return _to_jpeg_data_url(raw, max_side)


async def attachment_images(event, limit=MAX_IMAGES):
    """Return (data_urls, report) for at most `limit` images of this exact event."""
    from astrbot.api.message_components import Image
    urls = []
    report = {'attached': 0, 'skipped': 0}
    for component in event.get_messages() or []:
        if not isinstance(component, Image):
            continue
        if len(urls) >= limit:
            report['skipped'] += 1
            continue
        try:
            raw = _decode(await component.convert_to_base64())
        except Exception as exc:
            report['skipped'] += 1
            logger.info('[luoxue_vision] image unavailable: %s', type(exc).__name__)
            continue
        if not raw or len(raw) > MAX_DECODED:
            report['skipped'] += 1
            continue
        try:
            converted = await asyncio.to_thread(_to_jpeg_data_url, raw)
        except Exception as exc:
            report['skipped'] += 1
            logger.info('[luoxue_vision] image decode skipped: %s', type(exc).__name__)
            continue
        if not converted:
            report['skipped'] += 1
            continue
        urls.append(converted)
        report['attached'] += 1
    return urls, report
