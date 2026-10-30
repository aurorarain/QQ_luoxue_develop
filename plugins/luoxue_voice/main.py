# -*- coding: utf-8 -*-
"""洛雪语音插件：LLM 工具（speak/sing）+ 自然语言语音意图 + 手动命令兜底。

密钥与音色只从容器环境读取，不写进代码。语音意图判断复用
luoxue_social.voice_control，保证群聊与私聊用同一套规则。
"""
import json
import os
import pathlib
import re
import tempfile
import time
import uuid

import aiohttp

from astrbot.api import star, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Record
from astrbot.core.message.message_event_result import MessageChain
from astrbot.core.star.filter.command import GreedyStr
from astrbot.core.star.session_llm_manager import SessionServiceManager

FISH_TTS_URL = "https://api.fish.audio/v1/tts"
FISH_API_KEY = os.getenv("FISH_AUDIO_API_KEY", "").strip()
FISH_MODEL = os.getenv("FISH_AUDIO_MODEL", "s2.1-pro-free").strip()
FISH_REFERENCE_ID = os.getenv(
    "FISH_AUDIO_REFERENCE_ID", "fbe02f8306fc4d3d915e9871722a39d5"
).strip()
FISH_PROXY = os.getenv("FISH_AUDIO_PROXY", "").strip() or None
SING_URL = os.getenv("LUOXUE_SING_URL", "http://127.0.0.1:6102/sing").strip()
SONGS_DIR = os.getenv("LUOXUE_SONGS_DIR", "/AstrBot/data/plugin_data/luoxue_voice/songs").strip()

_FALLBACK_CUE = re.compile(r"语音|音频|录音|声音|嗓子|出声|开口")
_FALLBACK_ACTION = re.compile(r"说|讲|念|读|发|来|听|喊|叫|撒娇|哄|夸|唱")


def wants_voice_reply(text: str) -> bool:
    """Delegate to the shared implementation so group and private chat agree."""
    try:
        from data.plugins.luoxue_social.voice_control import wants_voice_reply as impl

        return impl(text)
    except Exception:
        logger.warning("[luoxue_voice] shared voice intent unavailable, using fallback")
        value = re.sub(r"\s+", "", (text or "").strip())
        if not value or value.startswith("/"):
            return False
        if re.search(r"(?:不要|别|不用|不想|停止|关闭|关掉).{0,6}(?:语音|声音|出声|开口)", value):
            return False
        return bool(_FALLBACK_CUE.search(value) and _FALLBACK_ACTION.search(value))


def _prepare_voice(text: str) -> str:
    try:
        from data.plugins.luoxue_social.voice_control import prepare_voice

        return prepare_voice(text)
    except Exception:
        return text


async def fish_tts(text: str) -> bytes:
    if not FISH_API_KEY:
        raise RuntimeError("未配置 FISH_AUDIO_API_KEY")
    timeout = aiohttp.ClientTimeout(total=180)
    headers = {
        "Authorization": f"Bearer {FISH_API_KEY}",
        "Content-Type": "application/json",
        "model": FISH_MODEL,
    }
    payload = {
        "text": _prepare_voice(text),
        "reference_id": FISH_REFERENCE_ID,
        "format": "wav",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            FISH_TTS_URL,
            headers=headers,
            json=payload,
            timeout=timeout,
            proxy=FISH_PROXY,
        ) as response:
            if response.status != 200:
                detail = (await response.text())[:300]
                raise RuntimeError(f"Fish Audio HTTP {response.status}: {detail}")
            return await response.read()


def _write_wav(wav: bytes, prefix: str) -> str:
    path = os.path.join(tempfile.gettempdir(), f"{prefix}_{int(time.time_ns())}.wav")
    with open(path, "wb") as handle:
        handle.write(wav)
    return path


async def _send_voice(event, wav: bytes, prefix: str):
    """Tool handlers reply through event.send; generator handlers yield instead."""
    path = _write_wav(wav, prefix)
    await event.send(MessageChain([Record(file=path, url=path)]))
    return path


def _owner_ids() -> set:
    """Owner comes from the private settings file, never from a literal in this repository."""
    ids = set()
    path = pathlib.Path(os.getenv("LUOXUE_SETTINGS", "/AstrBot/data/config/luoxue_social_settings.json"))
    try:
        data = json.loads(path.read_text())
        if data.get("owner_qq"):
            ids.add(str(data["owner_qq"]))
    except Exception:
        logger.warning("[luoxue_voice] owner settings unreadable; private voice filter stays empty")
    env = os.getenv("LUOXUE_OWNER_QQ", "").strip()
    if env:
        ids.add(env)
    return ids


OWNER_IDS = _owner_ids()


class VoiceIntentFilter(filter.CustomFilter):
    def filter(self, event, cfg):
        return (
            event.is_private_chat()
            and str(event.get_sender_id()) in OWNER_IDS
            and wants_voice_reply(event.get_message_str())
        )


class Main(star.Star):
    def __init__(self, context: star.Context):
        self.context = context

    # ── LLM 工具：让模型自己判断什么时候该出声 ──────────────

    @filter.llm_tool()
    async def speak(self, event: AstrMessageEvent, text: str) -> str:
        """用洛雪的 AD 学姐音色把一段话读出来，直接把语音发给用户。
        当用户想听你「说话」、要求用语音回复、或说「说句话」「用语音说」时调用。
        text 是你要用户听到的完整内容（用中文，不要带指令）。

        Args:
            text(string): 要读出来的完整内容
        """
        try:
            wav = await fish_tts(text)
            await _send_voice(event, wav, "luoxue_say")
            return "语音已发送给用户。"
        except Exception as exc:
            logger.error(f"[luoxue_voice] speak 失败: {exc}")
            return f"语音生成出错：{exc}"

    @filter.llm_tool()
    async def sing(self, event: AstrMessageEvent, song: str = "") -> str:
        """用洛雪的音色唱一首歌，直接把歌声发给用户。
        当用户想听你「唱歌」、点歌、说「唱首歌」「来一首」时调用。
        song 是歌名（可为空；为空时用歌曲库里第一首）。

        Args:
            song(string): 歌名，可为空
        """
        songs = []
        if os.path.isdir(SONGS_DIR):
            songs = [d for d in os.listdir(SONGS_DIR) if os.path.isdir(os.path.join(SONGS_DIR, d))]
        if not songs:
            return "歌曲库还是空的（songs/ 目录下没有歌曲），暂时唱不了。"
        target = None
        for name in songs:
            if song and (song in name or name in song):
                target = name
                break
        # 只有用户没有指定歌名时，才允许选择歌曲库第一首。
        if target is None and not song:
            target = songs[0]
        if target is None:
            return (
                f"歌曲库里没有《{song}》，目前只有：" + "、".join(songs)
                + "。不要冒充唱了这首歌，也不要播放其他歌曲。"
            )
        song_dir = os.path.join(SONGS_DIR, target)
        files = os.listdir(song_dir)
        vocal = next((os.path.join(song_dir, f) for f in files if f.lower().startswith("vocal")), None)
        accomp = next((os.path.join(song_dir, f) for f in files if f.lower().startswith("accomp")), None)
        if not vocal:
            return f"《{target}》缺少干声文件，唱不了。"
        try:
            timeout = aiohttp.ClientTimeout(total=900)
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    SING_URL,
                    json={"vocal_path": vocal, "accompaniment_path": accomp or "", "transpose": 0},
                    timeout=timeout,
                ) as response:
                    if response.status != 200:
                        return f"唱歌失败（HTTP {response.status}）"
                    wav = await response.read()
            await _send_voice(event, wav, "luoxue_sing")
            return f"《{target}》的歌声已发送给用户。"
        except Exception as exc:
            logger.error(f"[luoxue_voice] sing 失败: {exc}")
            return f"唱歌出错：{exc}"

    # ── 语义识别兜底：模型没调工具也能出声 ──────────────────

    @filter.custom_filter(VoiceIntentFilter)
    async def natural_say(self, event: AstrMessageEvent):
        request = (event.get_message_str() or "").strip()
        if not wants_voice_reply(request):
            return
        event.stop_event()
        try:
            provider = await self.context.get_using_provider_async(event.unified_msg_origin)
            if not provider:
                raise RuntimeError("没有可用的对话模型")
            prompt = (
                "你是洛雪，Alex 的鲸鱼娘 AI 伙伴（不是女友、不是恋人）。语气亲近、活泼、偶尔傲娇，避免客服腔。"
                "用户明确希望听语音。请根据他的具体要求生成要说出口的内容；如果要求朗读指定文字，"
                "就忠实朗读；如果要求自我介绍，就简短自然地自我介绍。只输出最终要朗读的正文，"
                "不要解释工具、语音功能或生成过程，控制在1到3句。\n用户：" + request
            )
            response = await provider.text_chat(
                prompt=prompt,
                session_id=f"luoxue-voice-{uuid.uuid4().hex}",
                persist=False,
            )
            spoken_text = (response.completion_text or "").strip()
            if not spoken_text:
                raise RuntimeError("对话模型没有生成可朗读内容")
            wav = await fish_tts(spoken_text)
            path = _write_wav(wav, "luoxue_natural")
            yield event.chain_result([Record(file=path, url=path)])
        except Exception as exc:
            logger.error(f"[luoxue_voice] 自然语言语音请求失败: {type(exc).__name__}: {exc}")
            yield event.plain_result("这次语音没合成出来，先文字回你。")

    # ── 手动命令兜底 ──────────────────────────────────────

    @filter.command("说话")
    async def say(self, event: AstrMessageEvent, text: GreedyStr):
        """让洛雪把文字说成语音发给你。用法：/说话 想让我说的话"""
        text = (text or "").strip()
        if not text:
            yield event.plain_result("用法：/说话 想让我说的话")
            return
        try:
            wav = await fish_tts(text)
            path = _write_wav(wav, "luoxue")
            yield event.chain_result([Record(file=path, url=path)])
        except Exception as exc:
            logger.error(f"[luoxue_voice] /说话 失败: {exc}")
            yield event.plain_result("这次语音没合成出来，稍后再试。")

    @filter.command("声音")
    async def voice_status(self, event: AstrMessageEvent):
        """查看洛雪声音服务状态"""
        status = {
            "provider": "Fish Audio",
            "model": FISH_MODEL,
            "reference_id": FISH_REFERENCE_ID,
            "api_key": "configured" if FISH_API_KEY else "missing",
        }
        yield event.plain_result(f"洛雪声音服务：{status}")

    @filter.command("关语音")
    async def tts_off(self, event: AstrMessageEvent):
        """关闭自动语音，之后只发文字"""
        await SessionServiceManager.set_tts_status_for_session(event.unified_msg_origin, False)
        yield event.plain_result("好，之后只发文字。想听我说就说「开语音」。")

    @filter.command("开语音")
    async def tts_on(self, event: AstrMessageEvent):
        """开启自动语音，之后每条回复都发语音"""
        await SessionServiceManager.set_tts_status_for_session(event.unified_msg_origin, True)
        yield event.plain_result("好，之后每条回复都发语音。")
