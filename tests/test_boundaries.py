import asyncio
import importlib
import json
import pathlib
import sys
import tempfile
import types
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'plugins'))
try:import astrbot.api
except ImportError:
    for name in ['astrbot','astrbot.api','astrbot.api.event','astrbot.api.star','astrbot.api.message_components',
                 'astrbot.core','astrbot.core.message','astrbot.core.message.message_event_result']:
        sys.modules[name]=types.ModuleType(name)
    class Component:
        def __init__(self,text=None,**kw):self.text=text;self.__dict__.update(kw)
        @classmethod
        def fromFileSystem(cls,path):return cls(file=path)
    for name in ['Plain','At','Image','Record']:
        setattr(sys.modules['astrbot.api.message_components'],name,type(name,(Component,),{}))
    class Filters:
        CustomFilter=type('CustomFilter',(),{})
        def __getattr__(self,name):return lambda *a,**k:lambda f:f
    sys.modules['astrbot.api.event'].filter=Filters()
    sys.modules['astrbot.api.event'].AstrMessageEvent=object
    sys.modules['astrbot.api.star'].Star=type('Star',(),{})
    sys.modules['astrbot.api.star'].register=lambda *a,**k:lambda c:c
    sys.modules['astrbot.api'].logger=types.SimpleNamespace(info=lambda *a:None,warning=lambda *a:None,error=lambda *a:None)
    sys.modules['astrbot.core.message.message_event_result'].MessageChain=list

main=importlib.import_module('luoxue_social.main')
features=importlib.import_module('luoxue_social.features')
voice=importlib.import_module('luoxue_social.voice_control')
main.OWNER='10001';main.GROUP='20001';main.BOT='30001'

class Event:
    def __init__(self,sender='90001',private=False,text='你好',group='20001',wake=True,raw=None):
        self.sender=sender;self.private=private;self.text=text;self.group=group
        self.is_at_or_wake_command=wake;self.sent=[];self.stopped=False
        self.unified_msg_origin='napcat:FriendMessage:'+sender if private else 'napcat:GroupMessage:'+group
        self.message_obj=types.SimpleNamespace(raw_message=raw or {'post_type':'message'})
    def is_private_chat(self):return self.private
    def get_group_id(self):return self.group
    def get_sender_id(self):return self.sender
    def get_self_id(self):return '30001'
    def get_message_str(self):return self.text
    def get_messages(self):return []
    def stop_event(self):self.stopped=True
    async def send(self,chain):self.sent.append(chain)

class Boundaries(unittest.IsolatedAsyncioTestCase):
    async def test_wake_and_poke(self):
        self.assertFalse(main.group_wake(Event(wake=False)))
        self.assertTrue(main.group_wake(Event(wake=False,text='肥鱼你好')))
        self.assertFalse(main.group_wake(Event(group='99999')))
        self.assertTrue(main.group_wake(Event(raw={'sub_type':'poke','target_id':30001})))
        self.assertFalse(main.group_wake(Event(raw={'sub_type':'poke','target_id':99999})))

    async def test_private_tools(self):
        social=main.Social.__new__(main.Social)
        tools=types.SimpleNamespace(tools=[types.SimpleNamespace(name=x) for x in ['update_soul','astrbot_execute_shell','astrbot_execute_python','read_file']])
        req=types.SimpleNamespace(func_tool=tools)
        await social.tool_safety(Event(sender='10001',private=True),req)
        self.assertEqual([t.name for t in req.func_tool.tools],['update_soul'])
        self.assertEqual(len(tools.tools),4) # no global mutation
        req=types.SimpleNamespace(func_tool=tools)
        await social.tool_safety(Event(sender='90001',private=True),req)
        self.assertEqual(req.func_tool.tools,[])

    async def test_group_cannot_read_private_archive(self):
        import sqlite3
        social=main.Social.__new__(main.Social)
        social.state={'private':[{'text':'SECRET_CANARY'}],'group':[{'text':'PUBLIC_ONLY'}]}
        with tempfile.TemporaryDirectory() as folder:
            social.db_path=pathlib.Path(folder)/'events.db'
            with sqlite3.connect(social.db_path) as db:
                db.execute('CREATE TABLE events(id INTEGER PRIMARY KEY, channel TEXT,ts REAL,sender TEXT,text TEXT)')
                db.execute('INSERT INTO events(channel,ts,sender,text) VALUES(?,?,?,?)',('private',0,'owner','SECRET_CANARY topic'))
                db.execute('INSERT INTO events(channel,ts,sender,text) VALUES(?,?,?,?)',('group',0,'public','topic public memory'))
            text=json.dumps(social.group_memory('topic'))
            self.assertNotIn('SECRET_CANARY',text)
            self.assertIn('public memory',text)

    async def test_passive_observation_does_not_wake(self):
        observed=[]
        main.INSTANCE=types.SimpleNamespace(observe=lambda event:observed.append(event))
        self.assertFalse(main.PassiveObserver().filter(Event(wake=False),{}))
        self.assertEqual(len(observed),1)
        main.INSTANCE=None

    async def test_private_meme_scope_and_rotation(self):
        from unittest.mock import Mock
        f=features.Features.__new__(features.Features)
        f.s=types.SimpleNamespace(state={},save=lambda:None)
        f.library=pathlib.Path('/not-used');f._save_index=lambda:None
        f.index=[{'sha':'private','scope':'private','category':'开心','file':'private.png'},
                 {'sha':'public1','scope':'public','category':'开心','file':'one.png'},
                 {'sha':'public2','scope':'public','category':'开心','file':'two.png'}]
        a=f.choose_meme('开心',False,'group');b=f.choose_meme('开心',False,'group')
        self.assertNotEqual(a,b);self.assertNotIn('private',str(a)+str(b))

    async def test_nonpublic_download_rejected(self):
        for url in ['http://example.com','file:///etc/passwd','https://127.0.0.1','https://169.254.169.254']:
            with self.assertRaises(ValueError):await features.fetch(url)

    async def test_voice_markup(self):
        self.assertTrue(voice.prepare_voice('嘿嘿，开心。').startswith('[happy]'))
        self.assertNotIn('表情:',voice.prepare_voice('晚安[表情:晚安]'))
        self.assertNotIn('脸红',voice.prepare_voice('（脸红）才不是呢'))

    async def test_capabilities_never_expose_api_credentials(self):
        f=features.Features.__new__(features.Features)
        f.cfg={'image_api':{'api_key':'SECRET_API_CANARY'}}
        meta=types.SimpleNamespace(root_dir_name='uninstalled-example',name='example',version='1.0',activated=True)
        f.s=types.SimpleNamespace(context=types.SimpleNamespace(get_all_stars=lambda:[meta]))
        result=f.capabilities()
        self.assertEqual(result['plugins'][0]['files'],[])
        self.assertEqual(result['features']['image_generation'],'configured')
        self.assertNotIn('SECRET_API_CANARY',json.dumps(result))

    async def test_fish_pack_preferred_without_leaking_affection(self):
        f=features.Features.__new__(features.Features)
        f.s=types.SimpleNamespace(state={},save=lambda:None)
        f.library=pathlib.Path('/not-used');f._save_index=lambda:None
        f.index=[{'sha':'starter','scope':'public','category':'开心','file':'starter.png'},
                 {'sha':'fish','scope':'public','category':'开心','file':'fish.gif','pack':'blue-fat-fish'},
                 {'sha':'kiss','scope':'private','category':'喜欢','file':'kiss.gif','pack':'blue-fat-fish'}]
        self.assertEqual(f.choose_meme('开心',False,'group').name,'fish.gif')
        self.assertNotEqual(f.choose_meme('喜欢',False,'group').name,'kiss.gif')

if __name__=='__main__':unittest.main()
