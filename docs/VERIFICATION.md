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
