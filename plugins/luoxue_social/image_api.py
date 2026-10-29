"""Official DashScope image protocols, bounded polling; credentials remain private."""
import asyncio
import json
import re
from urllib.parse import urlparse

async def generate(api,prompt):
    from .features import fetch
    base=api['base_url'].rstrip('/')
    host=urlparse(base).hostname or ''
    if not (host=='dashscope.aliyuncs.com' or host.endswith('.maas.aliyuncs.com')):
        raise ValueError('DashScope endpoint must be official mainland HTTPS host')
    headers={'Authorization':'Bearer '+api['api_key']}
    model=api['model'];proxy=api.get('proxy')
    if model=='wan2.6-t2i':
        payload={'model':model,'input':{'messages':[{'role':'user','content':[{'text':prompt[:2000]}]}]},
                 'parameters':{'size':api.get('size','1280*1280'),'n':1}}
        data=json.loads(await fetch(base+'/api/v1/services/aigc/multimodal-generation/generation',
            headers=headers,proxy=proxy,json_body=payload,limit=2_000_000))
        for choice in data.get('output',{}).get('choices',[]):
            for item in choice.get('message',{}).get('content',[]):
                if item.get('image'):return await fetch(item['image'],limit=15_000_000)
        raise RuntimeError('DashScope returned no image')
    if model not in ('wanx2.0-t2i-turbo','wan2.2-t2i-flash'):raise ValueError('Unsupported image model')
    size=api.get('size','1024*1024')
    if model=='wanx2.0-t2i-turbo' and size not in ('768*768','576*1024','1024*576','1024*1024','720*1280','1280*720','864*1152','1152*864'):
        raise ValueError('Wan 2.0 requires a supported discrete size, e.g. 1024*1024')
    payload={'model':model,'input':{'prompt':prompt[:800]},'parameters':{'size':size,'n':1}}
    data=json.loads(await fetch(base+'/api/v1/services/aigc/text2image/image-synthesis',
        headers={**headers,'X-DashScope-Async':'enable'},proxy=proxy,json_body=payload,limit=500000))
    task=data.get('output',{}).get('task_id','')
    if not re.fullmatch(r'[A-Za-z0-9-]{8,100}',task):raise RuntimeError('No valid image task ID')
    async def poll():
        for _ in range(24):
            await asyncio.sleep(3)
            result=json.loads(await fetch(base+'/api/v1/tasks/'+task,headers=headers,proxy=proxy,limit=500000))
            out=result.get('output',{})
            if out.get('task_status')=='SUCCEEDED':
                return await fetch(out['results'][0]['url'],limit=15_000_000)
            if out.get('task_status') in ('FAILED','CANCELED'):
                code=str(out.get('code','unknown'))
                raise RuntimeError('Image task failed: '+(code if re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',code) else 'unknown'))
        raise TimeoutError('Image task still pending; not resubmitted')
    return await asyncio.wait_for(poll(),150)
