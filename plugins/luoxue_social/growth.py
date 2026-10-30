"""Auditable growth: candidate → independent evidence → cooldown → ratified → revocable.

This layer can never rewrite persona.py. Ratified entries are short, attributed and
revocable, and only the real owner's private chat may observe, ratify, reject or revoke.
Group content may be quoted as evidence but can never be the sole source of a trait.
"""
import hashlib
import json
import re
import time

MIN_EVIDENCE = 3
EVIDENCE_GAP = 6 * 3600
COOLDOWN = 12 * 3600
MAX_CANDIDATES = 40
MAX_RATIFIED = 20
TRAIT_MAX = 60


def _normal(trait):
    return re.sub(r'\s+', '', str(trait or ''))[:TRAIT_MAX]


def _key(trait):
    return hashlib.sha256(_normal(trait).encode()).hexdigest()[:12]


def _clean_evidence(text):
    value = re.sub(r'https?://\S+', ' ', str(text or ''))
    value = re.sub(r'\d{7,}', ' ', value)
    value = re.sub(r'(?i)api[_-]?\s?key|token|密码|验证码', ' ', value)
    return re.sub(r'\s+', ' ', value).strip()[:120]


def store(social):
    return social.state.setdefault('growth', {'candidates': [], 'ratified': []})


def observe(social, trait, evidence, now=None):
    """Record one independent piece of evidence. Never changes the active persona."""
    now = now or time.time()
    trait = _normal(trait)
    evidence = _clean_evidence(evidence)
    if len(trait) < 3 or not evidence:
        return {'ok': False, 'reason': 'too_short'}
    data = store(social)
    key = _key(trait)
    if any(row['id'] == key for row in data['ratified']):
        return {'ok': False, 'reason': 'already_ratified'}
    candidate = next((row for row in data['candidates'] if row['id'] == key), None)
    if candidate is None:
        candidate = {'id': key, 'trait': trait, 'evidence': [], 'created': now,
                     'status': 'collecting', 'cooldown_until': 0}
        data['candidates'].append(candidate)
        data['candidates'] = data['candidates'][-MAX_CANDIDATES:]
    rows = candidate['evidence']
    if rows and now - rows[-1]['time'] < EVIDENCE_GAP:
        return {'ok': False, 'reason': 'too_soon', 'need': max(0, MIN_EVIDENCE - len(rows)),
                'wait_hours': round((EVIDENCE_GAP - (now - rows[-1]['time'])) / 3600, 1)}
    digest = hashlib.sha256(evidence.encode()).hexdigest()[:16]
    if any(row['hash'] == digest for row in rows):
        return {'ok': False, 'reason': 'duplicate'}
    rows.append({'time': now, 'text': evidence, 'hash': digest})
    candidate['evidence'] = rows[-6:]
    if len(candidate['evidence']) >= MIN_EVIDENCE and candidate['status'] == 'collecting':
        candidate['status'] = 'ready'
        candidate['cooldown_until'] = now + COOLDOWN
    social.save()
    return {'ok': True, 'id': key, 'trait': trait, 'evidence': len(candidate['evidence']),
            'status': candidate['status']}


def ratify(social, key, now=None):
    """Promote a ready candidate; owner-only callers enforce that upstream."""
    now = now or time.time()
    data = store(social)
    candidate = next((row for row in data['candidates'] if row['id'] == key), None)
    if candidate is None:
        return {'ok': False, 'reason': 'unknown'}
    if len(candidate['evidence']) < MIN_EVIDENCE:
        return {'ok': False, 'reason': 'insufficient_evidence', 'have': len(candidate['evidence'])}
    if now < candidate['cooldown_until']:
        return {'ok': False, 'reason': 'cooldown', 'wait_hours': round((candidate['cooldown_until'] - now) / 3600, 1)}
    data['candidates'] = [row for row in data['candidates'] if row['id'] != key]
    data['ratified'].append({'id': key, 'trait': candidate['trait'],
                             'evidence': len(candidate['evidence']), 'ratified_at': now,
                             'active': True, 'revoked_at': 0,
                             'sources': [row['text'][:60] for row in candidate['evidence'][-3:]]})
    data['ratified'] = data['ratified'][-MAX_RATIFIED:]
    social.save()
    return {'ok': True, 'id': key, 'trait': candidate['trait']}


def revoke(social, key, now=None):
    for row in store(social)['ratified']:
        if row['id'] == key and row.get('active'):
            row['active'] = False
            row['revoked_at'] = now or time.time()
            social.save()
            return {'ok': True, 'trait': row['trait']}
    return {'ok': False, 'reason': 'unknown_or_revoked'}


def reject(social, key):
    data = store(social)
    kept = [row for row in data['candidates'] if row['id'] != key]
    if len(kept) == len(data['candidates']):
        return {'ok': False, 'reason': 'unknown'}
    data['candidates'] = kept
    social.save()
    return {'ok': True}


def active_traits(social, limit=6):
    return [row['trait'] for row in store(social)['ratified'] if row.get('active')][-limit:]


def context(social):
    traits = active_traits(social)
    if not traits:
        return ''
    return ('\n你已经固化的成长（Alex 确认过，可以自然体现在语气和习惯里，不要当口号背；'
            '和当前情境冲突时以本轮为准）：' + json.dumps(traits, ensure_ascii=False))


def summary(social, now=None):
    now = now or time.time()
    data = store(social)
    ready = [{'id': row['id'], 'trait': row['trait'], 'evidence': len(row['evidence']),
              'wait_hours': max(0.0, round((row['cooldown_until'] - now) / 3600, 1))}
             for row in data['candidates'] if row['status'] == 'ready']
    collecting = [{'id': row['id'], 'trait': row['trait'], 'evidence': len(row['evidence'])}
                  for row in data['candidates'] if row['status'] == 'collecting']
    ratified = [{'id': row['id'], 'trait': row['trait'], 'active': row['active']}
                for row in data['ratified']]
    return {'ready': ready, 'collecting': collecting, 'ratified': ratified,
            'rules': {'min_evidence': MIN_EVIDENCE, 'evidence_gap_hours': EVIDENCE_GAP // 3600,
                      'cooldown_hours': COOLDOWN // 3600}}
