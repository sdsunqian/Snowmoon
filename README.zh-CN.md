# Snowmoon · snowmoon.cc

中英双语响应式小说与漫画剧集网站。纯静态 HTML / CSS / JavaScript，无运行时依赖，无服务器、数据库、视频文件或第三方字体。面向 Cloudflare Pages；所有可提交的项目材料均位于本目录。

## 本地运行

需要 Node.js 22 或更高版本。正常构建不需要 Python、翻译 API 或原视频项目，也不访问外部网络。

```sh
npm run build
npm run check
npm run dev
```

打开 <http://localhost:4321/en/> 或 <http://localhost:4321/zh/>。`npm run dev` 预览已有的 `dist`，修改后重新构建。产物只在 `dist/`，不要把上一层视频项目作为站点部署目录。

## Cloudflare Pages 部署

将 **website 目录本身的内容**提交为独立 GitHub 仓库：

- Framework preset：None
- Build command：`npm run build`
- Build output directory：`dist`
- Root directory：仓库根目录（如果保留整个大项目结构，则设为 `website`；推荐独立仓库）
- 环境变量：`NODE_VERSION=22`

不需要 API Key、Functions、Wrangler 配置或数据库绑定。也可以将本地构建后的 `dist` 目录通过 Pages 的 Direct Upload 上传。

在 Cloudflare Pages 项目中添加自定义域名 `snowmoon.cc`。顶级域名需要在对应 Cloudflare zone 中按控制台指引配置 DNS；如需 `www.snowmoon.cc`，也添加该域名。站点已包含 www → apex 的重定向规则，主域名统一为 `https://snowmoon.cc`。GitHub 仓库创建、域名绑定和线上发布尚需在你的账户中操作，本项目不会自动更改 DNS。

Pages 的已核对限制：Free 每站 20,000 个文件、单文件 25 MiB；部署量请以 `dist/build-info.json` 的实际构建统计为准，而不是把它理解成一个固定的总空间限制。

- <https://developers.cloudflare.com/pages/platform/limits/>
- <https://developers.cloudflare.com/pages/get-started/git-integration/>
- <https://developers.cloudflare.com/pages/configuration/custom-domains/>

## 接入 YouTube

编辑 `content/youtube.json`，键名就是集数，空字符串表示待上线。支持 YouTube 常规链接、youtu.be、shorts 和 embed 链接，构建时校验域名与视频 ID。

```json
{
  "1": "https://www.youtube.com/watch?v=你的视频ID",
  "2": ""
}
```

不要直接复制示例中的中文占位符到正式配置。YouTube 视频 ID 必须为真实的 11 位 ID。每集已经有空值，无须删除其余集数。

如果要输出 Google 的 `VideoObject` 结构化数据，提供实际的上传时间（含时区）：

```json
{
  "1": {
    "url": "https://www.youtube.com/watch?v=你的视频ID",
    "uploadDate": "2026-10-19T08:00:00+08:00"
  }
}
```

未提供上传时间时仍显示可用的观看链接，但不会捏造上传日期来生成 `VideoObject`。未提供视频链接时不会展示假播放按钮或加载 iframe。点击观看跳转 YouTube，本站不托管 MP4。

`content/site.json` 中的 `sourceRepository` 可在 GitHub 开源后填写完整仓库链接，源码页面会自动显示。`youtubeChannel` 为后续扩展预留，目前页面以逐集链接为准。

## 页面结构

| 地址 | 内容 |
| --- | --- |
| `/en/`, `/zh/` | 中英首页 |
| `/{lang}/episodes/` | 32 集目录，支持搜索和分组筛选 |
| `/{lang}/episodes/1/` 至 `32/` | 独立剧集页，待填 YouTube 入口 |
| `/{lang}/characters/` | 六位主要人物与改编形象 |
| `/{lang}/world/` | 地点、制度和概念介绍 |
| `/zh/novel/` | 全部中文小说目录 |
| `/zh/read/chapter-1/` 至 `chapter-32/` | 完整中文译文 |
| `/{lang}/about/` | 内容来源、编辑说明、隐私说明 |
| `/{lang}/source/` | GPL v3、翻译方法、源码和素材来源下载 |

英文原作按章外链到 <https://vitalik.eth.limo/snowmoon/>，不在本站重新发表英文阅读页面。

## SEO 与 GEO

- 每页生成独立静态 HTML，关闭 JavaScript 仍能抓取正文、目录和链接。
- 英文和中文使用独立路径与 `lang`，等价页面具有双向 `hreflang` 和 `x-default`。只有中文版的完整阅读页不把英文简介页伪装成全文语言等价页。
- 独立 title、description、canonical、Open Graph、Twitter Cards、描述性 alt、图片尺寸与语义化标题。
- `sitemap.xml`、`robots.txt`、`llms.txt` 与章节深链；站点根地址 301 到英文首页。
- JSON-LD：WebSite、WebPage、ItemList、BreadcrumbList、Book、Chapter、FAQPage；可用时再添加真实 VideoObject。
- 保留原作来源、许可证、翻译身份、改编边界和人物设定说明，帮助搜索引擎和 AI 判断信息出处。
- FAQ 内容与结构化数据保持一致；不添加虚假的评分、发布日期、官方身份或观看数据。

`llms.txt` 是辅助发现文件，不是搜索排名或 AI 引用承诺。Google 的 AI 搜索遵循基础可索引性和内容质量原则；上线后仍需检查 Cloudflare 的 robots / AI 爬虫设置是否允许你希望允许的抓取。预览 pages.dev 域名可通过 Cloudflare 设置访问控制或搜索索引规则，避免预览版本与主域名竞争。

上线后在 Google Search Console 和 Bing Webmaster Tools 验证 `snowmoon.cc`，提交 `https://snowmoon.cc/sitemap.xml`。用 Google Rich Results Test 检查实际发布的页面；结构化数据不保证产生富结果。需要统计时可自行接入 Cloudflare Web Analytics，当前默认无统计脚本。

## 翻译与校订

`content/zh/` 中包含 32 章**机器辅助中文译文初稿**。生成流程使用 Google Translate 公开接口，并在翻译前应用 `content/glossary.json` 统一主要人名、地名与部分术语。保留段落、表格与原作示意图，图中文字保留英文。架空泽戈语发音可保留原文。未声称已由原作者审定或逐章人工校订。

正常构建只使用已提交的译文，不会调用翻译接口，不需要密钥。后续应逐章人工润色并对照原文检查隐喻、技术术语、对话语气和图表含义。直接修改 `content/zh/chapter-NN.html`，保留语义结构；如增删段落，同步更新对应的处理记录并说明改动，避免校验报告失真。

可复现的导入与压缩脚本在 `scripts/prepare_content.py`、`scripts/prepare_assets.py`，需要 `python -m pip install -r scripts/requirements.txt`。翻译脚本优先使用已提交的 `content/original/` 快照；压缩脚本是最初从父目录视频项目导入的辅助工具（依赖父目录 `concept-art` / `snowmoon-episode`），不是独立部署的前置步骤。正常构建无需重新翻译、压缩或抓取。公开翻译接口可能限流或改变，导入过程按批缓存、遇到段落标记丢失会拆分重试，失败不会静默略过。

重新运行翻译后，执行 `python scripts/review_translation.py`，应用 `content/translation-edits.json` 中针对原文段落的修正、恢复泽戈语发音、校正“长小时”计时单位，并核对所有表格和正文 SVG。该步骤包含定点的模型辅助校对，仍不等于全书人工润色。后续人工修改译文后也请更新审校记录与译文文件哈希，再运行构建检查。

`content/translation-report.json` 记录每章原文 SHA-256、处理块数和段落数，**只证明处理覆盖，不证明翻译质量**。导读副标题由本站添加，不冒充原作标题。

## 图片与开源材料

图片为项目已有插画，不新增付费生成调用。WebP 提供移动与桌面尺寸，图片保留宽高、使用响应式 srcset，非首屏图片懒加载。社交分享图片为压缩 JPEG。不会提交原视频、原始大图、音频、API 凭据或构建缓存。

`content/artwork-provenance.json` 包含每张使用素材的来源路径（项目相对路径）、原文件哈希、已有原始提示词与压缩参数。提示词中的角色设定和场景是改编材料；部分参考素材来自原视频项目。本站随附的优化图是已提交的网站素材，正常重建不依赖原视频文件。制作全视频的完整流水线不属于本网站源码包；若另行发布视频改编，请同时提供其对应的制作材料。

构建会在 `dist/source/snowmoon-website-source.tar.gz` 中自动提供**本网站完整对应源码**，包括压缩后的图片、译文、原文快照、脚本和许可证。源码归档排除 `dist`、`.git`、`.env*`、缓存与 QA 产物。

## License

Snowmoon is released under the **GNU GPL v3**: <https://www.gnu.org/licenses/gpl-3.0.html>.

This independent website, translations and project-specific adaptation materials are licensed **GPL-3.0-only**. Preserve the original source attribution and license. Full license text: [LICENSE](LICENSE). Independent project; no official affiliation or endorsement claimed.
