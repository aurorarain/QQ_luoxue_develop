# Read-only capability awareness and Blue Fat Fish stickers

The owner-only `luoxue_capabilities` tool returns actual loaded-plugin metadata and top-level filenames from `/AstrBot/data/plugins`. It never returns source contents, configuration, arbitrary paths, API keys or credentials. The same manifest is injected into private requests, with a shorter capability summary in group requests. Shell and configuration editing remain disabled.

Group mentions normalize `[at:QQ]`, plain `@QQ`, full-width mentions and CQ-at markup into a real roster-validated At component. Explicit “@我” requests also have a deterministic sender-target fallback. Unknown IDs and @all are not converted. Bilibili read requests now route to the real public reader in both allowed-group chat and owner private chat, rather than asking the language model to pretend to browse. Public results are cached for 15 minutes.

The upstream Blue Fat Fish pack is https://github.com/anka-afk/blue-fat-fish-meme-pack . Its manifest describes 157 animated GIFs across 15 categories; the raw GIF total is approximately 460.43 MiB. The install script fetches only upstream media into the private runtime sticker library and preserves the README/license. These assets are not redistributed in this source repository; upstream does not provide complete original-author/license information and does not grant commercial use.

Fish-pack images are preferred when available, matched by category and excluding the session's five most recent choices. Affection-category stickers are private-only by default. Other private collected images remain private-only as well. Replies can explicitly request an emotion category, or receive a sticker with the existing 22% background probability. This does not mean a sticker is sent on every reply.

Screenshot capability is separate from having a platform account. The current integration fetches Bilibili public titles/descriptions and produces explicitly labeled information cards. It does not have a browser, a full video player or authenticated personalized feeds. A bounded single headless browser could be added without a GPU; session login helps with protected content but cannot guarantee bypassing captcha or platform restrictions. Screenshots must remain distinct from generated cards.

Traffic budget examples (estimates, not a provider bill): public JSON metadata is usually KB-scale per request; full video at 2 Mbit/s uses about 150 MB per ten minutes, and 5 Mbit/s about 375 MB. Daily ten-minute viewing is about 4.5 GB or 11.25 GB per 30 days respectively, excluding all other traffic. Screenshot pages additionally download JS/images; actual traffic depends on page resources and whether playback is blocked. Server memory/disk availability does not prove its monthly traffic quota or remaining bill allowance.
# 2026-10-28 表情与说说调整

- 模型收到表情分类和肥鱼素材文件名含义、图片 ID 对照，使用 `[表情:分类:图片id]` 选择；文件名标签不等于视觉识别。
- 禁止随机跨分类兜底；同分类未指定 ID 时选最少使用的素材。普通回复至少隔四轮和五分钟，私人素材不进群提示。
- 明确图片/GIF发送能力；停用旧人设中的高频颜文字要求，输出清理常见装饰颜文字。
- 说说默认纯文字，35%尝试搜索公共领域/CC0图片，仍经过相关性审查；失败不阻塞文字发布。每日最多一次发布尝试。
- 文案10–120字，具体观察和笑点优先；没有新内容可以不发，禁止捏造经历或透露私聊内容。
- 服务器容器边界测试13项通过；真实QQ展示及下一次自主说说仍需自然事件验证。
- 新增自有轻量陪伴模块：私聊角色心境余温三小时衰减；22点后有当日真实私聊素材才写日记，每日最多尝试一次，仅保留30篇。`/洛雪日记`只允许主人私聊读取最近三篇，群内不可读取，不自动发群或说说。
- 调研参考：`zzby-poi/astrbot_plugin_weather`（包含主动推送，暂未安装）、`menglimi/astrbot_plugin_private_companion`（与现有主动聊天/记忆重叠，未安装）；`976230600/astrbot_plugin_daily_note`仓库当前404。没有复制这些第三方实现。
