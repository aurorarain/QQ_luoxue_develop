"""Bounded simulated appraisal, episodic recall, and outcome learning."""
import re

DAY = 86400
LIMIT = 96
HALF_LIVES = {'valence': 5400, 'arousal': 900, 'prediction': 1200, 'stress': 2400}
ACTIVITY = {'read': '阅读', 'browse': '浏览', 'rest': '休息', 'stretch': '舒展', 'water': '照顾植物'}
ROUTINES = {
    'stretch': {'label': '舒展一下身体', 'done': '完成了一小段伸展', 'action': 'idle',
                'spot': 'center', 'duration': 90, 'cooldown': 2700, 'reward': .34},
    'water': {'label': '在后花园给花浇水', 'done': '给后花园的花浇了水', 'action': 'water',
              'spot': 'garden', 'duration': 120, 'cooldown': DAY, 'reward': .50},
}
ACTIVITY_RULES = {
    'water': (42, DAY), 'read': (36, 3600), 'stretch': (26, 7200), 'browse': (21, 5400),
}
TOPICS = {
    '阅读': r'阅读|看书|读书|书桌|那本书|书架|章节',
    '浏览': r'贴吧|帖子|刷帖|浏览',
    '休息': r'休息|午睡|睡觉|困了|缓一缓',
    '工作': r'工作|开会|上班|加班|测试|工位',
    '天气': r'下雨|降温|暴雨|天气|大风',
    '做饭': r'做饭|煮饭|厨房|米饭|吃饭',
    '舒展': r'伸展|伸懒腰|舒展',
    '照顾植物': r'后花园|浇水|盆栽|照顾植物',
}
SOCIAL = (
    (r'你(?:让我失望|这次说错了|刚才说错了|别这样说)|你(?:刚才)?理解错了', '收到明确的纠正', -.36, .42),
    (r'洛雪[，, ]*(?:辛苦了|做得好|真棒)|你(?:真棒|做得好|刚才说得好|这次答得好)|谢谢你', '受到肯定', .62, .45),
    (r'好消息|终于(?:成功|过了|通过|做完|搞定)|太开心了', '听到值得高兴的消息', .46, .38),
    (r'今天(?:很|太|真的)?(?:难受|沮丧|伤心)|我(?:有点|真的|很|特别)(?:难受|伤心|委屈)', '听到对方心情低落', -.18, .22),
    (r'抱抱你|给你个拥抱|想你了|来陪你一会', '收到亲近的表示', .45, .23),
)
NEED_BY_ACTION = {'read': '意', 'browse': '见', 'rest': '触', 'stretch': '触', 'water': '香'}
FEELINGS = {
    '满足': (.46, .20, .70), '释然': (.36, .10, .80), '好奇': (.18, .55, .64),
    '亲近': (.42, .25, .58), '挂念': (-.22, .35, .32), '受挫': (-.36, .52, .36),
    '平常': (0., 0., .50),
}


def clamp(value, lo=-1., hi=1.):
    return min(hi, max(lo, value))


def decay(value, elapsed, half):
    return value * 2 ** (-max(0, elapsed) / half)


def snapshot(state, now, owner=False):
    brain = state.get('cognition') or {}
    sources = brain.get('signals') or {}
    result = dict.fromkeys(HALF_LIVES, 0.)
    for source in ('life', 'owner') if owner else ('life',):
        row = sources.get(source) or {}
        for name, half in HALF_LIVES.items():
            result[name] += decay(row.get(name, 0.), now - row.get('at', now), half)
    return {name: round(clamp(value, -40, 40), 3) for name, value in result.items()}


def cues(text):
    return [name for name, pattern in TOPICS.items() if re.search(pattern, text)]


def needs_level(state, need, now, owner=False):
    raw = float((state.get('room_desires') or {}).get(need, 55.) or 0.)
    return clamp(raw + affect_overlay(state, now, owner)['needs'].get(need, 0.), 0., 100.)


def affect_overlay(state, now, owner=False):
    sources = (state.get('cognition') or {}).get('appraisals') or {}
    result = {'emotions': {}, 'needs': {}}
    for name in ('life', 'owner') if owner else ('life',):
        source = sources.get(name) or {}
        for kind, half in (('emotions', 3600), ('needs', 14400)):
            for key, value in (source.get(kind) or {}).items():
                target = result[kind]
                target[key] = target.get(key, 0.) + decay(value, now - source.get('at', now), half)
    return result


def evaluate(state, need, valence, arousal, novelty, now, agency=.55, owner=False):
    """Turn an event's direction into an appraisal relative to her current state."""
    body = clamp((65. - float(state.get('room_energy', 65))) / 50, 0, 1)
    want = 1 - needs_level(state, need, now, owner) / 100
    relevance = .65 + .55 * want
    felt = clamp(valence * relevance * (.55 + .45 * novelty)
                 * (1 - .35 * body if valence >= 0 else 1 + .40 * body))
    return {'need': need, 'felt': felt, 'arousal': clamp(arousal * novelty * (1 + .20 * body)),
            'agency': agency, 'strain': body, 'relevance': relevance}


def apply_appraisal(state, source, frame, now):
    brain = state.setdefault('cognition', {})
    all_sources = brain.setdefault('appraisals', {})
    old = all_sources.get(source) or {}
    felt, arousal, agency = (frame[key] for key in ('felt', 'arousal', 'agency'))
    pleasant, uneasy = max(0., felt), max(0., -felt)
    need = frame['need']
    emotion = {'喜': 22 * pleasant - 8 * uneasy, '怒': 18 * uneasy * agency,
               '哀': 15 * uneasy, '惧': 23 * uneasy * (1 - agency),
               '爱': 15 * pleasant if need == '触' else 0,
               '怜': 9 * uneasy if need == '触' else 0,
               '恶': 10 * uneasy * agency * arousal, '欲': 12 * arousal}
    satisfaction = {need: 28 * pleasant - 16 * uneasy}
    if frame.get('curiosity'):
        satisfaction[need] = -14 * arousal
    if need in ('见', '听', '香') and arousal > .2:
        satisfaction['意'] = -6 * arousal
    row = {'at': now}
    for kind, half, change in (('emotions', 3600, emotion), ('needs', 14400, satisfaction)):
        before = old.get(kind) or {}
        row[kind] = {key: round(clamp(decay(before.get(key, 0.), now - old.get('at', now), half)
                                     + change.get(key, 0.), -30, 30), 3)
                     for key in sorted(before.keys() | change.keys())}
    all_sources[source] = row


def apply_signal(state, source, felt, arousal, error, now):
    signals = state['cognition'].setdefault('signals', {})
    old = signals.get(source) or {}
    impacts = {'valence': 22 * felt, 'arousal': 14 * arousal,
               'prediction': 20 * error, 'stress': 18 * max(0., -felt) - 8 * max(0., felt)}
    signals[source] = {'at': now, **{
        name: round(clamp(decay(old.get(name, 0.), now - old.get('at', now), half)
                          + impacts[name], -35 if name in ('valence', 'prediction') else 0, 35), 3)
        for name, half in HALF_LIVES.items()
    }}


def remember(state, source, key, label, valence, arousal, now, tags=()):
    brain = state.setdefault('cognition', {})
    traces = brain.setdefault('episodes', [])
    previous = next((row for row in reversed(traces) if row['source'] == source and row['key'] == key), None)
    if previous and 0 <= now - previous['at'] < 75 and previous['label'] == label:
        return
    novelty = 1. if not previous else 1 - .75 * decay(1, now - previous['at'], 2700)
    values = brain.setdefault('values', {})
    stat = values.get(key) or {'mean': 0., 'count': 0}
    need = NEED_BY_ACTION.get(key.partition(':')[0], '触')
    frame = evaluate(state, need, valence, arousal, novelty, now, owner=source == 'owner')
    felt = frame['felt']
    error = felt - stat['mean']
    rate = .28 if stat['count'] >= 3 else .45
    values[key] = {'mean': round(clamp(stat['mean'] + rate * error), 3),
                   'count': min(stat['count'] + 1, 10000), 'at': now}
    if len(values) > LIMIT:
        del values[min(values, key=lambda item: values[item]['at'])]
    apply_signal(state, source, felt, frame['arousal'], error, now)
    apply_appraisal(state, source, frame, now)
    traces.append({'at': now, 'source': source, 'key': key, 'label': label[:100], 'cues': list(tags),
                   'pleasant': round(felt, 3), 'surprise': round(error, 3),
                   'salience': round(max(abs(felt), abs(error), arousal * novelty), 3),
                   'mood': snapshot(state, now, owner=True)['valence']})
    del traces[:-LIMIT]


def observe_owner(state, text, now):
    """Classify clear cues from a verified owner turn without keeping its raw text."""
    if state.get('memory_off') or not (state.get('feature_flags') or {}).get('memory', True):
        return
    for index, (pattern, label, valence, arousal) in enumerate(SOCIAL):
        for hit in re.finditer(pattern, text):
            prefix = text[max(0, hit.start() - 12):hit.start()]
            suffix = text[hit.end():hit.end() + 4]
            if re.search(r'不是|没有|并非|引用|例子|测试|假设|[“「"]', prefix) or re.match(r'吗|？|\?', suffix):
                continue
            remember(state, 'owner', f'social:{index}', label, valence, arousal, now, cues(text))
            return


def activity_key(option):
    action = option['action']
    detail = str(option.get('title') or option.get('topic') or '')[:80]
    return action + (':' + detail if detail else '')


def learn_activity(state, option, entry, now):
    action, outcome = option['action'], entry.get('outcome')
    if action not in ('read', 'browse') or outcome not in ('done', 'failed'):
        return
    if outcome == 'done':
        label = entry['result']
        valence = .54 if action == 'read' else .42
    else:
        label, valence = f'{ACTIVITY[action]}这次没有完成', -.28
    remember(state, 'life', activity_key(option), label, valence, .42, now, [ACTIVITY[action]])


def advance(state, room, now):
    brain = state.setdefault('cognition', {})
    if not brain.get('imported_activity'):
        existing = any(row['source'] == 'life' for row in brain.get('episodes', []))
        if not existing:
            for row in state.get('hb_log', [])[-28:]:
                action, at = row.get('action'), row.get('at', 0)
                if action not in ('read', 'browse') or row.get('outcome') != 'done' or not 0 <= now - at < 14 * DAY:
                    continue
                label = str(row.get('result') or '')
                topic = re.search(r'《([^》]+)》' if action == 'read' else r'「([^」]+)」', label)
                if topic:
                    learn_activity(state, {'action': action, 'title': topic[1]}, row, at)
            brain.get('episodes', []).sort(key=lambda row: row['at'])
        brain['imported_activity'] = True
    pending = brain.get('rest_due')
    if pending and (now >= pending or not state.get('autonomy_enabled', True)):
        brain.pop('rest_due')
        started = brain.pop('rest_started', None)
        done = state.get('autonomy_enabled', True) and 0 <= now - pending < 300
        audit = next((row for row in reversed(state.get('hb_log', []))
                      if row.get('at') == started and row.get('action') == 'rest'), None)
        if audit is not None:
            audit.update(outcome='done' if done else 'interrupted',
                         result='完成了一段安排好的休息' if done else '休息中断了')
        if done:
            remember(state, 'life', 'rest', '完成了一段安排好的休息', .33, .08, now, ['休息'])
    routine = brain.get('routine') or {}
    awake = room.get('sleepMode') == 'awake' and state.get('autonomy_enabled', True)
    if routine and (now >= routine['until'] or not awake):
        brain.pop('routine')
        action = routine['action']
        spec = ROUTINES[action]
        done = awake and now - routine['until'] < 300
        audit = next((row for row in reversed(state.get('hb_log', []))
                      if row.get('at') == routine['started'] and row.get('action') == action), None)
        if audit is not None:
            audit.update(outcome='done' if done else 'interrupted',
                         result=spec['done'] if done else '这轮活动中断了')
        if done:
            if action == 'stretch':
                state['room_sleepiness'] = max(0., float(state.get('room_sleepiness', 40)) - 3)
            remember(state, 'life', action, spec['done'], spec['reward'], .25, now, [ACTIVITY[action]])
    if room.get('sleepMode') not in ('asleep', 'nap'):
        brain.pop('sleep_since', None)
        return
    start = brain.setdefault('sleep_since', now)
    if now - start < 1800 or brain.get('last_consolidation', 0) >= start:
        return
    candidates = [row for row in brain.get('episodes', [])
                  if 0 <= start - row['at'] < DAY and not row.get('consolidated') and row['salience'] >= .25]
    candidates.sort(key=lambda row: row['salience'], reverse=True)
    for row in candidates[:6]:
        row['consolidated'] = True
    brain.update(last_consolidation=now, consolidated_count=min(100000, brain.get('consolidated_count', 0)
                                                               + min(6, len(candidates))))


def recall_rank(state, text, now, owner=False, past_only=False):
    query = set(cues(text))
    if owner and (state.get('memory_off') or not (state.get('feature_flags') or {}).get('memory', True)):
        return []
    candidates = []
    explicit = owner and re.search(r'(?:上回|上次|之前|以前|刚才).{0,12}(?:做过|做了|做的|在干嘛|干什么|哪件事|还记得)|(?:还记得|记不记得).{0,10}(?:上回|上次|之前|以前)', text)
    for row in (state.get('cognition') or {}).get('episodes', []):
        if not owner and row['source'] != 'life':
            continue
        age = max(0., now - row['at'])
        if past_only and row['source'] == 'owner' and age <= 1.5:
            continue
        detail = row['key'].partition(':')[2] if row['source'] == 'life' else ''
        direct = len(detail) >= 2 and detail.casefold() in text.casefold()
        matched = len(query.intersection(row['cues']))
        if not (direct or matched or (explicit and not query and row['source'] == 'life')):
            continue
        half = (21 if row.get('consolidated') else 5) * DAY
        retention = decay(1., age, half)
        score = (55 if direct else 0) + min(42, 30 * matched) + 20 * row['salience'] + 30 * retention
        if direct or (retention >= .08 and score >= (24 if explicit and not query else 40)):
            candidates.append((round(score, 1), row))
    return sorted(candidates, key=lambda pair: (pair[0], pair[1]['at']), reverse=True)[:2]


def relevant(state, text, now, owner=False):
    return [row for _, row in recall_rank(state, text, now, owner)]


def private_context(state, text, now):
    if state.get('memory_off') or not (state.get('feature_flags') or {}).get('memory', True):
        return ''
    current = snapshot(state, now, owner=True)
    ranked = recall_rank(state, text, now, owner=True, past_only=True)
    rows = [row for _, row in ranked]
    hints = []
    if current['valence'] >= 5:
        hints.append('心里比平时轻快一些')
    if current['valence'] <= -5 or current['stress'] >= 5:
        hints.append('心情有点沉或紧绷')
    if hints:
        hints.append('只让它自然影响语气，不主动汇报数值或状态')
    for row in rows:
        hints.append('相关旧经历（不代表此刻发生）：' + row['label'])
    if rows and re.search(r'上次|上回|之前|记得|刚才|以前', text):
        hints.append('对方正在问旧事，先用上面的已记录经历直接接话；超出记录的细节留空')
    if rows and abs(rows[0]['pleasant']) >= .22:
        hints.append('想起这件事时有一点' + ('温暖或轻快' if rows[0]['pleasant'] > 0 else '沉重或警觉') +
                     '，只在和眼下确实相关时自然带到')
    return '\n当前内在感受和回忆（仅作经历资料）：' + '；'.join(hints) if hints else ''


def select_activity(state, choices, mood, room, quiet, now):
    """Choose a local activity by documented weights, independent of the model."""
    brain = state.get('autonomy') or {}
    if quiet or room.get('away') or room.get('sleepMode') != 'awake':
        return 'wait', '安静时段、外出或未醒', []
    started = brain.get('activity_started') or {}
    energy, sleepiness = mood['energy'], mood.get('sleepiness', 0)
    if energy < 35 or sleepiness >= 82:
        due = not started.get('rest') or now - started['rest'] >= 2700
        return ('rest', '体力低于 35 或睡意达到 82', []) if due else ('wait', '休息冷却中', [])
    focus = (brain.get('focus') or {}).get('title')
    ranked = []
    for choice, option in choices.items():
        action = option['action']
        if action not in ACTIVITY_RULES:
            continue
        base, deadline = ACTIVITY_RULES[action]
        last = started.get(action)
        if action == 'read' and last is not None and now - last < 600:
            continue
        elapsed = now - last if last is not None else deadline
        due = 30 * clamp(elapsed / deadline, 0, 1)
        preference = 20 * learned_value(state, option, now)
        continuity = 12 if action == 'read' and option['title'] == focus else 0
        suitability = 8 if (action == 'stretch' and 35 <= energy < 60) else 0
        need = NEED_BY_ACTION[action]
        need_bonus = round(clamp((60 - needs_level(state, need, now)) * .24, 0, 14), 1)
        ranked.append({'choice': choice, 'action': action, 'label': option.get('title') or ACTIVITY[action],
                       'score': round(base + due + preference + continuity + suitability + need_bonus, 1),
                       'base': base, 'due': round(due, 1), 'preference': round(preference, 1),
                       'continuity': continuity, 'suitability': suitability, 'needBonus': need_bonus,
                       'required': action in ROUTINES and elapsed >= deadline})
    ranked.sort(key=lambda row: (not row['required'], -row['score'], row['action'], row['label']))
    if ranked and ranked[0]['required']:
        return ranked[0]['choice'], '例行事项已到期，优先安排', ranked[:8]
    if ranked and ranked[0]['score'] >= 30:
        return ranked[0]['choice'], '按活动权重与到期程度排序', ranked[:8]
    return 'wait', '目前没有活动达到 30 分', ranked[:8]


def decision_evidence(state, choices, now):
    values = (state.get('cognition') or {}).get('values') or {}
    evidence = {}
    for choice, option in choices.items():
        if option['action'] not in ACTIVITY:
            continue
        value = values.get(activity_key(option))
        hint = ' '.join((ACTIVITY[option['action']], option.get('title') or option.get('topic') or ''))
        recall = relevant(state, hint, now)
        if value or recall:
            evidence[choice] = {
                '以往结果感受': round(decay(value['mean'], now - value['at'], 14 * DAY), 2) if value else None,
                '次数': value['count'] if value else 0,
                '有关经历': [row['label'] for row in recall],
            }
    return evidence


def reflection_candidate(state, owner_id, now):
    brain = state.setdefault('cognition', {})
    if now < brain.get('next_reflection', 0):
        return None
    allow_owner = bool(owner_id and not state.get('memory_off')
                       and (state.get('feature_flags') or {}).get('memory', True))
    remembered = set(brain.get('reflected', []))
    values = {name: needs_level(state, name, now) for name in ('见', '听', '香', '味', '触', '意')}
    need = min(values, key=values.get)
    if values[need] >= 52 and snapshot(state, now, owner=allow_owner)['stress'] < 5:
        return None
    candidates = []
    for row in brain.get('episodes', [])[-24:]:
        age = now - row['at']
        if not 120 <= age <= 2 * DAY or (row['source'] == 'owner' and not allow_owner):
            continue
        related = NEED_BY_ACTION.get(row['key'].partition(':')[0], '触')
        key = f"episode:{row['key']}:{row['at']}"
        if key not in remembered:
            priority = row['salience'] + .35 * (related == need) + .25 * decay(1, age, 3600)
            candidates.append((priority, {'id': key, 'source': row['source'], 'material': row['label'],
                                           'need': need, 'prior': '偏愉快' if row['pleasant'] >= 0 else '偏不舒服',
                                           'fallback': '释然' if row['pleasant'] >= 0 else '挂念'}))
    if allow_owner:
        for row in reversed((state.get('private') or [])[-10:]):
            age = now - row.get('time', 0)
            text = str(row.get('text') or '').strip()
            key = f"owner:{row.get('time')}"
            if (str(row.get('sender')) == str(owner_id) and 90 <= age <= 1800
                    and len(text) >= 12 and key not in remembered):
                candidates.append((.72, {'id': key, 'source': 'owner', 'material': text[:180], 'need': need}))
                break
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def reserve_reflection(state, candidate, now):
    brain = state['cognition']
    brain['next_reflection'] = now + 1800
    brain['reflected'] = (brain.get('reflected', []) + [candidate['id']])[-48:]


def finish_reflection(state, candidate, choice, now):
    feeling = choice.get('feeling')
    if not isinstance(feeling, str) or feeling not in FEELINGS or feeling == '平常':
        return False
    need = choice.get('need')
    if not isinstance(need, str) or need not in ('见', '听', '香', '味', '触', '意'):
        need = candidate['need']
    valence, arousal, agency = FEELINGS[feeling]
    frame = evaluate(state, need, valence * .7, arousal * .7, .8, now, agency, candidate['source'] == 'owner')
    frame['curiosity'] = feeling == '好奇'
    apply_appraisal(state, candidate['source'], frame, now)
    apply_signal(state, candidate['source'], frame['felt'], frame['arousal'], 0., now)
    text = choice.get('note')
    note = ' '.join(text.split())[:70] if isinstance(text, str) else ''
    if re.search(r'https?://|\d{5,}|[<>{}]|口令|验证码|密码|密钥', note):
        note = ''
    brain = state['cognition']
    rows = brain.setdefault('reflections', [])
    rows.append({'at': now, 'source': candidate['source'], 'need': need, 'feeling': feeling, 'note': note,
                 'mood': snapshot(state, now, owner=True)['valence']})
    del rows[:-20]
    return True


def learned_value(state, option, now):
    value = ((state.get('cognition') or {}).get('values') or {}).get(activity_key(option))
    return decay(value['mean'], now - value['at'], 14 * DAY) if value else 0.


def projection(state, now):
    brain = state.get('cognition') or {}
    activity = []
    for key, row in sorted((brain.get('values') or {}).items(), key=lambda pair: -pair[1]['at']):
        action, _, detail = key.partition(':')
        if action in ACTIVITY:
            activity.append({'action': action, 'label': detail or ACTIVITY[action],
                             'score': round(learned_value(state, {'action': action, 'title': detail}, now), 2),
                             'count': row['count']})
    allow_private = not state.get('memory_off') and (state.get('feature_flags') or {}).get('memory', True)
    rows = [row for row in brain.get('episodes', []) if allow_private or row['source'] == 'life']
    reflections = [row for row in brain.get('reflections', []) if allow_private or row['source'] == 'life']
    return {'at': now, 'signals': snapshot(state, now, owner=allow_private),
            'episodes': rows[-24:], 'activity': activity[:8],
            'reflections': reflections[-6:],
            'decision': (state.get('autonomy') or {}).get('last_rule_decision'),
            'consolidated': brain.get('consolidated_count', 0)}
