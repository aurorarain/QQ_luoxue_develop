#!/usr/bin/env python3
"""Tiny sidecar for the pixel room: state for the page, chat queue for the bot."""
import hmac
import json
import math
import os
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.join(os.environ.get('LUOXUE_HOME', os.getcwd()), 'astrbot/data/room')
PASSWORD_FILE = os.path.join(os.environ.get('LUOXUE_HOME', os.getcwd()), 'room_admin_password')
PLUGIN_DIR = os.path.join(os.environ.get('LUOXUE_HOME', os.getcwd()), 'astrbot/data/plugin_data/luoxue_social')


def list_files(pattern, limit=60):
    import glob
    rows = sorted(glob.glob(os.path.join(PLUGIN_DIR, pattern)), key=os.path.getmtime, reverse=True)
    return [os.path.basename(row) for row in rows[:limit]]


PUBLIC_KEYS = ('stats', 'mood', 'moodTags', 'activity', 'action', 'spot', 'away', 'awayRemain',
               'weather', 'phase', 'clock', 'date', 'weekday', 'season', 'sleepMode', 'illness',
               'books', 'props', 'daylight', 'lights', 'body', 'online', 'messagesToday', 'room', 'roomLabel', 'motion', 'appearance', 'snapshotAt')


def public_payload():
    room = read_json(STATE, {})
    bot = read_json(BOT_STATE, {})
    econ = room.get('economy') or {}
    data = {key: room.get(key) for key in PUBLIC_KEYS if key in room}
    data['economy'] = {'stores': [{'name': row.get('name'), 'items': len(row.get('items') or [])}
                                  for row in (econ.get('stores') or [])]}
    data['books'] = room.get('books') or []
    data['stickers'] = len(read_json(os.path.join(PLUGIN_DIR, '表情包', 'index.json'), {}) or {})
    data['serverTime'] = time.time()
    return data


def full_payload():
    bot = read_json(BOT_STATE, {})
    room = read_json(STATE, {})
    health = read_json(os.path.join(PLUGIN_DIR, 'health.json'), {})
    stickers = read_json(os.path.join(PLUGIN_DIR, '表情包', 'index.json'), {})
    sticker_names = list(stickers.keys())[:40] if isinstance(stickers, dict) else []
    return {
        'private': (bot.get('private') or [])[-12:],
        'group': (bot.get('group') or [])[-12:],
        'timeline': (bot.get('room_log') or [])[-40:],
        'diary': bot.get('companion_diary') or [],
        'moodJournal': bot.get('companion_mood') or [],
        'drawings': list_files('drawing-*.png', 24),
        'voices': list_files('group_voice_*.wav', 12),
        'stickers': {'count': len(stickers) if isinstance(stickers, dict) else 0, 'names': sticker_names},
        'health': health,
        'outings': bot.get('room_outing') or {},
        'stores': bot.get('room_stores') or [],
        'books': bot.get('room_books') or [],
        'postStatus': bot.get('post_status') or '',
        'memoryGraph': {'nodes': (bot.get('mem_graph') or {}).get('nodes', []),
                       'edges': (bot.get('mem_graph') or {}).get('edges', [])},
        'heartbeat': [{'time': time.strftime('%H:%M', time.localtime(row.get('at', 0))),
                       'action': row.get('action', ''), 'thought': row.get('thought', ''),
                       'text': row.get('text', '')} for row in (bot.get('hb_log') or [])][-20:],
        'reminders': [{'text': row.get('text', ''), 'due': row.get('due', 0), 'sent': row.get('sent', False)}
                      for row in (bot.get('reminders') or [])][-12:],
        'proactive': {'enabled': bot.get('proactive_enabled'), 'group': bot.get('group_proactive_enabled')},
        'room': room.get('activity') or '',
        'serverTime': time.time(),
    }


def text_of(row):
    return str(row.get('text') or '')


def log_payload(limit=500):
    """她的统一日志：想过什么、说了什么、做了什么，按时间排成一条河。"""
    bot = read_json(BOT_STATE, {})
    rows, seen = [], set()

    def add(at, kind, text, extra='', target=''):
        try:
            ts = float(at or 0)
        except (TypeError, ValueError):
            ts = 0
        text = str(text or '')
        if not ts or not text:
            return
        key = (kind, text[:60], int(ts // 60))
        if key in seen:
            return
        seen.add(key)
        rows.append({'at': ts, 'kind': kind, 'text': text[:400],
                     'extra': str(extra)[:80], 'target': str(target)[:20]})

    for row in (bot.get('hb_log') or []):
        action = str(row.get('action') or 'none')
        thought = str(row.get('thought') or '')
        text = str(row.get('text') or '')
        if thought:
            add(row.get('at'), 'think', thought, action, '自己想的')
        if row.get('outcome') == 'done' and text and action == 'message':
            target = {'message': '发给主人', 'group': '群里', 'moment': '说说'}.get(action, '')
            add(row.get('at'), 'say', text, action, target)
        if row.get('result') and row.get('outcome') not in ('idle', 'running'):
            add(row.get('at'), 'life', row['result'], action, '独处活动')
        mood = row.get('mood') or {}
        if isinstance(mood, dict):
            parts = []
            for group in ('emotions', 'desires'):
                for name, delta in (mood.get(group) or {}).items():
                    if delta:
                        parts.append('%s%+d' % (name, int(delta)))
            if parts:
                add(row.get('at'), 'state', '调整了自己：' + '、'.join(parts), 'heartbeat', '数值')
    for row in (bot.get('proactive') or []):
        add(row.get('time'), 'say', row.get('text'), 'proactive', '发给主人')
    for channel, label in (('private', '私聊'), ('group', '群聊'), ('group_observed', '群里（旁听）')):
        for row in (bot.get(channel) or []):
            who = str(row.get('sender') or '')
            if who.startswith('洛雪'):
                add(row.get('time'), 'say', text_of(row), channel, label)
            else:
                add(row.get('time'), 'hear', '%s：%s' % (who, text_of(row)), channel, label)
    for row in (bot.get('life_events') or []):
        add(row.get('at'), 'life', row.get('text'), row.get('kind') or '', '人生')
    for row in (bot.get('self_edits') or []):
        add(row.get('at'), 'state', '%s = %s' % (row.get('key'), row.get('value')), 'self_config', '改自己')
    for row in (bot.get('browse_log') or []):
        add(row.get('at'), 'browse', '[' + str(row.get('topic') or '')[:14] + '] ' +
            ('✓ ' if row.get('ok') else '✗ ') + str(row.get('text'))[:160],
            str(row.get('source') or ''), '刷贴吧')
    for row in (bot.get('learnings') or []):
        add(row.get('at'), 'learn', '[' + str(row.get('topic'))[:16] + '] ' + str(row.get('text'))[:120],
            'browse', '学到')
    for row in (bot.get('room_log') or []):
        add(row.get('ts') or row.get('time'), 'room', row.get('text'), row.get('day') or '', '日常')
    rows.sort(key=lambda r: r['at'])
    return {'count': len(rows), 'items': rows[-limit:], 'serverTime': time.time()}


# ── 本地媒体节点：她的贴吧／抖音靠主人电脑执行 ──────────────
NODE_TOKEN_FILE = os.path.join(os.environ.get('LUOXUE_HOME', os.getcwd()), 'node_token')
NODE_STATE = os.path.join(os.environ.get('LUOXUE_HOME', os.getcwd()), 'astrbot/data/plugin_data/luoxue_social/node_state.json')
TIEBA_DIR = os.path.join(os.environ.get('LUOXUE_HOME', os.getcwd()), 'tieba')
TIEBA_COOKIE = os.path.join(TIEBA_DIR, 'cookies.txt')
TIEBA_COOKIE_SHARED = os.path.join(os.environ.get('LUOXUE_HOME', os.getcwd()), 'astrbot/data/plugin_data/luoxue_social/tieba_cookies.txt')


def node_token():
    try:
        with open(NODE_TOKEN_FILE, encoding='utf-8') as handle:
            return handle.read().strip()
    except Exception:
        return ''


def _node_state():
    return read_json(NODE_STATE, {'last_seen': 0, 'name': '', 'jobs': []})


def _save_node_state(state):
    try:
        os.makedirs(os.path.dirname(NODE_STATE), exist_ok=True)
        tmp = NODE_STATE + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as handle:
            json.dump(state, handle, ensure_ascii=False)
        os.replace(tmp, NODE_STATE)
    except Exception:
        pass


def node_heartbeat(payload):
    state = _node_state()
    state['last_seen'] = time.time()
    state['name'] = str(payload.get('name') or '本地电脑')[:40]
    state['caps'] = payload.get('caps') or ['tieba', 'douyin']
    _save_node_state(state)
    return {'ok': True, 'now': time.time()}


def node_online(within=90):
    state = _node_state()
    return time.time() - float(state.get('last_seen') or 0) < within


def node_jobs():
    state = _node_state()
    pending = [j for j in (state.get('jobs') or []) if j.get('status') == 'pending']
    for job in pending:
        job['status'] = 'running'
        job['taken_at'] = time.time()
    _save_node_state(state)
    return {'ok': True, 'jobs': pending[:5], 'online': node_online()}


def node_push_job(kind, params, timeout=40):
    state = _node_state()
    if not node_online():
        return {'ok': False, 'error': 'offline'}
    job = {'id': str(int(time.time() * 1000)) + str(len(state.get('jobs') or [])),
           'kind': kind, 'params': params or {}, 'status': 'pending', 'at': time.time()}
    jobs = (state.get('jobs') or [])[-50:]
    jobs.append(job)
    state['jobs'] = jobs[-50:]
    _save_node_state(state)
    return {'ok': True, 'id': job['id']}


def node_result(payload):
    state = _node_state()
    job_id = str(payload.get('id') or '')
    for job in (state.get('jobs') or []):
        if str(job.get('id')) == job_id:
            job['status'] = 'done'
            job['result'] = str(payload.get('result') or '')[:20000]
            job['done_at'] = time.time()
            break
    _save_node_state(state)
    return {'ok': True}


def node_fetch_result(job_id, wait=0):
    deadline = time.time() + max(0, wait)
    while True:
        state = _node_state()
        for job in (state.get('jobs') or []):
            if str(job.get('id')) == str(job_id) and job.get('status') == 'done':
                return {'ok': True, 'result': job.get('result') or ''}
        if time.time() >= deadline:
            return {'ok': False, 'error': 'timeout'}
        time.sleep(0.6)


def save_tieba_cookie(raw):
    raw = str(raw or '').strip()
    if 'BDUSS=' not in raw:
        return {'ok': False, 'error': '缺少 BDUSS，请复制完整的 Cookie'}
    try:
        os.makedirs(TIEBA_DIR, exist_ok=True)
        with open(TIEBA_COOKIE, 'w', encoding='utf-8') as handle:
            handle.write(raw)
        try:
            with open(TIEBA_COOKIE_SHARED, 'w', encoding='utf-8') as shared:
                shared.write(raw)
            os.chmod(TIEBA_COOKIE_SHARED, 0o666)
        except Exception:
            pass
    except Exception as exc:
        return {'ok': False, 'error': '写入失败：%s（目录权限问题）' % type(exc).__name__}
    return {'ok': True, 'length': len(raw)}


def tieba_status():
    for path in (TIEBA_COOKIE, TIEBA_COOKIE_SHARED):
        try:
            with open(path, encoding='utf-8') as handle:
                raw = handle.read()
            if raw.strip():
                return {'ok': True, 'saved': True, 'hasBDUSS': 'BDUSS=' in raw, 'length': len(raw)}
        except Exception:
            continue
    return {'ok': False, 'saved': False}



REGIONS = ('persona', 'memory', 'emotion', 'relation', 'interest', 'skill', 'goal')
ACTIVITY_NAMES = {'read': '阅读', 'browse': '浏览贴吧', 'rest': '休息',
                  'stretch': '舒展', 'water': '照顾植物', 'message': '主动私聊', 'none': '静观'}


def brain_payload(bot=None, now=None):
    """Projection of stored state and verified heartbeat outcomes."""
    room = read_json(STATE, {}) if bot is None else {}
    if bot is None:
        bot = read_json(BOT_STATE, {})
    now = time.time() if now is None else now
    nodes, links = {}, {}

    def add(nid, region, label, strength, **meta):
        nodes[nid] = {'id': nid, 'region': region, 'label': str(label or '')[:200],
                      'w': round(max(0, min(1, float(strength))), 3), 'meta': meta}

    def link(a, b, kind, weight):
        if a in nodes and b in nodes and a != b:
            key = (kind, *sorted((a, b)))
            links[key] = {'a': a, 'b': b, 'kind': kind, 'w': weight}

    for row in bot.get('persona_nodes') or []:
        add('p_' + str(row['id']), 'persona', row.get('text'), row.get('w', 0.5),
            hits=row.get('hits', 0), tags=row.get('tags', []))

    if room.get('appearance'):
        add('p_appearance', 'persona', room['appearance'], 1, category='当前外观')
    for row in (bot.get('growth') or {}).get('ratified', []):
        if row.get('active'):
            add('p_growth_' + str(row['id']), 'persona', row.get('trait'), .8, category='已确认成长')

    graph = bot.get('mem_graph') or {}
    indexed = {}
    for idx, row in enumerate(graph.get('nodes') or []):
        imp = float(row.get('imp') or 0.3)
        last = float(row.get('last') or row.get('at') or now)
        days = max(0, (now - last) / 86400)
        stability = float(row.get('S') or 0.6 + 12 * max(0, imp) ** 1.5)
        r = 1 if imp >= 0.75 else math.exp(-days / max(0.3, stability))
        nid = 'm_' + str(row.get('id') or f'legacy-{idx}')
        add(nid, 'memory', row.get('text'), imp * r, at=row.get('at'), role=row.get('role'),
            imp=round(imp, 2), retention=round(r, 3), stability=round(stability, 2),
            hits=row.get('hits', 0), kws=row.get('kws') or [])
        indexed[idx] = nid
    for edge in graph.get('edges') or []:
        if not isinstance(edge, list) or len(edge) != 2:
            continue
        a, b = (indexed.get(idx) for idx in edge)
        # Old graph compaction left some positional edges pointing at the wrong records.
        if a and b and set(nodes[a]['meta']['kws']).intersection(nodes[b]['meta']['kws']):
            link(a, b, 'memory-keyword', 0.35)
        if len(links) >= 900:
            break

    for kind, key in (('情绪', 'room_emotions'), ('需要', 'room_desires')):
        values = room.get('emotions' if kind == '情绪' else 'desires') or bot.get(key) or {}
        for name, value in values.items():
            add('e_' + kind + name, 'emotion', name, float(value) / 100, value=value, category=kind)

    cognition = bot.get('cognition_view') or {}
    signals = cognition.get('signals') or {}
    for key, label in (('valence', '心情偏移'), ('arousal', '唤醒程度'),
                       ('prediction', '奖赏预测误差'), ('stress', '压力反应')):
        if key in signals:
            value = round(float(signals[key]), 1)
            add('c_' + key, 'emotion', label, .3 + abs(value) / 60, value=value, category='模拟信号')
    episodes = (cognition.get('episodes') or [])[-24:]
    for idx, row in enumerate(episodes):
        nid = f'episode_{row["at"]}_{idx}'
        add(nid, 'memory', row['label'], .3 + .7 * row['salience'],
            at=row['at'], category='情景记忆', cues=row['cues'], pleasant=row['pleasant'],
            surprise=row['surprise'], consolidated=bool(row.get('consolidated')), kws=row['cues'])
        link(nid, 'c_valence', 'episode-affect', .5)
        if abs(row['surprise']) >= .12:
            link(nid, 'c_prediction', 'episode-reward', .6)

    for qq, row in (bot.get('people') or {}).items():
        count = int(row.get('count') or 0)
        add('r_' + str(qq), 'relation', row.get('name') or '群成员', min(1, count / 60),
            count=count, last=row.get('last'))

    interests = sorted((bot.get('interests') or {}).items(), key=lambda item: -float(item[1]))
    for word, weight in interests[:20]:
        add('i_' + word, 'interest', word, weight, weight=weight)

    brain = bot.get('autonomy') or {}
    audit = [row for row in bot.get('hb_log', []) if row.get('outcome')]
    flags = bot.get('feature_flags') or {}
    enabled = bot.get('autonomy_enabled', True)
    for action, name in ACTIVITY_NAMES.items():
        history = [row for row in audit if row.get('action') == action]
        active = enabled
        if action == 'browse':
            active = active and flags.get('browse', True)
        if action == 'message':
            active = active and flags.get('proactive', True) and bot.get('proactive_enabled', True)
        done = sum(row['outcome'] == 'done' for row in history)
        add('s_' + action, 'skill', name, 0.75 if active else 0.15, enabled=active,
            attempts=len(history), completed=done, last=history[-1]['at'] if history else None)
    for idx, row in enumerate(episodes):
        if row.get('source') == 'life':
            link(f'episode_{row["at"]}_{idx}', 's_' + row['key'].partition(':')[0], 'episode-action', .65)
    for key, label in {'voice': '语音', 'sticker': '表情包', 'face': 'QQ 表情',
                       'memory': '长期记忆', 'group_speak': '群聊主动接话'}.items():
        active = flags.get(key, True)
        if key == 'group_speak':
            active = active and bot.get('group_proactive_enabled', True)
        add('sf_' + key, 'skill', label, 0.65 if active else 0.15, enabled=active)

    for prefix, key, name in (('r', 'reminders', '提醒'), ('p', 'promises', '承诺'),
                              ('q', 'browse_queue', '见闻')):
        pending = [row for row in bot.get(key, []) if not any(row.get(k) for k in ('done', 'sent', 'said'))]
        for idx, row in enumerate(pending[-12:]):
            add(f'g_{prefix}{row.get("id") or row.get("at") or idx}', 'goal',
                row.get('text') or row.get('title'), 0.65, category=name, due=row.get('due'))
    focus = brain.get('focus') or {}
    if focus.get('title'):
        title = focus['title']
        book = (bot.get('book_shelf') or {}).get(title) or {}
        add('g_focus', 'goal', '继续读《%s》' % title, 0.9, category='阅读计划',
            page=book.get('pages_read'), total=book.get('total'))
        link('g_focus', 's_read', 'plan-action', 0.9)

    persona = [node for node in nodes.values() if node['region'] == 'persona']
    for idx, a in enumerate(persona):
        for b in persona[idx + 1:]:
            if set(a['meta'].get('tags', [])).intersection(b['meta'].get('tags', [])):
                link(a['id'], b['id'], 'persona-tag', 0.45)
    memories = [node for node in nodes.values() if node['region'] == 'memory']
    for word, _ in interests[:20]:
        matches = [n for n in memories if word in n['meta']['kws'] or word in n['label']]
        for memory in sorted(matches, key=lambda n: -n['w'])[:12]:
            link('i_' + word, memory['id'], 'interest-memory', 0.4)

    regions = []
    for region in REGIONS:
        weights = [node['w'] for node in nodes.values() if node['region'] == region]
        regions.append({'id': region, 'count': len(weights), 'weight': round(sum(weights) / max(1, len(weights)), 3)})
    latest = [{key: row[key] for key in ('at', 'action', 'outcome', 'result', 'thought') if key in row}
              for row in reversed(audit[-10:])]
    return {'regions': regions, 'nodes': list(nodes.values()), 'links': list(links.values()),
            'stats': {'nodes': len(nodes), 'links': len(links)}, 'serverTime': now,
            'cognition': {'at': cognition.get('at'), 'signals': signals,
                          'episodes': [{key: row.get(key) for key in
                                        ('at', 'label', 'cues', 'pleasant', 'surprise', 'mood', 'consolidated')}
                                       for row in episodes],
                          'activity': cognition.get('activity') or [],
                          'emotions': cognition.get('emotions') or {},
                          'needs': cognition.get('needs') or {},
                          'reflections': cognition.get('reflections') or [],
                          'decision': cognition.get('decision'),
                          'consolidated': cognition.get('consolidated', 0)},
            'autonomy': {'enabled': enabled, 'nextAt': brain.get('next_at'),
                         'restUntil': brain.get('rest_until'), 'recent': latest}}


def password_matches(supplied):
    try:
        with open(PASSWORD_FILE, encoding='utf-8') as handle:
            expected = handle.read().strip()
    except OSError:
        return False
    return bool(expected) and hmac.compare_digest(supplied.encode('utf-8'), expected.encode('utf-8'))


STATE = os.path.join(ROOT, 'state.json')
BOT_STATE = os.path.join(os.environ.get('LUOXUE_HOME', os.getcwd()), 'astrbot/data/plugin_data/luoxue_social/state.json')
EVENTS = os.path.join(ROOT, 'events.json')
INBOX = os.path.join(ROOT, 'inbox.jsonl')


def read_json(path, default):
    try:
        with open(path, encoding='utf-8') as handle:
            return json.load(handle)
    except Exception:
        return default


def search_status():
    config = read_json(os.path.join(PLUGIN_DIR, 'search-config.json'), {})
    if not isinstance(config, dict):
        config = {}
    provider = config.get('provider', 'tavily')
    bot = read_json(BOT_STATE, {})
    usage = bot.get('web_usage_v2') or {}
    import datetime
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return {'provider': provider,
            'configured': bool(config.get(provider + '_api_key')),
            'daily_limit': config.get('daily_limit', 25),
            'monthly_limit': config.get('monthly_limit', 900),
            'today': usage.get('count', 0) if usage.get('day') == now.strftime('%Y-%m-%d') else 0,
            'month': usage.get('credits', 0) if usage.get('month') == now.strftime('%Y-%m') else 0}


def save_search_config(payload):
    import tempfile
    if not isinstance(payload, dict) or payload.get('provider') not in ('tavily', 'brave'):
        raise ValueError('请选择支持的搜索服务')
    provider = payload['provider']
    key = payload.get('api_key', '')
    if not isinstance(key, str) or len(key) > 512 or any(ch.isspace() for ch in key):
        raise ValueError('密钥格式不正确')
    daily, monthly = int(payload.get('daily_limit', 25)), int(payload.get('monthly_limit', 900))
    if not (1 <= daily <= 200 and 1 <= monthly <= 10000):
        raise ValueError('每日上限应在 1–200，每月上限应在 1–10000')
    path = os.path.join(PLUGIN_DIR, 'search-config.json')
    config = read_json(path, {})
    if not isinstance(config, dict):
        config = {}
    config.update(provider=provider, daily_limit=daily, monthly_limit=monthly)
    if key:
        config[provider + '_api_key'] = key
    descriptor, temporary = tempfile.mkstemp(prefix='.search-config-', dir=PLUGIN_DIR)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
            json.dump(config, handle, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return dict(search_status(), ok=True)


class Handler(BaseHTTPRequestHandler):
    def _send(self, payload, code=200):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        authenticated = password_matches(self.headers.get('X-Password') or '')
        if path in ('/roomapi/brain', '/roomapi/log', '/roomapi/full', '/roomapi/search/status') and not authenticated:
            self._send({'error': 'password'}, 403)
            return
        if path == '/roomapi/search/status':
            self._send(search_status())
            return
        if self.path.startswith('/roomapi/state'):
            state = read_json(STATE, {})
            fresh = read_json(BOT_STATE, {})
            # 经济设定和钱包直接取机器人内存里的最新值，避免等 20 秒的落盘
            if isinstance(fresh.get('room_income_types'), list):
                state.setdefault('economy', {})['incomes'] = fresh['room_income_types']
            if isinstance(fresh.get('room_stores'), list):
                state.setdefault('economy', {})['stores'] = fresh['room_stores']
            if isinstance(fresh.get('room_wallet'), dict):
                wallet = fresh['room_wallet']
                state['wallet'] = {
                    'balance': wallet.get('balance', 0),
                    'goal': (wallet.get('goal') or {}).get('name', ''),
                    'saved': (wallet.get('goal') or {}).get('saved', 0),
                    'target': (wallet.get('goal') or {}).get('target', 0),
                    'log': [{'time': time.strftime('%m-%d %H:%M', time.localtime(row.get('at', 0))),
                             'amount': row.get('amount', 0), 'reason': row.get('reason', '')}
                            for row in (wallet.get('log') or [])[-20:]],
                }
            if not authenticated:
                state = {key: state[key] for key in (*PUBLIC_KEYS, 'umbrella', 'wet', 'festival')
                         if key in state}
            self._send({
                'state': state,
                'events': read_json(EVENTS, []) if authenticated else [],
                'serverTime': time.time(),
            })
            return
        if self.path.startswith('/roomapi/public'):
            self._send(public_payload())
            return
        if self.path.startswith('/roomapi/node/jobs'):
            if (self.headers.get('X-Node-Token') or '') != node_token():
                self._send({'ok': False, 'error': 'token'}, 403)
                return
            self._send(node_jobs())
            return
        if self.path.startswith('/roomapi/node/result'):
            if (self.headers.get('X-Node-Token') or '') != node_token():
                self._send({'ok': False, 'error': 'token'}, 403)
                return
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            job_id = (query.get('id') or [''])[0]
            wait = float((query.get('wait') or ['0'])[0] or 0)
            self._send(node_fetch_result(job_id, wait))
            return
        if self.path.startswith('/roomapi/node/cookie'):
            if (self.headers.get('X-Node-Token') or '') != node_token():
                self._send({'ok': False, 'error': 'token'}, 403)
                return
            try:
                with open(TIEBA_COOKIE_SHARED, encoding='utf-8') as handle:
                    raw = handle.read().strip()
            except Exception:
                try:
                    with open(TIEBA_COOKIE, encoding='utf-8') as handle:
                        raw = handle.read().strip()
                except Exception:
                    raw = ''
            self._send({'ok': bool(raw), 'cookie': raw})
            return
        if self.path.startswith('/roomapi/node/status'):
            state = _node_state()
            self._send({'online': node_online(), 'last_seen': state.get('last_seen'),
                        'name': state.get('name'), 'jobs': len(state.get('jobs') or [])})
            return
        if self.path.startswith('/roomapi/tieba/status'):
            self._send(tieba_status())
            return
        if path == '/roomapi/brain':
            try:
                self._send(brain_payload())
            except Exception as exc:
                self._send({'error': type(exc).__name__, 'regions': [], 'nodes': [], 'links': []}, 500)
            return
        if path == '/roomapi/log':
            try:
                self._send(log_payload())
            except Exception as exc:
                self._send({'error': type(exc).__name__, 'items': [], 'count': 0}, 500)
            return
        if path == '/roomapi/full':
            self._send(full_payload())
            return
        if self.path.startswith('/roomapi/asset/'):
            if not authenticated:
                self._send({'error': 'password'}, 403)
                return
            try:
                name = os.path.basename(self.path.split('/roomapi/asset/', 1)[1])
                if not (name.startswith('drawing-') or name.startswith('group_voice')):
                    self._send({'error': 'denied'}, 403)
                    return
                path = os.path.join(PLUGIN_DIR, name)
                if not os.path.isfile(path):
                    self._send({'error': 'missing'}, 404)
                    return
                with open(path, 'rb') as handle:
                    data = handle.read()
                ctype = 'audio/wav' if name.endswith('.wav') else 'image/png'
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(data)
            except Exception as exc:
                self._send({'error': type(exc).__name__}, 500)
            return
        self._send({'error': 'not found'}, 404)

    def do_POST(self):
        if urllib.parse.urlsplit(self.path).path == '/roomapi/search/config':
            if not password_matches(self.headers.get('X-Password') or ''):
                self._send({'ok': False, 'error': 'password'}, 403)
                return
            try:
                length = int(self.headers.get('Content-Length') or 0)
                if not 0 < length <= 4096:
                    raise ValueError('请求大小不正确')
                payload = json.loads(self.rfile.read(length).decode('utf-8'))
                result = save_search_config(payload)
            except (ValueError, TypeError):
                self._send({'ok': False, 'error': '设置无效，请检查服务、密钥格式和用量范围'}, 400)
                return
            except OSError:
                self._send({'ok': False, 'error': '设置保存失败'}, 500)
                return
            self._send(result)
            return
        if self.path.startswith('/roomapi/node/heartbeat'):
            if (self.headers.get('X-Node-Token') or '') != node_token():
                self._send({'ok': False, 'error': 'token'}, 403)
                return
            try:
                length = int(self.headers.get('Content-Length') or 0)
                payload = json.loads(self.rfile.read(length).decode('utf-8') or '{}')
            except Exception:
                payload = {}
            self._send(node_heartbeat(payload))
            return
        if self.path.startswith('/roomapi/node/push'):
            if (self.headers.get('X-Node-Token') or '') != node_token():
                self._send({'ok': False, 'error': 'token'}, 403)
                return
            try:
                length = int(self.headers.get('Content-Length') or 0)
                payload = json.loads(self.rfile.read(length).decode('utf-8') or '{}')
            except Exception:
                payload = {}
            self._send(node_push_job(payload.get('kind') or '', payload.get('params') or {}))
            return
        if self.path.startswith('/roomapi/node/done'):
            if (self.headers.get('X-Node-Token') or '') != node_token():
                self._send({'ok': False, 'error': 'token'}, 403)
                return
            try:
                length = int(self.headers.get('Content-Length') or 0)
                payload = json.loads(self.rfile.read(length).decode('utf-8') or '{}')
            except Exception:
                payload = {}
            self._send(node_result(payload))
            return
        if self.path.startswith('/roomapi/tieba/cookie'):
            if not password_matches(self.headers.get('X-Password') or ''):
                self._send({'ok': False, 'error': '密码不对'}, 403)
                return
            try:
                length = int(self.headers.get('Content-Length') or 0)
                payload = json.loads(self.rfile.read(length).decode('utf-8') or '{}')
            except Exception:
                self._send({'ok': False, 'error': 'bad json'}, 400)
                return
            self._send(save_tieba_cookie(payload.get('cookie')))
            return
        if self.path.startswith('/roomapi/allowance'):
            if not password_matches(self.headers.get('X-Password') or ''):
                self._send({'error': 'password'}, 403)
                return
            try:
                length = int(self.headers.get('Content-Length') or 0)
                payload = json.loads(self.rfile.read(length).decode('utf-8') or '{}')
                value = float(payload.get('value') or 0)
                with open(INBOX, 'a', encoding='utf-8') as handle:
                    handle.write(json.dumps({'cmd': 'allowance', 'value': value, 'ts': time.time()},
                                            ensure_ascii=False) + '\n')
                self._send({'ok': True, 'value': value})
            except Exception as exc:
                self._send({'error': type(exc).__name__}, 500)
            return
        if self.path.startswith('/roomapi/auth'):
            try:
                length = int(self.headers.get('Content-Length') or 0)
                payload = json.loads(self.rfile.read(length).decode('utf-8') or '{}')
                self._send({'ok': password_matches(str(payload.get('password') or ''))})
            except Exception as exc:
                self._send({'error': type(exc).__name__}, 500)
            return
        if self.path.startswith('/roomapi/system'):
            try:
                length = int(self.headers.get('Content-Length') or 0)
                payload = json.loads(self.rfile.read(length).decode('utf-8') or '{}')
                if not password_matches(str(payload.pop('password', ''))):
                    self._send({'error': 'password'}, 403)
                    return
                with open(INBOX, 'a', encoding='utf-8') as handle:
                    handle.write(json.dumps({'cmd': 'system', 'action': payload.get('cmd'),
                                             'value': payload.get('value'), 'ts': time.time()},
                                            ensure_ascii=False) + '\n')
                self._send({'ok': True})
            except Exception as exc:
                self._send({'error': type(exc).__name__}, 500)
            return
        if self.path.startswith('/roomapi/economy'):
            try:
                length = int(self.headers.get('Content-Length') or 0)
                payload = json.loads(self.rfile.read(length).decode('utf-8') or '{}')
                if not password_matches(str(payload.pop('password', ''))):
                    self._send({'error': 'password'}, 403)
                    return
                with open(INBOX, 'a', encoding='utf-8') as handle:
                    handle.write(json.dumps({'cmd': 'economy', 'data': payload, 'ts': time.time()},
                                            ensure_ascii=False) + '\n')
                self._send({'ok': True})
            except Exception as exc:
                self._send({'error': type(exc).__name__}, 500)
            return
        if not self.path.startswith('/roomapi/say'):
            self._send({'error': 'not found'}, 404)
            return
        if not password_matches(self.headers.get('X-Password') or ''):
            self._send({'error': 'password'}, 403)
            return
        try:
            length = int(self.headers.get('Content-Length') or 0)
            payload = json.loads(self.rfile.read(length).decode('utf-8') or '{}')
            text = str(payload.get('text') or '').strip()[:300]
            if not text:
                self._send({'error': 'empty'}, 400)
                return
            with open(INBOX, 'a', encoding='utf-8') as handle:
                handle.write(json.dumps({'text': text, 'ts': time.time()}, ensure_ascii=False) + '\n')
            self._send({'ok': True})
        except Exception as exc:
            self._send({'error': type(exc).__name__}, 500)

    def log_message(self, *args):
        pass


if __name__ == '__main__':
    os.makedirs(ROOT, exist_ok=True)
    open(INBOX, 'a').close()
    ThreadingHTTPServer(('0.0.0.0', 8791), Handler).serve_forever()
