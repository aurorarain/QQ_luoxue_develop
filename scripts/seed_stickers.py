"""Download a small public starter set. Runtime assets are not committed."""
import asyncio
import hashlib
import json
import os
from pathlib import Path

from luoxue_social.features import fetch

ROOT=Path('/AstrBot/data/plugin_data/luoxue_social/表情包')
PAIRS=[('开心','1f604'),('开心','1f606'),('傲娇','1f60f'),('傲娇','1f60e'),
       ('生气','1f624'),('生气','1f620'),('委屈','1f97a'),('委屈','1f622'),
       ('惊讶','1f632'),('无语','1f644'),('晚安','1f634'),('喜欢','1f970')]

async def main():
    path=ROOT/'index.json';items=json.loads(path.read_text()) if path.exists() else []
    for category,code in PAIRS:
        url='https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/'+code+'.png'
        try:
            offline=Path(os.environ['LUOXUE_SEED_SOURCE'])/(code+'.png') if os.environ.get('LUOXUE_SEED_SOURCE') else None
            body=offline.read_bytes() if offline and offline.exists() else await fetch(url,proxy='http://mihomo:7890',limit=100000)
        except Exception:continue
        sha=hashlib.sha256(body).hexdigest()
        if any(x['sha']==sha for x in items):continue
        folder=ROOT/category;folder.mkdir(parents=True,exist_ok=True)
        target=folder/(sha+'.png');target.write_bytes(body)
        items.append({'sha':sha,'file':str(target.relative_to(ROOT)),'category':category,
                      'scope':'public','source':'Twemoji / Twitter and contributors / CC-BY-4.0 / '+url,'used':0})
    ROOT.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(items,ensure_ascii=False,indent=2))
    (ROOT/'README.md').write_text('# 洛雪表情包索引\n\n种子图：Twemoji，Twitter及贡献者，CC-BY-4.0。私人收集图禁止用于群聊。\n\n'+
        '\n'.join('- '+x['file']+' | '+x['category']+' | '+x['scope']+' | '+x.get('source','owner') for x in items))
    print('public starter stickers:',len(items))

asyncio.run(main())
