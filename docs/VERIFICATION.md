# Verification — 2026-10-28

## Passed

- 7 boundary regression tests passed in the server AstrBot environment.
- Social plugin v2.0.0 loads successfully; OneBot reconnects after AstrBot restart.
- Real group-member-list API returned a nonempty list (3 members during this deployment).
- Qzone login/cookie refresh and own-feed read succeeded; the original autonomous post exists.
- 12 public Twemoji seed stickers installed with categories, JSON index and Markdown attribution/index.
- Public model call succeeded.
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
