"""书架：真的书、真的页码、真的读过多少。

每本书切成页（约 700 字一页），她只知道自己读到第几页；
没读到的页她讲不出来，也不许编。
"""
import hashlib
import json
import pathlib
import re
import time

BOOK_DIR = pathlib.Path('/AstrBot/data/plugin_data/luoxue_social/books')
PAGE_CHARS = 700


def _index(social):
    return social.state.setdefault('book_shelf', {})


def _save(social):
    try:
        social.save()
    except Exception:
        pass


def add_book(social, title, text):
    """把整本书切页入库。"""
    text = str(text or '').strip()
    if len(text) < 200:
        return '这本书内容太短了，先不放进书架。'
    BOOK_DIR.mkdir(parents=True, exist_ok=True)
    pages = [text[i:i + PAGE_CHARS] for i in range(0, len(text), PAGE_CHARS)]
    key = hashlib.sha1(title.encode('utf-8')).hexdigest()[:10]
    path = BOOK_DIR / (key + '.json')
    path.write_text(json.dumps({'title': title, 'pages': pages}, ensure_ascii=False), encoding='utf-8')
    shelf = _index(social)
    row = shelf.get(title) or {'title': title, 'file': path.name, 'total': len(pages),
                               'pages_read': 0, 'reads': 0, 'last_read': 0, 'notes': []}
    row['total'] = len(pages)
    shelf[title] = row
    _save(social)
    return '《%s》放上书架了，共 %d 页。' % (title, len(pages))


def recover_shelf(social):
    """Re-index existing book files without resetting progress."""
    shelf = _index(social)
    for path in sorted(BOOK_DIR.glob('*.json')):
        if not re.fullmatch(r'[0-9a-f]{10}\.json', path.name):
            continue
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            title, pages = data['title'], data['pages']
        except (OSError, ValueError, KeyError, TypeError):
            continue
        if (not isinstance(title, str) or not title.strip() or not isinstance(pages, list)
                or not pages or any(not isinstance(page, str) for page in pages)):
            continue
        if hashlib.sha1(title.encode('utf-8')).hexdigest()[:10] + '.json' != path.name:
            continue
        shelf.setdefault(title, {'title': title, 'file': path.name, 'total': len(pages),
                                 'pages_read': 0, 'reads': 0, 'last_read': 0, 'notes': []})


def _pages(social, title):
    shelf = _index(social)
    row = shelf.get(title)
    if not row:
        return None, []
    path = BOOK_DIR / row['file']
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return row, data.get('pages') or []
    except Exception:
        return row, []


def read(social, title, pages=5):
    """读几页，记住读了什么。"""
    shelf = _index(social)
    row = shelf.get(title)
    if not row:
        return '书架上没有这本《%s》。' % title
    row_data, all_pages = _pages(social, title)
    if not all_pages:
        return '这本书记录坏了，读不了。'
    start = int(row.get('pages_read') or 0)
    end = min(len(all_pages), start + max(1, int(pages)))
    if start >= len(all_pages):
        return '《%s》已经读完了（%d 页）。' % (title, len(all_pages))
    chunk = '\n'.join(all_pages[start:end])
    row['pages_read'] = end
    row['reads'] = int(row.get('reads') or 0) + 1
    row['last_read'] = time.time()
    shelf[title] = row
    _save(social)
    try:
        social.features.remember('读《%s》第 %d–%d 页：%s' % (title, start + 1, end, chunk[:180]),
                                 '洛雪·看书', imp=0.55, cat='event', role='洛雪')
    except Exception:
        pass
    return '读了《%s》第 %d–%d 页。\n%s' % (title, start + 1, end, chunk[:900])


def recall(social, title=None, chars=600):
    """只返回她真正读过的内容。"""
    shelf = _index(social)
    rows = [shelf[title]] if title and title in shelf else list(shelf.values())
    out = []
    for row in rows[:4]:
        row_data, all_pages = _pages(social, row['title'])
        read_pages = int(row.get('pages_read') or 0)
        if read_pages <= 0:
            out.append('《%s》：还没读过。' % row['title'])
            continue
        text = '\n'.join(all_pages[:read_pages])[:chars]
        out.append('《%s》读到第 %d/%d 页：\n%s' % (row['title'], read_pages, row['total'], text))
    return '\n\n'.join(out)


def shelf_note(social):
    """给她看的书架概况：读过多少、哪些还没读。"""
    shelf = _index(social)
    if not shelf:
        return ''
    lines = ['\n【书架】只看过读到的部分，没读到的页讲不出来：']
    for row in list(shelf.values())[:6]:
        note = '（还没读）' if not row.get('pages_read') else '（读到 %d/%d 页，读过 %d 遍）' % (
            row['pages_read'], row['total'], int(row.get('reads') or 0))
        lines.append('· 《%s》%s' % (row['title'], note))
    return '\n'.join(lines)
