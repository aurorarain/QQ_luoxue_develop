# 服务器网页后台与插件补全

## 网页入口

后台由服务器 Nginx 通过 HTTPS 代理到服务器本机的 AstrBot 6185 端口，不依赖用户电脑、SSH 隧道或 BAT。Nginx 示例见 `deploy/astrbot-nginx.conf.example`。

运行实例的实际网址、密码和证书文件不随源码发布。后台使用独立的随机强密码、PBKDF2 存储及登录限流；不是 NapCat 的口令，也不是 API Token 页面。证书由 certbot 定时续期，部署钩子验证并重载 Nginx。机器人及网页均随服务器服务运行。

## 新增插件与适配

| 插件 | 版本 | 本实例的设置 |
| --- | --- | --- |
| [QQ 资料管理增强版](https://github.com/Akusative/astrbot_plugin_qqprofile_ex) | v3.0.0 | 仅主人私聊可触发；签名六小时、状态两小时冷却；自动改昵称、人格切换和定时状态关闭 |
| [AnySearch](https://github.com/AgIzT/astrbot_plugin_anysearch) | v0.3 | 匿名模式，无额外 Key；支持搜索和正文提取；独立群回复也优先调用其客户端，失败回退原搜索 |
| [万能解析器](https://github.com/Zhalslar/astrbot_plugin_parser) | v1.6.1 | 仅主人私聊和指定群；单资源最多 20MB/3分钟，五分钟去重，每三小时清理缓存；平台登录与 Cookie 仍按平台要求 |
| [QQ Tools](https://github.com/YUMU1658/astrbot_plugin_qq_tools) | v0.2.1 | 当前会话历史、资料、头像、消息详情、引用、撤回、戳一戳；浏览器、Gemini、任意唤醒、禁言踢人等关闭 |
| [关系／情绪](https://github.com/qsbb/astrbot_plugin_relationship) | 0.14.3 | 只处理主人私聊，提供疲劳、短期态度、好感/信任/熟悉度及衰减参考；跨平台记忆关闭，不接管人格和发送 |

QQ Tools 上游已归档，按审核的提交固定版本，不视为持续维护项目。签名是公开信息，资料插件引导词要求不写私人聊天细节和个人资料。昵称默认保持不变。

以上新增五项；原有 memory、qzone、luoxue_social、luoxue_voice 保留，共九个外部/定制插件，另有 AstrBot 内置模块。原日记和长期记忆未迁移或清空；新的关系插件激活时，旧关键词心境标签暂停，避免两个模块相互覆盖。

## 权限

`prepare_reviewed_plugins.py` 在原源码上添加聊天入口及工具执行检查。QQ 资料和关系插件只接收主人私聊；解析仅允许既定会话；QQ Tools 工具只供主人私聊调用，私聊戳一戳只能指向主人，撤回必须有本轮明确意图。群模型不获得私聊工具或历史；群联网通过只含本条公开查询的独立路径执行。

QQ Tools 不向原消息追加 `[MSG_ID:...]`，不接管已有 @ 处理，也不自动下载浏览器。原系统的 Shell/文件/环境配置工具禁用保持有效。群友不能通过新插件写人设。

用户可在 AstrBot 网页的「插件管理 → 已安装 → 插件配置」调整第三方参数。新插件带本地适配，直接点击更新可能覆盖保护，升级应重新运行适配与边界检查。

## 可复现与许可

精确提交及许可证见 `deploy/reviewed-plugins.json`。所有上游完整源码和许可证保存在服务器插件目录，公开仓库保存版本固定清单、适配源码与下载脚本，不复制其私人配置。

```text
python scripts/download_reviewed_plugins.py <review-directory>
python scripts/prepare_reviewed_plugins.py <review-directory> <prepared-directory>
```

备份并安装准备后的目录，安装万能解析器 requirements，然后由服务器脚本 `configure_reviewed_plugins.py` 初始化。已有 Key 不会写进公开版本清单。AGPL 的 QQ 资料管理源码及我们的全部适配可由上述固定提交和脚本重现，原版权/许可证保留。

配置初始化兼容 AstrBot 的 UTF-8 BOM 文件和 `template_list` 类型；解析器首次加载的模板必须是列表。日常手动修改请使用 WebUI，不需要反复运行初始化脚本。

## 验证

- 公网 HTTPS、证书校验、账号登录和登录后的插件接口通过。
- 九个扩展均在真实运行实例显示 activated=true。
- 40 项回归检查通过；另有七项真实第三方方法拒绝越权调用检查，未发 QQ 测试消息。
- 服务器 AnySearch 匿名请求实际返回带来源的结果。
- 万能解析器实际加载 39 个关键词入口，并只读解析 B站样例为 ParseResult。此项不是已下载/发送视频的证明。
- 新签名、状态修改、QQ 撤回及各平台视频下载尚未做真实写入验收；没有批量登录所有媒体平台。
