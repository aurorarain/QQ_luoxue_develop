# AstrBot 插件生态对照（GitHub star 前 100，2026-10-31）

> 数据来源：GitHub Search API，关键词 `astrbot_plugin` / `astrbot plugin`，按 star 降序取前 100，
> 已剔除 AstrBot 本体、桌面版与插件合集仓库。star 只是热度代理指标，不等于质量或兼容性。

## 一、与你当前部署的能力差距（按价值排序）

- **拟人化整包（生活日程/重要日期/日记/主动消息）**（601★，如 `private_companion`）：你有轻量版：作息、气氛余温、生活层、深夜关心（已休眠）。缺：纪念日、更细的日程与主动话题。
- **群聊"读空气"状态机 + 主动接话**（147–195★，如 `angel_heart / SpectreCore / group_chat_plus / Heartflow`）：你现在是规则 + 模型判断；这类插件用状态机控制"何时开口"，接话更自然但更难调。
- **向量/图谱记忆（RAG）**（87–408★，如 `livingmemory / mnemosyne / persistent_memory / angel_memory`）：你现在是 Markdown + 关键词；没有 embedding，检索靠 LIKE，长历史容易漏。
- **图生图 / 多后端绘图**（80–85★，如 `omnidraw / shoubanhua`）：你现在只有文生图（万相 2.6）；用户发参考图让你"画成这个风格"目前只能靠文字猜。
- **视频解析 + AI 总结**（59–80★，如 `biliVideo / videos_analysis / media_parser`）：你现在只能读公开标题简介，不能总结视频内容。
- **语音情绪路由 / 音色克隆**（59–87★，如 `tts_emotion_router / clonetts / feiyu_voice`）：你现在单一 Fish 音色，情绪只靠 S2 标签；克隆与唱歌未完成。
- **群聊日报 / 数据报告**（531★，如 `qq_group_daily_analysis`）：你现在只有资讯卡片，没有"今天群里聊了什么"的总结。
- **表情包管理增强**（521★，如 `meme_manager / meme_generator`）：你现在有本地库 + 冷却 + 三次重复偷用；缺 WebUI 管理、云端同步、AI 生成表情。
- **提示词注入防护**（85★，如 `antipromptinjector`）：你现在靠人设约束 + 工具白名单，没有独立防护层。

## 二、前 100 明细（按类别）

### 拟人化 / 主动群聊 / 读空气

| Star | 仓库 | 说明 | 洛雪现状 |
|---|---|---|---|
| 601 | `menglimi/astrbot_plugin_private_companion` | 面向 AstrBot 的拟人化整合插件。它会让 bot 拥有连续的拟人状态、每天的生活日程、重要日期、日记和低频主动消息。包含60+实用功能且具有完善的拓展管理页面。 | 部分：自研作息、低频主动、气氛余温；无状态机式读空气 |
| 495 | `Pancakes-Labs/astrbot_plugin_proactive_chat` | 一个能让 Bot 在私聊和群聊中发起主动消息的插件，拥有上下文感知、持久化数据、动态情绪、免打扰时段和 TTS 集成。还有独立 WebUI，可进行个性化配置。  An AstrBo | 部分：自研作息、低频主动、气氛余温；无状态机式读空气 |
| 195 | `Him666233/astrbot_plugin_group_chat_plus` | 一个为AstrBot平台提供的以AI读空气为核心的群聊增强插件，让你的Bot更懂氛围、更自然地参与群聊互动 | 部分：自研作息、低频主动、气氛余温；无状态机式读空气 |
| 147 | `kawayiYokami/astrbot_plugin_angel_heart` | 告别“人工智障”式群聊！本插件用【4状态机】教会AI观察时机、判断气氛，实现真人般社交直觉；再以【轻重双AI核】分离思考与决策，保证回复质量的同时大幅降低API成本。 | 部分：自研作息、低频主动、气氛余温；无状态机式读空气 |
| 138 | `23q3/astrbot_plugin_SpectreCore` | 使大模型更好的主动回复群聊中的消息，带来生动和沉浸的群聊对话体验 | 部分：自研作息、低频主动、气氛余温；无状态机式读空气 |
| 91 | `advent259141/Astrbot_plugin_Heartflow` | 简单的心流机制群聊主动回复插件 | 部分：自研作息、低频主动、气氛余温；无状态机式读空气 |
| 87 | `Sisyphbaous-DT-Project/astrbot_plugin_AstrNa` | AstrNa是一款AstrBot优化插件 | 部分：自研作息、低频主动、气氛余温；无状态机式读空气 |
| 70 | `advent259141/astrbot_plugin_debounce` | 利用微调模型实现消息防抖，判断用户在分段发送消息的情况下是否说完一句话，合并后调用LLM | 部分：自研作息、低频主动、气氛余温；无状态机式读空气 |

### 群聊总结 / 数据报告

| Star | 仓库 | 说明 | 洛雪现状 |
|---|---|---|---|
| 531 | `SXP-Simon/astrbot_plugin_qq_group_daily_analysis` | ✨ AstrBot 群日常分析总结插件 —— 自动总结群聊提取有趣信息并生成精美海报或网页链接，还能制作群趣味连环漫画；自带管理后台，可查看运行链路、历史报告、异常日志和数据审计； | 有：公开资讯卡片；无群日报 |

### 表情包管理 / 生成

| Star | 仓库 | 说明 | 洛雪现状 |
|---|---|---|---|
| 521 | `anka-afk/astrbot_plugin_meme_manager` | 一个功能强大的 AstrBot 表情包管理插件，支持 🤖 AI 智能发送与自动收集表情、🖥️ WebUI 管理界面、☁️ 云端同步等特性。 | 有：本地语义表情库 + 冷却 + 偷用；无 WebUI/云端同步 |
| 80 | `SodaSizzle/astrbot_plugin_meme_generator` | 表情包生成插件 | 有：本地语义表情库 + 冷却 + 偷用；无 WebUI/云端同步 |
| 37 | `QingchenWait/astrbot_plugin_smart_imagechat_hub` | LLM 驱动的一体化 AstrBot 图片对话插件。自动生成多维度图像标签，并通过多模态语义分析，实现智能斗图、主动表情、表情包分享等多种功能，支持 4 种导入图库方法。 | 有：本地语义表情库 + 冷却 + 偷用；无 WebUI/云端同步 |

### 自主学习 / 自我进化 / 代码生成

| Star | 仓库 | 说明 | 洛雪现状 |
|---|---|---|---|
| 447 | `NickCharlie/astrbot_plugin_self_learning` | AstrBot 自主学习插件 — 让 AI 聊天机器人自主学习对话风格、理解群组黑话、管理社交关系与好感度、自适应人格演化，像真人一样自然对话。 | 部分：自研可审计成长层；不做代码自我修改 |
| 74 | `DITF16/astrbot_plugin_self_iterative_core` | 赋予 AstrBot 自我进化与代码迭代的核心能力 | 部分：自研可审计成长层；不做代码自我修改 |
| 72 | `qa296/astrbot_plugin_CodeMage` | 还在手写 AstrBot 插件？描述你想要的功能，看着 AI 在几秒内把它变成可运行的代码——不需要编程经验，不需要翻阅文档，只需要一句话。CodeMage 正在改变机器人扩展的开 | 部分：自研可审计成长层；不做代码自我修改 |

### 长期记忆 / RAG

| Star | 仓库 | 说明 | 洛雪现状 |
|---|---|---|---|
| 408 | `lxfight-s-Astrbot-Plugins/astrbot_plugin_livingmemory` | 一个拥有动态生命周期的智能长期记忆插件。 | 部分：有 memory 插件（Markdown + 关键词检索），无向量检索 |
| 261 | `lxfight/astrbot_plugin_mnemosyne` | 一个AstrBot插件，实现基于RAG技术的长期记忆功能。 | 部分：有 memory 插件（Markdown + 关键词检索），无向量检索 |
| 199 | `kawayiYokami/astrbot_plugin_angel_memory` | 为AstrBot赋予真正的记忆能力：让AI不仅能记住，还能主动思考、自主进化 | 部分：有 memory 插件（Markdown + 关键词检索），无向量检索 |
| 88 | `lxfight/astrbot_plugin_knowledge_base` |  | 部分：有 memory 插件（Markdown + 关键词检索），无向量检索 |
| 87 | `zhanzhao2/astrbot-plugin-persistent-memory` | astrbot持久化记忆插件：基于 memory-lancedb-pro 二次开发，支持自动记忆捕获、召回注入、LanceDB 持久化、混合检索与重排序。 | 部分：有 memory 插件（Markdown + 关键词检索），无向量检索 |
| 85 | `Renyus/astrbot_plugin_self_evolution` | A self-evolution plugin for AstrBot that enables persona evolution, long-term memory, and  | 部分：有 memory 插件（Markdown + 关键词检索），无向量检索 |
| 77 | `menglimi/astrbot_plugin_memory_companion` | 是与陪伴插件紧密配合的定制记忆插件，能够实现更加拟人化的记忆调度和更加可理解性的记忆编排；并通过协议将记忆提供给陪伴插件实现更加逼真的拟人日程生成。 | 部分：有 memory 插件（Markdown + 关键词检索），无向量检索 |
| 58 | `2718labs/astrbot_plugin_sylanne` | 让你的Bot不再只是记住你，Sylanne致力于为你的Bot提供一个足以回答“Ta是谁、Ta如何看待你、Ta为什么这样回应、Ta如何因经历而改变”的试验性方案。 | 部分：有 memory 插件（Markdown + 关键词检索），无向量检索 |
| 38 | `leafliber/astrbot_plugin_iris_memory` | A memory plugin for astrbot | 部分：有 memory 插件（Markdown + 关键词检索），无向量检索 |
| 35 | `qa296/astrbot_plugin_memora_connect` | 一款模仿生物海马体、通过“概念节点”与“关系连接”构成记忆网络，具备记忆形成、提取、遗忘、巩固功能且采用“双峰”时间分布回顾聊天，记忆可被定期保存的插件。 | 部分：有 memory 插件（Markdown + 关键词检索），无向量检索 |

### 内容下载（需注意合规）

| Star | 仓库 | 说明 | 洛雪现状 |
|---|---|---|---|
| 299 | `GEMILUXVII/astrbot_plugin_jm_cosmos` | AstrBot 禁漫漫画下载插件 / 全新重构v2.x架构 / 支持搜索/详情/排行榜/推荐浏览 / 加密PDF/ZIP打包 / 账号登录与收藏夹 / 封面预览 / 代理支持 | 不做 |
| 68 | `vmoranv-reborn/astrbot_plugin_pixiv_reborn` | 为astrbot提供pixiv适配,提供订阅服务,小说动图适配等 | 不做 |
| 60 | `FloatSakura/astrbot_plugin_jm_downloader` | An AstrBot plugin for downloading comics from JMComic (18+) via QQ chat. Supports `.jm <ID | 不做 |
| 34 | `vmoranv/astrbot_plugin_pixiv_search` | AstrBot Plugin for Pixiv Search ✨ 一个基于 AstrBot 框架的插件，支持通过关键词或作品ID搜索 Pixiv 插画，并返回详细信息（如作者、标 | 不做 |

### 游戏数据查询

| Star | 仓库 | 说明 | 洛雪现状 |
|---|---|---|---|
| 223 | `Maoer233/astrbot_plugin_steam_status_monitor` | 监控Steam指定玩家的游戏状态变更，并实时推送至群聊。 | 无 |
| 152 | `Entropy-Increase-Team/astrbot_plugin_rocom` | 洛克王国数据查询插件，支持个人信息 精灵查询 交换大厅 图鉴 配队攻略等 | 无 |
| 66 | `Entropy-Increase-Team/astrbot_plugin_endfield` | 终末地协议终端——查询抽卡记录，角色，森空岛签到，当前理智等 | 无 |
| 56 | `KimigaiiWuyi/astrbot_plugin_gscore_adapter` | astrbot的GsCore插件适配器 | 无 |
| 50 | `NullumNomen/astrbot_plugin_fishing` | 电子钓鱼小游戏 | 无 |
| 43 | `tinkerbellqwq/astrbot_plugin_fishing` | 电子钓鱼小游戏 | 无 |
| 39 | `UmocxZzZ/astrbot_plugin_owstats777` | Astrbot 守望先锋国服战绩查询插件，封装 Overstats 本地 API， 支持玩家资料、战绩详情、段位历史、总结图片、AI 锐评、AI 开庭等功能。 | 无 |

### 其他

| Star | 仓库 | 说明 | 洛雪现状 |
|---|---|---|---|
| 194 | `LiJinHao999/astrbot_plugin_hapi_connector` | 连接hapi，随时随地vibe coding的插件！ | 无 |
| 84 | `nagatoquin33/astrbot_plugin_stealer` | 不可能没有问题，但是没有问题不大可能 | 无 |
| 56 | `diaomin66/astrbot_plugin_qzone_ultra` | QQ空间Ultra：更稳定、快速的astrbot QQ空间插件 | 无 |
| 56 | `RichardLiuda/astrbot_plugin_goofish_catcher` | 闲鱼 Agent 化购物助理。LLM 可直接调用工具完成搜索、订阅管理、收藏及任意复杂页面操作；支持关键词订阅轮询、上新降价检测、LLM 推荐排序与 WebUI 管理。本地或远程部 | 无 |
| 55 | `Soulter/astrbot_plugin_essential` | AstrBot Q群插件 / 随机动漫图片、以图搜番、Minecraft服务器、一言、今天吃什么、群早晚安记录、EPIC喜加一。 | 无 |
| 53 | `olozhika/astrbot_plugin_local_reminiscence` | AstrBot本地回忆插件 - 无需API、节约Token、自动唤起回忆 / AstrBot Local Reminiscence - No API, Save Tokens, A | 无 |
| 53 | `tinkerbellqwq/astrbot_plugin_help` |  | 无 |
| 51 | `nuomicici/astrbot_plugin_splitter` | 优化消息分段体验，方便小白操作，并添加更多分段配置（如图片跟随等） | 无 |
| 51 | `Catfish872/astrbot_plugin_favourpro` | 这是一个与现有好感度系统完全不同的插件。它不再是一个简单的数值计算工具，而是旨在为 AI 模拟一个**多维度、自主且保密的内心世界**。AI 会根据与用户的互动，真实地改变其内在的 | 无 |
| 51 | `exynos967/astrbot_plugin_memorix` |  | 无 |
| 49 | `Wyccotccy/astrbot_plugin_Wyc_Tools` |  | 无 |
| 48 | `Sisyphbaous-DT-Project/astrbot_plugin_palette` | AstrBot调色盘是一个 AstrBot WebUI 美化插件 | 无 |
| 46 | `Ars1027/astrbot_plugin_twitter` | 基于 Nitter 镜像站的 Twitter 推文转发插件，支持多会话独立订阅、定时推送、链接识别、合并转发与推文翻译。 | 无 |
| 45 | `aliveriver/astrbot_plugin_continuous_message` |  | 无 |
| 45 | `nuomicici/astrbot_plugin_Favour_Ultra` | 好感度/亲密关系插件。比目前所有好感度插件都要更加完善，具备自然衰减、主动搭话、查询权限配置等功能，使用数据库存储，读取速度更快 | 无 |
| 44 | `hl7235659-droid/astrbot_plugin_doubao_free` | 豆包(dola.com国际版)免费API插件 for AstrBot。填入Cookie即可使用聊天、图片识别、文生图、视频生成。支持多账号轮询。 | 无 |
| 44 | `Heximiao/astrbot_plugin_atrifeed` | 基于astrbot框架开发的亚托莉陪伴插件 | 无 |
| 42 | `advent259141/astrbot_plugin_astrbook` | astrbook的适配插件，让bot拥有在astrbook上聊天的能力 | 无 |
| 42 | `Seeeaa/AstrBot_Plugin_aPromptGuardian` | 开箱即用的流式提示词框架：优化→审查→过滤→复核→防护→核验→感知。维护优化系统优化提示词、屏蔽注入攻击、身份核验、信息感知、黑白名单与 WebUi 管理 | 无 |
| 41 | `sa1guu/astrbot_plugin_touchi` |  | 无 |
| 41 | `Clhikari/astrbot_plugin_office_assistant` | 这是一个为 AstrBot 设计的 Office 助手插件。它赋予大语言模型（LLM）直接操作文件的能力，支持读取并分析多种格式文件，以及生成 Office 文档和office互转 | 无 |
| 41 | `Kalospacer/astrbot_plugin_maid_agent` | 给astrbot用的大小姐-管家子agent工具调用插件 | 无 |
| 40 | `vacacia/astrbot_plugin_link_resolver` |  | 无 |
| 40 | `HSJ-BanFan/astrbot_plugin_telegram_forwarder` | 将 Telegram 频道消息转发到 QQ 群或 Telegram 频道。                   Forward Telegram channel messages  | 无 |
| 40 | `Sisyphbaous-DT-Project/astrbot_plugin_period` | 为 AstrBot 设计的生理周期模拟插件，让女性人格 Bot 拥有真实的身体感知。低侵入式提示词注入，支持四阶段周期计算、全局默认值、会话级权限控制和 UMO 白名单过滤。 | 无 |
| 39 | `anka-afk/astrbot_plugin_humanlike` | 让 AI 聊天机器人更像真人！通过智能识别用户意图来控制回复行为的 AstrBot 模块。 | 无 |
| 39 | `Sisyphbaous-DT-Project/astrbot_plugin_what_to_eat` | 是啊，吃什么 | 无 |
| 38 | `674537331/astrbot_plugin_mihome` | 基于 AstrBot 框架开发的支持自然语言调用的米家智能家居云端控制插件。 | 无 |
| 38 | `Luna-channel/astrbot_plugin_Conversa` | 一个让AI主动定时触发自然切入回复的插件 | 无 |
| 37 | `Soulter/astrbot_plugin_github_cards` | 根据群聊中 GitHub 相关链接自动发送 GitHub OpenGraph 图片 | 无 |
| 37 | `lxfight/astrbot_plugin_deepresearch` | 为 AstrBot 提供一种 Deepresearch 方案 | 无 |
| 36 | `Axi404/astrbot_plugin_astrbot_enhance_mode` | 阿斯特波特聊天增强模式，一个自建组合包，包含诸多功能，详见 README | 无 |
| 36 | `Heximiao/astrbot-plugin-wifepicker` | 这是一个用于astrbot的抽群友老婆的插件，只抽取发言过的群友 | 无 |
| 36 | `zcj-ui/astrbot_plugin_group_guardian` | [QQ群智能守护者]集28项群管功能与AI智能审核于一体的astrbot综合群管理插件。支持禁言/踢人/全体禁言/群名片/公告/群文件/精华消息/群打卡等完整群管工具集；内置智能审 | 无 |
| 35 | `middcom/astrbot_plugin_affection` | AstrBot plugin simulating Freudian dual drives: Libido (Eros/life instinct) and Aggression | 无 |
| 34 | `sukafon/astrbot_plugin_big_banana` | 绘图插件，支持Gemini规范和高级配置参数。 | 无 |
| 34 | `SXP-Simon/astrbot_plugin_love_formula` | 本插件基于“恋爱动力学”逻辑，通过分析群成员每日的社交行为数据，利用大语言模型生成一份极具“二次元/亚文化”色彩的恋爱成分诊断报告。 | 无 |
| 34 | `RC-CHN/astrbot_dg_lab_plugin` | 嗯，ai也需要一点情趣，你说是吧 | 无 |
| 33 | `chuyegzs/astrbot_plugin_meting` | AstrBot使用的MetingAPI插件 | 无 |
| 33 | `VincenttHo/astrbot_plugin_dzmm` | astrbot的DZMM聊天插件 | 无 |

### GalGame 风格聊天框

| Star | 仓库 | 说明 | 洛雪现状 |
|---|---|---|---|
| 153 | `bvzrays/astrbot_plugin_chuanhuatong` | 将 AstrBot 的纯文本回复转换成带立绘的 GalGame 风聊天框图片，支持情绪差分、多层文本、拖拽式 WebUI 布局与自定义组件模板。 | 无 |
| 38 | `PyuraMazo/astrbot_plugin_galgame_box` | 一款AstrBot社区插件，本插件几乎满足了用户的所有与Gal相关的需求。结合了VNDB、Bangumi、TouchGal、AnimeTrace的API， 能够提供全面、贴心的Ga | 无 |

### 语音 / 音色克隆 / 唱歌

| Star | 仓库 | 说明 | 洛雪现状 |
|---|---|---|---|
| 108 | `Esmerubphire/astrbot_plugin_feiyu_voice` | AstrBot plugin and local HTTP service for Feiyu TTS, RVC v1 and optional score singing | 部分：Fish TTS 单一音色；无克隆、无唱歌 |
| 87 | `muyouzhi6/astrbot_plugin_tts_emotion_router` | 按情绪路由到不同音色与语速的 TTS 插件（硅基流动 API，其他OpenAI语音接口api同样适配） | 部分：Fish TTS 单一音色；无克隆、无唱歌 |
| 59 | `Radiant303/astrbot_plugin_clonetts` | 基于 火山引擎音色克隆 (ICL) 的 AstrBot 文本转语音插件，使用自定义克隆音色让你的聊天机器人开口"说话"。 | 部分：Fish TTS 单一音色；无克隆、无唱歌 |

### 灾害预警

| Star | 仓库 | 说明 | 洛雪现状 |
|---|---|---|---|
| 105 | `Pancakes-Labs/astrbot_plugin_disaster_warning` | 基于 AstrBot 的新一代灾害预警平台。无缝聚合全球权威数据，实时追踪地震、海啸、气象与台风动态。搭载现代化 WebUI、专业级可视化渲染与智能本地感知，让硬核的灾害监控触手可 | 无 |

### 视频/媒体解析

| Star | 仓库 | 说明 | 洛雪现状 |
|---|---|---|---|
| 101 | `Soulter/astrbot_plugin_bilibili` |  | 部分：只读公开标题简介 + 链接解析插件；无视频理解 |
| 83 | `chenluQwQ/astrbot_plugin_bilibili_ai_bot` |  | 部分：只读公开标题简介 + 链接解析插件；无视频理解 |
| 80 | `miaoxutao123/astrbot_plugin_videos_analysis` |  | 部分：只读公开标题简介 + 链接解析插件；无视频理解 |
| 76 | `drdon1234/astrbot_plugin_media_parser` | 适配 AstrBot 的插件，聚合解析流媒体平台链接，转换为媒体直链发送 | 部分：只读公开标题简介 + 链接解析插件；无视频理解 |
| 59 | `storyAura/astrbot_plugin_biliVideo` | biliVideo · AstrBot B 站视频解析与 AI 总结 | 部分：只读公开标题简介 + 链接解析插件；无视频理解 |

### 桌宠 / 屏幕观察

| Star | 仓库 | 说明 | 洛雪现状 |
|---|---|---|---|
| 97 | `muyouzhi6/astrbot_plugin_desktop_assistant` | AstrBot 桌宠悬浮球（兼容云服务器Astrbot配合本地客户端使用） | 无（需要本地客户端或截图权限） |
| 88 | `menglimi/astrbot_plugin_screen_companion` | 智能屏幕观察插件，通过截图分析和环境感知提供个性化互动体验 | 无（需要本地客户端或截图权限） |

### 绘图（文生图/图生图）

| Star | 仓库 | 说明 | 洛雪现状 |
|---|---|---|---|
| 85 | `diaomin66/astrbot_plugin_omnidraw` |  | 部分：万相 2.6 文生图 + 自主策划 + 自评；无图生图 |
| 80 | `muyouzhi6/astrbot_plugin_gitee_aiimg` | 接入 Gitee AI 图像生成模型，支持lmm调用（让bot自拍给你看）。 | 部分：万相 2.6 文生图 + 自主策划 + 自评；无图生图 |
| 75 | `shskjw/astrbot_plugin_shoubanhua` | 支持第三方所有OpenAI绘图格式和原生Google Gemini 终极缝合怪，文生图/图生图插件 | 部分：万相 2.6 文生图 + 自主策划 + 自评；无图生图 |
| 55 | `piexian/astrbot_plugin_gemini_image_generation` | 图像生成插件，支持生图和改图，可以自动获取头像作为参考等。 | 部分：万相 2.6 文生图 + 自主策划 + 自评；无图生图 |

### 提示词注入防护

| Star | 仓库 | 说明 | 洛雪现状 |
|---|---|---|---|
| 85 | `oyxning/astrbot_plugin_antipromptinjector` | 还在因为自己的 Bot 被调教成猫娘而烦恼吗？ Anti-Prompt Injector 插件为您提供全面的提示词注入防护，保护您的 Bot 不被恶意用户操控！ | 部分：靠提示词与工具白名单；无专门防护插件 |

### 直播 / Live2D 演出

| Star | 仓库 | 说明 | 洛雪现状 |
|---|---|---|---|
| 66 | `menglimi/astrbot_plugin_live_stream_companion` | 面向 AstrBot 的直播陪伴、弹幕互动与 Live2D 演出控制插件。它把 B 站直播间弹幕读取、LLM 自动回应、VTube Studio 表情动作、TTS 嘴型联动和 OB | 无（服务器无 GPU，场景也不符） |

### 娱乐小功能

| Star | 仓库 | 说明 | 洛雪现状 |
|---|---|---|---|
| 56 | `MegSopern/astrbot_plugin_rollpig` | 每日为用户随机抽取专属“今日小猪”，并生成配图展示名称、描述和性格。无需配置，支持自定义猪猪库和素材。自动缓存结果，每日刷新，避免重复。适合群聊互动或签到，增添聊天趣味。 | 部分：表情/接梗，无抽签类 |

### 网页解析 / 截图

| Star | 仓库 | 说明 | 洛雪现状 |
|---|---|---|---|
| 41 | `Sakura520222/astrbot_plugin_web_analyzer` | 这是一个AstrBot插件，能够自动识别用户发送的网页链接，智能抓取解析内容，集成大语言模型进行深度分析和总结，支持网页截图、缓存机制和多种管理命令。 | 部分：只读标题摘要，无截图 |

## 三、建议

1. **优先做"图生图"**：现有万相 2.6 支持参考图，能把"画成这个样子"变成真能力，改动小、体验提升明显。
2. **其次补向量检索**：不必装重型插件，可先上本地 bge-m3 或云端 embedding，把 `events.db` 做索引；4GB 内存要谨慎，先量内存。
3. **不建议装**："自我进化/自动改代码"类（self_evolution、self_iterative_core、CodeMage）风险极高；直播/Live2D、桌宠、屏幕观察需要本地环境或 GPU，与本机不符。
4. **许可证**：AstrBot 生态大量插件是 AGPL-3.0，二次分发需同协议开源；商用前逐个确认。
5. **装任何插件前**：先在隔离目录试跑、量内存、确认与现有 memory/relationship/成长层是否重复注入。
