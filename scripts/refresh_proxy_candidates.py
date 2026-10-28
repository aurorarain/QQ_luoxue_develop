"""Private server maintenance only; accepts a private exported proxies JSON file.
Never commit that input file. TCP reachability is not proof a proxy can reach Fish.
"""
import argparse
import asyncio
import datetime
import json
from pathlib import Path
import shutil
import yaml

async def reachable(node,semaphore):
    async with semaphore:
        try:
            _,writer=await asyncio.wait_for(asyncio.open_connection(node['server'],int(node['port'])),4)
            writer.close();await writer.wait_closed();return node
        except Exception:return None

async def main(args):
    source=Path(args.candidates)
    if source.stat().st_mode & 0o077:raise RuntimeError('candidate file must be mode 600')
    nodes=json.loads(source.read_text(encoding='utf-8-sig'))
    nodes=[x for x in nodes if x.get('type') in ('ss','vmess','vless','trojan','http','socks5')]
    semaphore=asyncio.Semaphore(16)
    live=[x for x in await asyncio.gather(*(reachable(n,semaphore) for n in nodes)) if x]
    print(json.dumps({'candidates':len(nodes),'tcp_reachable':len(live)}))
    if not live:raise RuntimeError('no reachable candidate; original routing preserved')
    preferred=[x for x in live if any(word in x.get('name','') for word in ['新加坡','日本'])]
    selected=(preferred or live)[:6]
    path=Path(args.config);backup=path.with_name('config.backup-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.yaml')
    shutil.copy2(path,backup);backup.chmod(0o600)
    data=yaml.safe_load(path.read_text())
    data['proxies']=selected
    data['proxy-groups']=[{'name':'FISH-AUTO','type':'fallback','proxies':[x['name'] for x in selected],
                          'url':'https://www.gstatic.com/generate_204','interval':120,'lazy':False}]
    data['rules']=['DOMAIN,api.fish.audio,FISH-AUTO','DOMAIN-SUFFIX,fish.audio,FISH-AUTO',
                   'DOMAIN-SUFFIX,githubusercontent.com,FISH-AUTO','DOMAIN-SUFFIX,wikimedia.org,FISH-AUTO','MATCH,DIRECT']
    path.write_text(yaml.safe_dump(data,allow_unicode=True,sort_keys=False));path.chmod(0o600)
    print('Routing written. Validate with mihomo -t before restarting. Subscription secrets were not displayed.')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('candidates',help='private exported proxies JSON, mode 600')
    parser.add_argument('--config',default='/opt/luoxue/mihomo/config.yaml')
    asyncio.run(main(parser.parse_args()))
