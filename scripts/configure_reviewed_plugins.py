"""Run on the server after preparing plugins; backup configuration before invoking."""
import copy
import json
from pathlib import Path


def defaults(schema):
    return {k: defaults(v['items']) if v.get('type') == 'object' and 'items' in v
            else copy.deepcopy(v.get('default', [] if v.get('type') in ('list', 'template_list') else ''))
            for k,v in schema.items()}


def configure(root):
    root=Path(root);settings=json.loads((root/'config/luoxue_social_settings.json').read_text(encoding='utf-8-sig'))
    owner,group=str(settings['owner_qq']),str(settings['group_qq'])
    def config(name):
        schema=json.loads((root/'plugins'/name/'_conf_schema.json').read_text(encoding='utf-8-sig'))
        values=defaults(schema)
        path=root/'config'/(name+'_config.json')
        if path.exists():values.update(json.loads(path.read_text(encoding='utf-8-sig')))
        return path,values
    def save(path,values):
        path.write_text(json.dumps(values,ensure_ascii=False,indent=2));path.chmod(0o600)
        print('CONFIGURED',path.name)
    p,c=config('astrbot_plugin_anysearch');save(p,c)
    p,c=config('astrbot_plugin_qqprofile_ex')
    c.update(auto_signature=True,auto_status=True,auto_nickname=False,sync_name=False,sync_avatar=False,
        enable_schedule=False,signature_cooldown_minutes=360,status_cooldown_minutes=120,
        nickname_cooldown_minutes=1440,ai_behavior_guide=(
            '你可以低频调整自己的公开QQ签名和在线状态，只有实际工具成功才算完成。'
            '签名不包含私聊内容、他人信息、账号、联系方式或私人关系细节；不编造真实线下经历。'
            '保持洛雪的名字与既定人格。无需每轮调用，也不要播报后台操作。'))
    save(p,c)
    p,c=config('astrbot_plugin_parser')
    if not isinstance(c.get('parsers_template'),list):c['parsers_template']=[]
    c.update(whitelist=['napcat:FriendMessage:'+owner,'napcat:GroupMessage:'+group],
        source_max_size=20,source_max_minute=3,download_timeout=60,common_timeout=20,
        download_retry_times=1,debounce_interval=300,require_at_in_group=True,enable_reply_parse=True,
        proxy=settings.get('web_proxy') or '',clean_cron='0 */3 * * *')
    save(p,c)
    p,c=config('astrbot_plugin_qq_tools')
    for key in c['basic_tools']:c['basic_tools'][key]=False
    c['basic_tools'].update(user_info=True,search=True,refresh=True,get_member_list=True,poke=True,
        delete=True,repeat=True)
    c['browser_config'].update(browser=False,auto_install_browser_deps=False,allow_private_network=False)
    c['gemini_video_config']['view_video']=False
    c['message_detail_config'].update(message_detail=True,auto_inject_images=False,max_inject_images=1)
    c['view_avatar_config'].update(view_avatar=True,view_mode='context')
    c['reply_adapter'].update(enable=True,prompt='只有需要明确引用某条消息时才使用[REPLY:消息ID]，不要每条引用。')
    c['context_enhance'].update(show_message_id=False,enable_auto_at_conversion=False,inject_bilibili_card_context=False)
    c['context_enhance']['reply_quote']['enhance_reply_quote']=False
    c['context_enhance']['file_info']['show_file_info']=False
    c['advanced']['compatibility'].update(add_tool_prefix=True,disable_auto_uninstall=True,delay_append_msg_id=False)
    c['advanced']['message_cache'].update(cache_size=30,cache_bot_messages=False)
    c['tool_permission'].update(llm_ignore_permission_check=False,allow_group_admin=False)
    save(p,c)
    p,c=config('astrbot_plugin_relationship')
    c.update(MOOD_ENABLED=True,MOOD_FREQUENT_AFTER=12,MOOD_STREAK_AFTER=20,
        MOOD_SILENCE_CHANCE_PERCENT=0,CROSS_PLATFORM_MEMORY_ENABLED=False,
        AFFINITY_WHITELIST_USER_IDS=owner)
    save(p,c)


if __name__=='__main__':configure('/opt/luoxue/astrbot/data')
