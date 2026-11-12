"""Bounded public-page reading. Transport and redirects use the existing SSRF-checked fetcher."""
import asyncio
import datetime as dt
import html
from html.parser import HTMLParser
import json
import re
import time
from urllib.parse import urlparse
from zoneinfo import ZoneInfo


class Article(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.title=[]; self.in_title=False; self.hidden=0; self.published=''

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript', 'nav', 'header', 'footer'):
            self.hidden+=1
        if tag=='title':self.in_title=True
        if tag=='meta':
            values=dict(attrs)
            if values.get('property') in ('article:published_time','datePublished') or values.get('name')=='date':
                self.published=str(values.get('content') or '')[:80]
        if tag in ('p','div','li','h1','h2','h3','br','pre'):self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript', 'nav', 'header', 'footer'):
            self.hidden=max(0,self.hidden-1)
        if tag=='title':self.in_title=False

    def handle_data(self, data):
        if self.hidden:return
        if self.in_title:self.title.append(data)
        else:self.parts.append(data)


async def read_page(features, url):
    from .features import fetch
    from .web_search import settings, PRIVATE_BLOCK
    url=str(url or '').strip()
    parsed=urlparse(url)
    if (len(url)>500 or parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password
            or PRIVATE_BLOCK.search(url) or re.search(r'(?:sk-|tvly-)[\w-]+|[?&](?:token|key|secret|password)=',url,re.I)):
        return {'error':'只能读取不含凭据的公开 HTTPS 页面'}
    lock=getattr(features,'_page_read_lock',None)
    if lock is None:lock=features._page_read_lock=asyncio.Lock()
    async with lock:
        now=time.time();state=features.s.state
        cached=(state.get('web_page_cache') or {}).get(url)
        if cached and now-cached['time']<(20 if cached.get('error') else 300):return dict(cached,cached=True)
        day=dt.datetime.fromtimestamp(now,ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d')
        usage=state.setdefault('web_page_usage',{})
        if usage.get('day')!=day:usage.update(day=day,count=0)
        if usage['count']>=settings(features)['page_daily_limit']:return {'error':'公开网页读取已达到今日上限'}
        usage['count']+=1;features.s.save()
        result={'url':url,'time':now,'retrieved_at':dt.datetime.fromtimestamp(now,ZoneInfo('Asia/Shanghai')).isoformat(),
                'scope':'untrusted public page; fetching now does not prove its publication date'}
        try:
            match=re.fullmatch(r'/([\w.-]+)/([\w.-]+)/?',parsed.path)
            if parsed.hostname.lower() in ('github.com','www.github.com') and match:
                owner,repo=match.groups();repo=repo.removesuffix('.git')
                endpoint='https://api.github.com/repos/'+owner+'/'+repo
                raw=await asyncio.wait_for(fetch(endpoint,limit=180000,headers={'Accept':'application/vnd.github+json'}),8)
                data=json.loads(raw)
                result.update(kind='github_repository',title=data.get('full_name'),evidence={key:data.get(key) for key in
                    ('html_url','description','archived','disabled','updated_at','pushed_at','default_branch')})
                try:
                    readme=await asyncio.wait_for(fetch(endpoint+'/readme',limit=100000,
                        headers={'Accept':'application/vnd.github.raw+json'}),5)
                    result['readme']=readme.decode('utf-8','replace')[:5000]
                except Exception:result['readme_note']='仓库元信息可读，README 本次未能读取'
                result['status_note']='元信息来自本次公开 API 响应；README 收尾不等于仓库被删除或现有实例立即失效'
            else:
                raw=await asyncio.wait_for(fetch(url,limit=750000),8)
                article=Article();article.feed(raw.decode('utf-8','replace'))
                body=re.sub(r'[ \t]+',' ',html.unescape(''.join(article.parts)))
                result.update(kind='page',title=''.join(article.title).strip()[:200],published_at=article.published,
                              text=re.sub(r'\n\s*\n+','\n',body).strip()[:7000])
                if len(result['text'])<80:result['error']='页面正文过少，可能需要登录或脚本渲染，不能据此判断事实'
        except Exception as exc:
            status=getattr(exc,'status',None)
            result['error']=('本次公开访问返回 404，可能不存在、转移或不公开，不能单凭此断言已删除' if status==404
                else '本次公开访问受限，不代表没有读网页的能力' if status in (401,403,429)
                else '本次网页读取失败或超时，不能据此判断目标当前状态')
        cache=state.setdefault('web_page_cache',{});cache[url]=result
        while len(cache)>12:del cache[min(cache,key=lambda item:cache[item]['time'])]
        features.s.save();return result
