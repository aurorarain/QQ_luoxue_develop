# Verification — 2026-10-28

## Passed

- 11 boundary regression tests passed in the server AstrBot environment, including read-only capability credential filtering, fish-pack privacy, real At-component serialization and routing Bilibili chat requests into the reader.
- Social plugin v2.0.0 loads successfully; OneBot reconnects after AstrBot restart.
- Real group-member-list API returned a nonempty list (3 members during this deployment).
- Qzone login/cookie refresh and own-feed read succeeded; the original autonomous post exists.
- 12 public Twemoji seed stickers and 157 Blue Fat Fish animated GIFs installed (169 indexed images total). Upstream GIF total: 460.43 MiB. Source/license notices retained only in private runtime storage; affectionate GIFs are private-only by default.
- Public model call succeeded.
- Bilibili public popular metadata returned 5 items in an 8183-byte JSON body during the measurement; no full video was downloaded.
- A read-only plugin/capability manifest is injected into private requests and exposed by an owner-only tool; group prompts receive only a capability summary. It does not expose code contents, keys or arbitrary paths.
- CPU information-card image and 12-second MP4 draft were really rendered; not published to Douyin.
- Owner-only memory-tool guards installed; OS execution/network permissions disabled for both member/admin computer-use roles. Model request tool whitelist excludes shell/Python/arbitrary file/configuration tools. QQ core configuration-management commands disabled; custom status remains.
- Source repository pushed successfully. No private application IDs, keys, runtime state, chat or QQ cache included.

## Pending real-event / external prerequisites

- New-member welcome, actual At rendering, collecting an owner sticker, /status and nested Qzone replies need normal live QQ events to verify client presentation. Their code paths and boundary tests do not replace that.
- Fish initially failed because all 6 saved proxy endpoints were unreachable. After privately refreshing the current subscription, 30/61 candidate endpoints were reachable. Server routing was updated, configuration validated and the proxy restarted independently of the local computer. A real emotional TTS request then returned valid WAV audio (213036 bytes). Naturalness still needs listening; this does not guarantee future proxy availability.
- Image-generation adapter has no configured image-provider key/model. DeepSeek chat credentials cannot provide this capability.
- Overseas source connectivity was retested after the proxy fix: GitHub raw retrieval succeeded and Wikimedia API returned 200 with an identified User-Agent. Actual illustration selection/upload remains conditional on a relevant public-domain image passing review.
- Qzone likes can be accepted by the API yet not visibly applied; visible likes have not been verified.
- Authenticated Douyin/Bilibili recommendation browsing, original webpage screenshots and Douyin publishing are not configured. No Douyin OAuth authorization/video.create credentials were supplied.
- Autonomous public content reading and video-draft rendering are not evidence of self-awareness, watching a full video, or publishing a video.

The deployment record intentionally omits private IDs and endpoint credentials.
# 2026-10-28 群聊空工具初始化修复

- 群聊核心兜底也执行最终消息装饰，将模型内部的`[at:QQ号]`变成真实At组件；不自动添加@。提示明确普通回复默认不@，只在被要求或确有点名需要时使用。17项测试通过，含群聊兜底转换测试。

- AstrBot 4.29.3 的 runner.reset 在 skills_like 模式且无工具时提前返回，未初始化消息和 stats。使用 `scripts/fix_runner_empty_tools.py` 在容器内应用精确、幂等补丁；修改前备份到持久化 social_backups。
- 真实运行时无工具的 skills_like/full 两模式均验证 stats 和系统消息完成初始化；16项边界/补丁测试通过。
- 群聊兜底模型请求强制公共人设和公开群记录、清空默认历史，纯@有空文本兜底，不带私人女友系统提示。
- 普通容器重启保留补丁；重新创建容器或升级镜像后需重新运行该补丁脚本（不匹配版本会拒绝修改）。真实群聊仍需用户发送消息确认客户端收发。

# 2026-10-30 P0 图文识图与绘图策划

- 代码缺口已修：`public_chat` 原先调用 `generate()` 时不带 `image_urls`，群消息里的 Image 组件整体被丢弃；现在按事件取附件（最多2张、长边1280、JPEG）后随请求送入主模型，并在系统提示里声明“本轮附带N张公开群图片”。
- 隐私边界：取图函数只遍历 `event.get_messages()`，不读 state、缓存或历史；群聊策划上下文只含公开群记录，主人私聊尾巴只在私聊用途出现，已由单元测试用 canary 断言。
- 主 provider 视觉能力已实测：对纯红64×64 PNG 提问“这张纯色图是什么颜色”，`deepseek-flash` 返回“红色”，reasoning 中写明看到了纯红；`prompt_tokens` 34（纯文字对照）对 226（含图），证明图像 token 真的进入请求。DashScope 同账户 `qwen3-vl-plus` 也可用作备选（`qwen-vl-max/plus` 该账户不存在）。
- 绘图链路改为“先策划后出图”：新增 `draw_planner`，输出结构化方案与成句提示词，程序清洗号码/链接/密钥痕迹/at标记并限长，失败回退清洗后的原话；非 DashScope 分支此前误用原始 `text[:1500]`，现同样使用策划提示词。
- 模型与额度：普通绘图统一 `wan2.6-t2i` 1280*1280，`/精绘26` 仍限真实主人；群友合计每日20张，主人不限量；同一实例同时只跑一个绘图请求。
- 测试：容器内 `python -m unittest discover -s tests` 共 50 项全部通过（本地 Windows 同套 50 项通过、2 项因缺 AstrBot 运行时跳过）。新增 `test_vision_and_planning.py` 覆盖附件数量/尺寸/损坏数据、图片确实传入 provider、策划清洗与限长、群聊上下文不含私聊 canary。
- 已部署备份：`/opt/luoxue/astrbot/data/social_backups/p0-vision-20261030-210441`；重启后插件 2.3.0 正常加载，health 探测全绿（群成员4、表情171、空间读取OK、公开模型OK）。
- 仍需真实QQ事件验收：群聊发图后洛雪能否据实描述；私聊发图；以及一次真实生图（当日额度已用满，需次日或调额度）。

# 2026-10-30 语音失效修复（意图漏判）

- 现象：Alex 在群里说“用语音喊我句老大”、在私聊说“用语音撒娇撒娇”，洛雪回“语音我这边发不出去，撒娇的话也只能用字凑合一下”，没有语音。
- 定位：Fish API、Key、音色、代理全部正常。容器内按真实配置直连合成返回 **HTTP 200 / 200748 字节 RIFF WAV**；容器环境 `FISH_AUDIO_API_KEY` 与 Alex 提供的新 Key 一致。真正原因在 `wants_voice_reply()`：旧规则要求“语音类词 + 动作词（说|讲|念|读|发|来|听）”，而“喊”“撒娇”不在动作词里，两句都被判为普通聊天，于是语音分支根本没执行，模型也就照着“没有语音”作答。
- 修复：把意图判断收敛到 `luoxue_social/voice_control.py` 一份实现（否定式 → 祈使式 → 动词前/后位置 → 词组合），`luoxue_voice` 通过 `data.plugins.luoxue_social.voice_control` 复用（带兜底并记录警告）。群聊分支改为直接调用这份实现。
- 顺带修的隐患：`natural_say`/`/说话` 既 `event.send` 又 `yield chain_result` 会重复发语音，已拆成 `_write_wav` 与 `_send_voice`；`natural_say` 的提示词还写着“Alex 的 AI 女友”，与已取消的女友设定冲突，已改为“鲸鱼娘 AI 伙伴（不是女友）”；`SONGS_DIR` 由写死的 Windows 路径改为 `LUOXUE_SONGS_DIR` 环境变量（默认 Linux 插件数据目录）；`luoxue_voice` 0.1.0 → 0.2.0 并纳入仓库。
- 能力说明纠正：群聊与私聊提示词现在都明确“你确实有 Fish 语音能力，识别到语音请求时由插件合成发送，不要说自己发不出语音”，避免模型凭旧印象否认能力。
- 验证：容器内 53 项测试全过；意图矩阵 11 个正例全中、7 个负例全不误触发；部署后插件 `luoxue_voice 0.2.0` 正常加载、`speak`/`sing` 工具注册成功、health 探测全绿；容器内实调 `fish_tts('老大，我回来啦，语音测试。')` 返回 200748 字节 RIFF WAV。
- 仍需真实 QQ 客户端验收：发一条语音请求，确认客户端能听、音色与情绪自然（API 成功只证明合成成功）。

# 2026-10-30 表情包扩容与语义触发优化

- 统计（改造前）：索引171条（157蓝胖鱼GIF + 14 Twemoji），公开160/私人11；使用分布极度偏斜——161张从未用过，最多的一张只发过2次；公开分类里"喜欢"只有1张，属于必然失败的空池。
- 扩容：`scripts/seed_stickers.py` 增补8张Twemoji（CC-BY-4.0，来源逐条记录）：喜欢 1f60d/1f618/1f60a、害羞 1f633/1f92d、晚安 1f319/1f4a4、委屈 1f62d。索引171→179，公开分类体量：喜欢1→4、害羞3→5、晚安9→11、委屈11→12，**所有公开分类均≥3张**。
- 提示词瘦身：旧版把157条素材明细全部塞进每个提示词（实测10910字符），既费token又淹没语义对照；新版按分类计数+最多2个示例含义+上次发送记录，群聊提示词1580字符、私聊1529字符，约减少86%。
- 触发改造：强情绪（哈哈/哼/才不/呜/好耶/讨厌/笨蛋/哎呀/委屈等）允许1轮+25秒就发，平静语气仍需2轮+45秒；发完记录到`state['meme_last']`（按群/私聊分开），并在下一次提示词里回显"你上一次刚发过［分类］（含义），这轮别连着发同类"，解决"不知道自己发过什么"和连续重复。
- 仍不跨分类随机兜底；表情 marker 依旧从正文剥离；私人素材永不进群（有测试断言群聊素材清单里不出现仅私人分类）。
- 测试：容器内79项全过（新增`tests/test_memes.py` 7项：提示词体积、群聊不列私人分类、上次发送回显、强情绪提前触发、平静需两轮、冷却阻止连发、marker清理）。
- 部署：备份 `/opt/luoxue/astrbot/data/social_backups/stickers-20261030-215217`（index.json）与 `stickers-code-20261030-215303`（features.py）；重启后health正常、分类统计确认。
- 仍需真实QQ验收：表情实际发送频率、观感是否自然、以及连续两次同类是否被正确抑制。

# 2026-10-30 批次1：生图自我评价 + 深夜关心

- 生图自评：`deliver_drawing` 发送成功后异步调度 `review_drawing`，把成图压到长边768以 JPEG data URL 回喂视觉模型，写一句30字内的客观描述存进 `drawing_history[].review`，`drawing_context` 把 review 一并注入，并明确"有 review 才是真读过像素，没有就别编细节"。日上限15次，失败只记日志不影响出图。
- 视觉链路实测：同一提示词在同一 provider 上，`max_tokens=120` 返回空（推理 token 吃满），`max_tokens=600` 正确返回"纯浅蓝色背景，无具体主体，平铺居中构图"。记录这条是为了以后排查"识图没反应"时先看 token 预算。
- 深夜关心：23:00–01:59 窗口、距主人最后消息 2–10 小时、当天未发过、距上次主动消息≥6 小时才触发；文案由模型生成后经程序校验（≤60字，命中"责怪/内疚/等了你/怎么还不回/为什么不/失踪/不理我/一整晚/多久没"一律丢弃），通过后标记当日并计入 `last_proactive`，避免和常规主动私聊撞车。
- 测试：容器内 88 项全过（新增 `tests/test_care_and_review.py` 6 项：自评入库与上下文可见、失败不影响出图、配额与坏图、关心窗口/冷却、内疚话术被拒、温柔句返回且当日只一次）。
- 部署：备份 `care-review-20261030-220958`；重启后插件正常加载。
- 仍需真实 QQ 验收：画一张后看 `drawing_history.review` 是否有内容、她能否据此聊画面；深夜关心是否在合适的日子触发且不烦。

# 2026-10-30 批次2：轻量生活层"她的一天"

- 新增 `life.py`：按小时分六个时段（深夜/清晨/上午/午后/黄昏/夜里），每个时段从固定文案池里用 `sha256(日期+时段)` 选一条活动，**每时段每天只记一次**；跨日自动重置。
- 诚实地基：文案是脚本固定的"角色演绎"，注入时明确写"不是真实经历，不能声称真的做过这些事，也不要编造没写在这里的经历"；只有当 `discoveries` 里真的有今天读到的公开内容时，才追加"今天真的读到过一条公开内容：<标题>"——真实与演绎分开标注。
- 注入位置：`clock_context` 末尾（群聊、私聊、群兜底三条路径都经过它），随 `tick()` 前进。
- 修过一次重复：只有一个时段时会出现"夜里…；此刻夜里…"，改为"其它时段 + 此刻当前时段"，并加断言 `text.count('此刻') == 1`。
- 测试：容器内 95 项全过（新增 `tests/test_life.py` 6 项：时段映射、每时段一次、角色演绎与真实材料区分、跨日重置、同日稳定跨日变化、当前时段不重复）。
- 部署：备份 `life-20261030-221213`；重启后运行时验证 `advance()` 返回"夜里/把今天的小事在心里过了一遍"，注入文本无重复。

# 2026-10-30 批次4：RSS 阅读源 + 知识库结论

- 新增 `feeds.py`：白名单三个公开源（少数派 / Solidot / V2EX），每天最多抓一次（12 小时间隔，缓存），每个源最多取 2 条、总计 3 条，只保留标题、链接、摘要，链接必须是 https；抓取失败的源静默跳过。读过的东西写进 `state['reading']`，并挑一条并入 `discoveries`，来源标注"公开RSS，只读了标题和摘要"。
- 注入 `clock_context`（群聊/私聊/群兜底共用），文案明确"只读过标题摘要，不能声称看完全文或视频"。
- 真实抓取验证（服务器直连，非模拟）：3 条，来源混合 `['Solidot','少数派']`，例如"本周看什么 | 最近值得一看的 9 部作品""LibreOffice 项目递交的代码发现使用LLM 的明确标记"。
- 第一版曾出现"一个源把 3 条全占满"，已加 `PER_FEED=2` 并新增测试断言来源必须是混合的。
- 测试：容器内 105 项全过（新增 `tests/test_feeds.py` 6 项：https 过滤与数量上限、缓存不重复抓、源失败容错、标题摘要标注、无阅读不注入、来源混合）。
- 部署：备份 `feeds-20261030-221709`；重启后无异常。
- **知识库结论**：AstrBot 内置 `knowledge_base/kb.db` 存在但为空，且知识库检索依赖 embedding provider；当前 provider 列表只有 `deepseek`（chat）与两个 TTS，没有 embedding 模型，所以知识库暂时不可用。要么配一个 embedding（本地 bge-m3 在 4GB 无 GPU 上偏重，或云 embedding 增加成本），要么继续用 RSS + memory 插件。**本轮选择 RSS，不启用知识库。**

# 2026-10-30 静音时段 + 群消息重复记录修复

- 静音时段：23:00–07:00 不向主人发任何主动私聊（回复不受影响），群聊不受限。实现为 `rhythm.quiet_hours()` + 私有 settings 的 `quiet_start_hour/quiet_end_hour`；`tick()` 在群主动之后、私聊主动之前加一道判断；深夜关心因为在静音窗口内，默认处于休眠（把静音时段改掉即可恢复）。
- 群消息重复记录（真实 bug）：同一条群消息会被写两次——`PassiveObserver` 写 `group_observed`，唤醒处理写 `group`，而 `group_memory()` 把两个频道合并，模型就看到同一句话两遍。Alex 截图里"你连着夸两遍"就是这么来的（`events.db` 里"画的不错"确实有两行，`channel` 分别是 `group_observed` 和 `group`）。
  - 修法：`add()` 跨两个群频道做 15 秒内的同发送者同文本去重；`group_memory()` 用 `dedupe()` 把 120 秒内的重复行合并，SQL 命中的结果也一并去重。
  - 验证：写两次后 `group_observed` 只有 1 行、`group` 0 行，`group_memory()` 返回 1 条；真的隔了 10 分钟重复说同一句仍然保留两条。
- 顺带如实：`drawing_context` 增加"review 只代表你看过一次，不要说看了两遍/反复研究"。实测最近一张图的自评是"戴眼罩的动漫少女居中，背景为天台建筑，呈紫灰暖黄色调。"，说明自评链路确实跑通了，但"看了两遍"是演绎。
- 测试：容器内 112 项全过（新增 `tests/test_dedupe.py` 5 项、`test_care_and_review.py` 增加静音边界与休眠断言）。
- 部署：备份 `quiet-dedupe-20261030-223024`；运行时验证静音边界、去重条数、23:30 不再触发关心。
