"""贴吧读写：用主人授权的 Cookie 走 HTTP，不依赖浏览器。

只做真实账号本来就能做的事：看吧、看帖、回帖。发主题帖默认关闭，
需要 主人 私聊明确要求才走。
"""
import json
import os
import re
import time
import urllib.parse
import urllib.request

NODE_STATE = '/AstrBot/data/plugin_data/luoxue_social/node_state.json'
NODE_ONLINE_WINDOW = 90


def node_status():
    """本地电脑上那个"媒体节点"在不在线。"""
    try:
        with open(NODE_STATE, encoding='utf-8') as handle:
            data = json.load(handle)
    except Exception:
        return {'online': False, 'last_seen': 0, 'name': ''}
    seen = float(data.get('last_seen') or 0)
    return {'online': time.time() - seen < NODE_ONLINE_WINDOW,
            'last_seen': seen, 'name': str(data.get('name') or '')}


def offline_note():
    status = node_status()
    if status['online']:
        return ''
    when = (time.strftime('%m-%d %H:%M', time.localtime(status['last_seen']))
            if status['last_seen'] else '还没连过')
    return ('主人 的电脑没开（上次在线：%s），所以贴吧和抖音都刷不了；'
            '别的照常，可以等电脑开了再看。' % when)


COOKIE_FILES = (
    '/AstrBot/data/plugin_data/luoxue_social/tieba_cookies.txt',
)
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
PROXY = os.getenv('LUOXUE_HTTP_PROXY', 'http://mihomo:7890')


def _cookie():
    for path in COOKIE_FILES:
        try:
            with open(path, encoding='utf-8') as handle:
                raw = handle.read().strip()
            if raw:
                return raw
        except Exception:
            continue
    return ''


def available():
    return bool(_cookie())


def _open(url, data=None, headers=None, timeout=20):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    req.add_header('User-Agent', UA)
    req.add_header('Cookie', _cookie())
    req.add_header('Referer', 'https://tieba.baidu.com/')
    handlers = []
    if PROXY:
        handlers.append(urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY}))
    opener = urllib.request.build_opener(*handlers)
    with opener.open(req, timeout=timeout) as resp:
        raw = resp.read()
    for enc in ('utf-8', 'gb18030'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', 'ignore')


def _strip(html):
    text = re.sub(r'<script.*?</script>', ' ', html, flags=re.S)
    text = re.sub(r'<style.*?</style>', ' ', text, flags=re.S)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'</(p|div|li|tr)>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    return re.sub(r'\n{3,}', '\n\n', text).strip()


TOKEN_FILES = ('/AstrBot/data/plugin_data/luoxue_social/node_token.txt',)


def _api(path, payload=None, timeout=25):
    base = os.getenv('LUOXUE_API', '')
    if not base:
        raise RuntimeError('LUOXUE_API is not configured')
    token = ''
    for path_token in TOKEN_FILES:
        try:
            with open(path_token, encoding='utf-8') as handle:
                token = handle.read().strip()
            if token:
                break
        except Exception:
            continue
    url = base.rstrip('/') + path
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(url, data=data, method='POST' if data else 'GET',
                                 headers={'X-Node-Token': token,
                                          'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8') or '{}')


def _via_node(kind, params, timeout=45):
    """把任务派给 主人 的电脑执行，等她回传结果。"""
    if not node_status()['online']:
        return None
    try:
        pushed = _api('/roomapi/node/push', {'kind': kind, 'params': params})
        if not pushed.get('ok'):
            return None
        job_id = pushed.get('id')
        done = _api('/roomapi/node/result?id=%s&wait=%d' % (job_id, timeout), timeout=timeout + 10)
        if done.get('ok'):
            return str(done.get('result') or '')
    except Exception:
        return None
    return None


def read_forum(kw, limit=10):
    """看某个吧的最新主题列表。"""
    relayed = _via_node('tieba_forum', {'kw': kw, 'limit': limit})
    if relayed:
        return relayed
    if not node_status()['online']:
        return offline_note()
    if not available():
        return '还没有贴吧身份，看不了。'
    url = 'https://tieba.baidu.com/f?kw=%s&ie=utf-8' % urllib.parse.quote(str(kw))
    try:
        html = _open(url)
    except Exception as exc:
        return '贴吧打不开：' + type(exc).__name__
    rows = re.findall(r'<a[^>]+href="(/p/\d+)"[^>]*class="[^"]*j_th_tit[^"]*"[^>]*>(.*?)</a>', html, re.S)
    if not rows:
        rows = re.findall(r'href="(/p/\d+)"[^>]*>(.*?)</a>', html, re.S)
    out, seen = [], set()
    for href, title in rows:
        name = _strip(title)[:60]
        if not name or href in seen:
            continue
        seen.add(href)
        out.append('%s https://tieba.baidu.com%s' % (name, href))
        if len(out) >= limit:
            break
    if not out:
        return '这个吧没读到帖子（可能被限流或吧名不对）。'
    return '「%s」吧最新：\n' % kw + '\n'.join(out)


def read_thread(url, limit=8):
    """读一个帖子的正文和前几楼。"""
    supplied = str(url or '').strip()
    match = re.fullmatch(r'(?:(?:https?://)?tieba\.baidu\.com)?/p/(\d{1,20})(?:[?#][^\s]*)?', supplied)
    if not match:
        return '这个地址不是贴吧帖子。'
    url = 'https://tieba.baidu.com/p/' + match.group(1)
    relayed = _via_node('tieba_thread', {'url': url, 'limit': limit})
    if relayed:
        return relayed
    if not node_status()['online']:
        return offline_note()
    if not available():
        return '还没有贴吧身份，看不了。'
    try:
        html = _open(url)
    except Exception as exc:
        return '帖子打不开：' + type(exc).__name__
    title = re.search(r'<title>(.*?)</title>', html, re.S)
    body = re.findall(r'<div[^>]+class="d_post_content[^"]*"[^>]*id="post_content_(\d+)"[^>]*>(.*?)</div>', html, re.S)
    out = []
    if title:
        out.append('标题：' + _strip(title.group(1))[:80])
    for pid, content in body[:limit]:
        text = _strip(content)
        if text:
            out.append('· ' + text[:220])
    return '\n'.join(out) if out else '这个帖子没解析出内容。'


def _tbs():
    try:
        data = json.loads(_open('https://tieba.baidu.com/dc/common/tbs'))
        return data.get('tbs') or ''
    except Exception:
        return ''


def _fid(kw):
    try:
        html = _open('https://tieba.baidu.com/f?kw=%s' % urllib.parse.quote(str(kw)))
        match = re.search(r'"forum_id":(\d+)', html) or re.search(r'fid=(\d+)', html)
        return match.group(1) if match else ''
    except Exception:
        return ''


def reply(kw, tid, content):
    """回帖。tid 是帖子数字 id。"""
    if not available():
        return '还没有贴吧身份，回不了贴。'
    tbs = _tbs()
    if not tbs:
        return '拿不到发帖令牌（tbs），可能 Cookie 过期了。'
    fid = _fid(kw)
    data = urllib.parse.urlencode({
        'ie': 'utf-8', 'kw': str(kw), 'fid': fid, 'tid': str(tid),
        'content': str(content)[:1500], 'tbs': tbs, 'files': '[]',
        'mouse_pwd': '', 'mouse_pwd_t': '', 'mouse_pwd_isclick': '0',
    }).encode()
    try:
        html = _open('https://tieba.baidu.com/f/commit/post/add', data=data,
                     headers={'Content-Type': 'application/x-www-form-urlencoded'})
        result = json.loads(html)
        if int(result.get('no') or 0) == 0:
            return '回好了。'
        return '没回成：' + str(result.get('error') or result)[:120]
    except Exception as exc:
        return '回帖失败：' + type(exc).__name__


def post(kw, title, content):
    """发主题帖。"""
    if not available():
        return '还没有贴吧身份，发不了。'
    tbs = _tbs()
    if not tbs:
        return '拿不到发帖令牌（tbs），可能 Cookie 过期了。'
    fid = _fid(kw)
    data = urllib.parse.urlencode({
        'ie': 'utf-8', 'kw': str(kw), 'fid': fid, 'tid': '0',
        'title': str(title)[:60], 'content': str(content)[:3000],
        'tbs': tbs, 'is_new': '1', 'files': '[]',
    }).encode()
    try:
        html = _open('https://tieba.baidu.com/f/commit/post/add', data=data,
                     headers={'Content-Type': 'application/x-www-form-urlencoded'})
        result = json.loads(html)
        if int(result.get('no') or 0) == 0:
            return '发出去了。'
        return '没发成：' + str(result.get('error') or result)[:120]
    except Exception as exc:
        return '发帖失败：' + type(exc).__name__
