# Snowmoon · snowmoon.cc

A responsive, bilingual website for the science fiction novel **Snowmoon** and its illustrated episode adaptation. Built with static HTML, CSS, and JavaScript for Cloudflare Pages.

[简体中文](README.zh-CN.md) · [Original English novel](https://vitalik.eth.limo/snowmoon/) · [GPL v3](LICENSE)

**All 32 episodes are now available on YouTube.** [View the complete playlist](https://www.youtube.com/playlist?list=PLC2mjVqLQUHA) · [Start with Episode 1](https://www.youtube.com/watch?v=B-KEK2XJxa0) · [GitHub repository](https://github.com/sdsunqian/Snowmoon)

## Features

- English and Simplified Chinese homepages, episode guides, character introductions, and world guides.
- Individual pages for all 32 episodes, with configurable YouTube links.
- A complete, machine-assisted Chinese translation of all 32 chapters, including original tables and diagrams.
- Reading controls for font size and dark mode, with preferences stored locally.
- Responsive WebP artwork, lazy loading, and no locally hosted video or audio files.
- Static, crawlable pages with multilingual SEO metadata and source attribution.
- A downloadable archive of the corresponding website source, generated during the build.

The project is an independent adaptation and reading companion. It is not the original author's official website and does not imply endorsement. The Chinese translation is a draft with targeted corrections, not a fully human-edited or author-approved edition.

## Requirements and local development

Use **Node.js 22 or later**. The website has no npm dependencies. Normal builds do not require Python, translation services, API keys, the parent video project, or network access.

```sh
npm run build
npm run check
npm run dev
```

Open <http://localhost:4321/en/> or <http://localhost:4321/zh/>.

`npm run dev` serves the existing `dist/` directory. Rebuild after changing source files. Set the `PORT` environment variable to change the preview port.

## Deploy to Cloudflare Pages

Commit the contents of this directory as a standalone GitHub repository and connect it to Cloudflare Pages.

| Setting | Value |
| --- | --- |
| Framework preset | None |
| Build command | `npm run build` |
| Build output directory | `dist` |
| Root directory | Repository root |
| Environment variable | `NODE_VERSION=22` |

If this directory remains inside a larger repository, set the Pages root directory to `website`. Deploy only the generated `dist/` directory, never the parent video project.

No Functions, database bindings, API keys, or Wrangler configuration are required. You can also build locally and upload `dist/` through Pages Direct Upload.

Add `snowmoon.cc` in your Pages project's custom domain settings and follow Cloudflare's DNS instructions. Add `www.snowmoon.cc` separately if needed. The generated redirect rules send `www` traffic to the apex domain and the root path to `/en/`. Canonical URLs use `https://snowmoon.cc`.

The project does not automatically create a GitHub repository, change DNS, or publish a production deployment.

Cloudflare Pages Free supports up to 20,000 files per site and a maximum individual asset size of 25 MiB. The build checks these constraints and records actual file counts and sizes in `dist/build-info.json`.

- [Pages limits](https://developers.cloudflare.com/pages/platform/limits/)
- [Git integration](https://developers.cloudflare.com/pages/get-started/git-integration/)
- [Custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/)

## Add YouTube videos

`content/youtube.json` is populated with the verified viewing links, actual upload timestamps, and YouTube durations for all 32 episodes. `content/youtube-release.json` records the public title-to-episode mapping and verification source. Normal builds use these checked-in files without contacting YouTube.

Episodes are matched by the `EP` number in their titles, independently of playlist position. The website lists EP1 through EP32 in chapter order. The YouTube playlist currently displays EP32 first; reorder it on YouTube if you want automatic EP1-to-EP32 playlist playback. Individual site viewing links open the selected episode directly.

To replace a video, edit its episode-number key in `content/youtube.json` and update its verification record. An empty string is supported for a future or unavailable release.

```json
{
  "1": "https://www.youtube.com/watch?v=YOUR_VIDEO_ID",
  "2": ""
}
```

Replace `YOUR_VIDEO_ID` with the real 11-character video ID. Keep the remaining episode entries. Standard YouTube, youtu.be, Shorts, and embed URLs are supported; the build validates the HTTPS host and video ID.

To generate `VideoObject` structured data, include the video's actual upload timestamp with a timezone:

```json
{
  "1": {
    "url": "https://www.youtube.com/watch?v=YOUR_VIDEO_ID",
    "uploadDate": "2026-10-19T08:00:00+08:00"
  }
}
```

The ID and timestamp above are placeholders: replace both with actual video details. Without an upload date, the viewing link still works, but the build does not invent metadata. Without a video link, the page displays a forthcoming message. Videos open on YouTube; the site does not load third-party players or host MP4 files.

`content/site.json` includes the GitHub repository, the publisher's YouTube channel, and `youtubePlaylist`. The playlist is linked from the episode directory, individual episode pages, and footer. The homepage links directly to EP1, and episode cards have their own viewing links. Keep these values current when replacing a playlist or moving the repository.

## Routes

| Route | Content |
| --- | --- |
| `/en/`, `/zh/` | Localized homepages |
| `/{lang}/episodes/` | All 32 episodes, with search and range filters |
| `/{lang}/episodes/{1..32}/` | Individual episode pages and YouTube links |
| `/{lang}/characters/` | Six character introductions and adaptation artwork |
| `/{lang}/world/` | Places, institutions, and concepts |
| `/zh/novel/` | Complete Chinese chapter directory |
| `/zh/read/chapter-{1..32}/` | Full Chinese chapter translations |
| `/{lang}/about/` | Project information, editorial disclosures, and privacy |
| `/{lang}/source/` | Source download, GPL v3, translation method, and provenance |

`{lang}` is `en` or `zh`. English reading links point to the corresponding chapter on the [original website](https://vitalik.eth.limo/snowmoon/); the site does not republish English reading pages.

## SEO and generative search discovery

- Every page is generated as static HTML. Core text, chapter directories, and links remain available without JavaScript.
- Localized pages have separate URLs, explicit document languages, reciprocal `hreflang`, and `x-default` annotations where equivalent pages exist. Chinese full-text reading pages do not misrepresent English summary pages as full-text equivalents.
- Pages include unique titles, descriptions, canonical URLs, Open Graph and Twitter metadata, descriptive image alternatives, image dimensions, and semantic headings.
- The build generates `sitemap.xml`, `robots.txt`, `llms.txt`, and chapter deep links.
- JSON-LD includes WebSite, WebPage, ItemList, BreadcrumbList, Book, Chapter, and FAQPage. VideoObject is generated only when real video information is supplied.
- Original sources, license terms, translation status, and adaptation boundaries are stated explicitly. FAQ markup matches the on-page answers.

`llms.txt` is a discovery aid, not a promise of search rankings or AI citations. Google AI search features rely on standard indexing, content quality, and accessibility principles. After deployment, review Cloudflare's crawler settings to ensure they allow the access you intend. Consider access controls or indexing rules for preview domains to avoid duplicate public previews.

Verify `snowmoon.cc` in Google Search Console and Bing Webmaster Tools, submit `https://snowmoon.cc/sitemap.xml`, and validate live pages with Google's Rich Results Test. Structured data does not guarantee rich results. Analytics are not enabled by default; Cloudflare Web Analytics can be added separately.

## Chinese translation and editorial corrections

`content/zh/` contains all 32 chapters as a **machine-assisted translation draft**. The import tool uses the Google Translate public endpoint and `content/glossary.json` to protect recurring names and terminology. Original paragraphs, tables, and SVG diagrams are preserved. Diagram labels remain in English, and invented Dzegoban phonetics may remain in their original form.

The translation has not been fully human-edited or approved by the original author. Further editing should compare the original text for meaning, technical terms, dialogue, and literary tone. Episode subtitles are editorial additions; the original chapters are numbered.

Normal builds use the checked-in translations and make no translation requests. To edit a chapter, update `content/zh/chapter-NN.html`, preserve its semantic structure, and update the relevant reports and file hashes. Paragraph counts and hashes establish processing coverage, not translation accuracy.

Optional import and review tools require Python dependencies:

```sh
python -m pip install -r scripts/requirements.txt
python scripts/prepare_content.py
python scripts/review_translation.py
```

`prepare_content.py` prefers the checked-in snapshots in `content/original/`. Its initial-import fallback uses the parent project's `source/` directory. The public translation endpoint may change or rate-limit requests. Progress is cached by batch, lost markers cause batches to be split and retried, and failures do not silently omit text.

`review_translation.py` applies source-indexed corrections from `content/translation-edits.json`, restores invented-language text, corrects the fictional longhour unit, and checks table and diagram preservation. These are targeted, model-assisted corrections, not a claim of complete human editing. After manual edits, update the reports and translation hashes before running the build checks.

`content/translation-report.json` records original source hashes, processed block counts, preserved structures, and translation hashes. Original HTML snapshots are included for comparison and reproducibility.

## Artwork and source materials

The site reuses existing AI-assisted illustrations from the associated motion-comic project. No new paid image-generation requests are needed. Responsive WebP variants serve mobile and desktop screens; offscreen images load lazily, and the social sharing image is an optimized JPEG.

`content/artwork-provenance.json` records project-relative source paths, original file hashes, recovered illustration prompts, and conversion parameters. The prompts and character designs are adaptation materials. Committed optimized images are sufficient to build this website independently.

`scripts/prepare_assets.py` is an optional historical import tool that reads artwork and production metadata from the parent `concept-art/` and `snowmoon-episode/` directories. It is not part of the standalone website build. The complete production pipeline for all 32 videos is outside this website source package; publishing the videos separately should include their corresponding production materials.

Each build creates `dist/source/snowmoon-website-source.tar.gz`, containing the corresponding website source, optimized artwork, translations, original snapshots, scripts, and license. Generated output, Git metadata, environment files, caches, and QA artifacts are excluded. Source videos, audio, raw production images, and API credentials are not part of this repository.

## Privacy

The site has no accounts, advertising cookies, or analytics scripts. Reading preferences are stored only in the visitor's browser. YouTube and other external services load only after following their links. The hosting provider may process request data to deliver and secure the site.

## License and attribution

**Snowmoon is released under GNU GPL v3.** Original source: <https://vitalik.eth.limo/snowmoon/>.

This independent website, its translations, and project-specific adaptation materials are licensed **GPL-3.0-only**. Retain the original source attribution and license notices when redistributing or modifying the project, and provide the corresponding source as required by GPL v3.

See [LICENSE](LICENSE) for the full license text and [NOTICE.md](NOTICE.md) for source, adaptation, and translation disclosures.
