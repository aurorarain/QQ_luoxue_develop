"""Personal-use upstream pack import. Media/copyright notices stay in private runtime data, not Git."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import quote
from luoxue_social.features import fetch

REPO='anka-afk/blue-fat-fish-meme-pack'
ROOT=Path('/AstrBot/data/plugin_data/luoxue_social/表情包')
MAP={'happy':'开心','angry':'生气','sad':'委屈','confused':'无语','surprised':'惊讶',
     'shy':'害羞','sleep':'晚安','affection':'喜欢','food':'吃饭','money':'金钱',
     'greeting':'问候','work':'工作','entertainment':'娱乐','teasing':'傲娇','reply':'回应'}

async def main():
    proxy='http://mihomo:7890'
    tree=json.loads(Path(os.environ['LUOXUE_PACK_TREE']).read_text(encoding='utf-8-sig')) if os.environ.get('LUOXUE_PACK_TREE') else json.loads(await fetch('https://api.github.com/repos/'+REPO+'/git/trees/main?recursive=1',proxy=proxy,limit=1_000_000))
    files=[x for x in tree['tree'] if x['path'].startswith('memes/') and x['path'].endswith('.gif')]
    source=ROOT/'blue-fat-fish-source';source.mkdir(parents=True,exist_ok=True)
    for name in ('README.md','LICENSE','manifest.json'):
        (source/name).write_bytes(await fetch('https://raw.githubusercontent.com/'+REPO+'/main/'+name,proxy=proxy,limit=100000))
    semaphore=asyncio.Semaphore(4)
    async def one(item):
        async with semaphore:
            path=item['path'];category=MAP.get(path.split('/')[1],'回应')
            name=Path(path).name;target=ROOT/category/('肥鱼_'+name);target.parent.mkdir(exist_ok=True)
            try:
                if target.exists() and target.stat().st_size==item['size']:body=target.read_bytes()
                else:
                    body=await fetch('https://raw.githubusercontent.com/'+REPO+'/main/'+quote(path,safe='/'),proxy=proxy,limit=16_000_000)
                    if len(body)!=item['size'] or not body.startswith((b'GIF87a',b'GIF89a')):raise ValueError('invalid upstream GIF')
                    target.write_bytes(body)
                return {'sha':hashlib.sha256(body).hexdigest(),'file':str(target.relative_to(ROOT)),
                        'category':category,'scope':'private' if category=='喜欢' else 'public','source':'https://github.com/'+REPO,
                        'pack':'blue-fat-fish','used':0}
            except Exception as exc:print('asset deferred',type(exc).__name__,flush=True);return None
    results=await asyncio.gather(*(one(item) for item in files))
    path=ROOT/'index.json';existing=json.loads(path.read_text()) if path.exists() else []
    hashes={x['sha'] for x in existing}
    for row in results:
        if row and row['sha'] not in hashes:existing.append(row);hashes.add(row['sha'])
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(existing,ensure_ascii=False,indent=2));tmp.replace(path)
    (ROOT/'README.md').write_text('# 洛雪表情包索引\n\n肥鱼包来源：https://github.com/'+REPO+
        '\n原作者/具体素材许可待上游补充，不代表可商用；只安装在本机运行目录，不随开源代码发布。\n\n'+
        '\n'.join('- '+x['file']+' | '+x['category']+' | '+x['scope'] for x in existing))
    print(json.dumps({'upstream_count':len(files),'installed':sum(x.get('pack')=='blue-fat-fish' for x in existing),
                      'library_total':len(existing),'download_total_mib':round(sum(x['size'] for x in files)/1048576,2)}),flush=True)

asyncio.run(main())
