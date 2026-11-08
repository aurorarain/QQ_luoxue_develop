"""Public presentation shared by the bot, the room snapshot and the brain view."""

AVATAR = '银蓝短发、蓝绿异色瞳、蓝青色科幻服饰与发饰的二次元少女'
ROOMS = {
    'living': '客厅', 'bedroom': '卧室', 'study': '书房',
    'gaming': '电竞房', 'garden': '后花园', 'kitchen': '厨房',
}
HOME = '家里有客厅、卧室、书房、电竞房、后花园和厨房。客厅有沙发和鱼缸，卧室有床与梳妆台，书房有书架，电竞房有双屏，后花园有花圃和小池塘。'

# Named activities override legacy pose tags, which are also used by the pixel room.
_ACTIVITIES = (
    ('study', 'read', ('看书', '读书', '阅读', '翻书')),
    ('kitchen', 'wash', ('洗碗', '洗杯')),
    ('kitchen', 'cook', ('煮', '做饭', '下厨', '炒')),
    ('kitchen', 'eat', ('吃饭', '零食', '吃东西', '吃了')),
    ('garden', 'water', ('浇花', '浇水')),
    ('garden', 'stroll', ('花园', '园艺')),
    ('living', 'pet', ('撸猫', '摸猫')),
    ('living', 'unpack', ('拆快递', '把买的东西放下')),
    ('study', 'draw', ('画画', '画稿')),
    ('study', 'write', ('写字', '日记', '学习', '啃笔头')),
    ('study', 'shelve', ('书架',)),
    ('gaming', 'game', ('电竞', '游戏', '打两把')),
    ('gaming', 'browse', ('贴吧', '看视频', '刷电脑', '表情包', '对着屏幕', '看老番')),
    ('bedroom', 'phone', ('床上刷手机', '自拍')),
    ('living', 'listen', ('听歌',)),
    ('living', 'watch', ('追剧',)),
    ('bedroom', 'stretch', ('起床', '伸懒腰', '洗完头', '晾刚洗')),
    ('bedroom', 'dress', ('换衣', '衣柜')),
    ('bedroom', 'recline', ('趴床', '躺床', '抱枕', '天花板')),
    ('living', 'window', ('看夜景', '看雨')),
    ('living', 'sit', ('沙发', '歇一会')),
)
_ACTIONS = {
    'read': ('study', 'read'), 'type': ('gaming', 'browse'), 'draw': ('study', 'draw'),
    'eat': ('kitchen', 'eat'), 'lie': ('bedroom', 'recline'), 'phone': ('living', 'phone'),
    'sit': ('living', 'sit'), 'walk': ('living', 'stroll'),
}


def location(activity, action, spot, sleep_mode, away=False):
    if away:
        return {'room': None, 'roomLabel': '外出', 'motion': 'away'}
    if sleep_mode in ('asleep', 'nap'):
        return {'room': 'bedroom', 'roomLabel': ROOMS['bedroom'], 'motion': 'sleep'}
    for room, motion, words in _ACTIVITIES:
        if any(word in activity for word in words):
            break
    else:
        room, motion = _ACTIONS.get(action, ('living', 'idle'))
        if spot == 'bed' and room == 'living':
            room = 'bedroom'
        elif spot == 'desk' and motion == 'idle':
            room = 'study'
    return {'room': room, 'roomLabel': ROOMS[room], 'motion': motion}
