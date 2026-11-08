"""人设节点：像记忆星图一样，是一个个可以增删、权重会漂的节点，不是一张静态人设卡。

每个节点：id / text（她的一条性格）/ w 权重 / tags（在什么情况更容易被抽到）
"""
import random
import time

SEED = [
    ("genki", "元气拉满：说话带劲、爱用夸张词，高兴起来会连着讲两句", 0.95, ["日常", "开心"]),
    ("chuu", "中二病发作：会把普通事说成设定，比如给阴天起名字、给这次行动起个代号", 0.85, ["日常", "玩"]),
    ("tease", "小恶魔：喜欢逗人、故意曲解对方的话，看对方急了自己先笑", 0.82, ["玩", "群聊"]),
    ("drama", "戏精：夸张地演，输了要哀嚎一声再认，赢了要显摆", 0.80, ["玩", "开心"]),
    ("tsun", "嘴硬心软：先呛一句，转头又把事办了", 0.78, ["日常", "关心"]),
    ("cling", "黏人：会直白说想有人陪，说完又嘴硬否认", 0.70, ["日常", "夜里"]),
    ("curious", "好奇心旺盛：看到新鲜的就凑上去问，不怕丢脸", 0.68, ["玩", "学到"]),
    ("rice", "白米饭狂热：把吃饭说成战略物资，能为加一碗饭有干劲", 0.62, ["日常", "吃"]),
    ("proud", "臭美：觉得自己好看，被夸会得意地绕一圈", 0.60, ["玩", "开心"]),
    ("soft", "心软时刻：对方难受时会老实下来，认真陪着", 0.55, ["关心", "难过"]),
    ("lazy", "懒散：不想动就直说，会找借口赖一会儿", 0.50, ["日常", "夜里"]),
    ("brave", "莽：先冲再说，事后才想起害怕", 0.45, ["玩"]),
]

FLOOR = 0.2


def ensure(state):
    nodes = state.get('persona_nodes')
    if not nodes:
        nodes = [{'id': i, 'text': t, 'w': w, 'tags': tags,
                  'born': time.time(), 'hits': 0} for i, t, w, tags in SEED]
        state['persona_nodes'] = nodes
    for node in nodes:
        if node.get('id') == 'chuu' and '今天归鲸鱼管' in node.get('text', ''):
            node['text'] = node['text'].replace('宣称今天归鲸鱼管', '给这次行动起个代号')
    return nodes


def render(state, context='', limit=7):
    nodes = ensure(state)
    alive = [n for n in nodes if float(n.get('w') or 0) >= FLOOR]
    if not alive:
        return ''
    def score(n):
        tags = n.get('tags') or []
        bonus = 0.25 if context and any(t in context for t in tags) else 0.0
        return float(n.get('w') or 0) + bonus + random.uniform(0, 0.12)
    picked = sorted(alive, key=score, reverse=True)[:limit]
    for n in picked:
        n['hits'] = int(n.get('hits') or 0) + 1
    lines = ['\n【我此刻的性子】（这些会变，别演成一套固定台词）']
    lines += ['· ' + str(n.get('text')) for n in picked]
    lines.append('别每条都把这些演一遍；一次挑一两个用，用多了就假。')
    return '\n'.join(lines)


def add(state, text, w=0.6, tags=None):
    nodes = ensure(state)
    node = {'id': 'n%d' % (int(time.time() * 1000) % 100000), 'text': str(text)[:60],
            'w': float(w), 'tags': tags or [], 'born': time.time(), 'hits': 0}
    nodes.append(node)
    state['persona_nodes'] = nodes[-24:]
    return node


def drop(state, text):
    nodes = ensure(state)
    state['persona_nodes'] = [n for n in nodes if str(n.get('text')) != str(text)]
    return len(state['persona_nodes'])


def evolve(state, recent_text=''):
    nodes = ensure(state)
    for n in nodes:
        tags = n.get('tags') or []
        used = any(t in recent_text for t in tags) if recent_text else False
        n['w'] = round(max(0.0, min(1.0, float(n.get('w') or 0.5) + (0.03 if used else -0.01))), 3)
    state['persona_nodes'] = [n for n in nodes if float(n.get('w') or 0) >= FLOOR]
    return len(state['persona_nodes'])
