# QQ 洛雪

基于 AstrBot + NapCat 的 AI 陪伴机器人扩展。服务器无需 GPU；对话、识图、语音和可选生图均使用 API。

## 已实现

- 单一主人私聊、指定群全员可互动；群友不能修改持久人格。
- 公共群人格与私人恋人人格分离；群消息可被动观察但不主动插话。
- 群记忆单向供主人私聊检索，群模型不读取私人记忆或工具。
- 成员列表缓存、新成员欢迎、经真实成员名单验证的 @、戳一戳冷却。
- 持久表情库、索引、轮换去重、视觉审核收集主人表情；私人素材不出私聊。
- OpenAI-compatible Images API 适配，无需 ComfyUI。需要独立服务商密钥，未配置时明确提示不可用。
- 主人专属低频主动私聊，自主决定是否发说说；公开动态点赞、评论与楼中楼去重回复。
- 有界的公开资讯阅读，供私聊或说说分享；不会把标题摘要说成完整观看过视频。
- 模型工具白名单，只保留记忆/成长/语音；不开放Shell、任意文件和环境配置。

## 安装

1. 先部署并连通 AstrBot 与 NapCat，完成自己的 QQ 登录；保持 `/AstrBot/data` 共享挂载。
2. 将 `plugins/luoxue_social` 放到 AstrBot 的 `data/plugins/`。
3. 将 `config/settings.example.json` 复制到 AstrBot `data/config/luoxue_social_settings.json`，本地填写自己的QQ号和可选生图API。该文件不可提交。
4. 语音、长期记忆插件属于独立集成；本仓库不携带私人画像、人设全文、聊天或登录态。
5. 空间服务适配 [Zhalslar/astrbot_plugin_qzone](https://github.com/Zhalslar/astrbot_plugin_qzone) v3.1.3。其原始自动任务、聊天监听和LLM发布工具需关闭，避免绕过本项目控制器；部署脚本会移除其filter装饰器并禁用原调度。原插件另行安装，许可证归原仓库。
6. 运行 `python -m unittest discover -s tests`，备份后部署，重启 AstrBot。首次上线先核验 `/status`、权限与空间只读探测。

具体安装/授权限制、各项实测状态见 [部署说明](docs/DEPLOYMENT.md)。本项目没有抖音授权凭据，不宣称已经能发抖音或刷其个性化推荐流。

## 数据边界

`data/plugin_data/luoxue_social/` 是私有运行数据。不要提交 events.db、state.json、health.json、表情素材、API配置、QQ缓存或聊天记录。

自主活动是定时唤醒、状态、记忆和模型判断形成的行为，不是自我意识或真实线下生活。

修改服务器代码后：同步源码 → 测试 → 部署 → 验证 → 安全扫描 → Git提交推送。敏感参数只在服务器私有配置维护。
