# Git Analyzer Skill

An agent skill (Claude Code / any `SKILL.md`-compatible agent) that turns a GitHub repository URL into:

1. **A prompt**: a short, clean "reverse-engineered" prompt that would rebuild the project.
2. **A diagram**: a clickable Mermaid architecture map of the project.

[English](#english) · [فارسی](#فارسی)

---

## English

### Two methods

| | Quick mode | Standalone mode |
|---|---|---|
| How | Swap the domain to a ready-made service | The agent reads the repo itself via the GitHub API |
| Prompt | `github.com` → `gitreverse.com` | Agent writes the prompt from repo context |
| Diagram | `github.com` → `gitdiagram.com` | Agent builds and validates Mermaid |
| Depends on third-party sites | Yes | No |
| Private repos | No | Yes (with a token) |

### How it works

**Quick mode**
1. Parse `owner/repo` from the URL.
2. Build `https://www.gitreverse.com/owner/repo` (prompt) or `https://gitdiagram.com/owner/repo` (diagram).
3. Optionally fetch the page and show the result inline. If that fails, fall back to standalone mode.

**Standalone mode**
1. `scripts/fetch_repo.py` calls the GitHub API and writes one `context.md` with:
   - metadata (description, topics, language, license, homepage)
   - the full recursive file tree (capped)
   - the README (capped)
   - excerpts of key files (manifests, entry points, main source modules)
2. The agent reads that context and:
   - **Prompt**: writes one first-person prompt of 80–180 words ("Build me a … that …"), grounded only in the context.
   - **Diagram**: groups components into subgraphs, ties every node to a real path, adds edges, and emits a Mermaid `flowchart TD` with a `click` link to GitHub on each node. It then checks that every path exists, every node is connected and no ids repeat, and fixes the diagram before output.

### Install

```bash
git clone https://github.com/codedast/Git-Analyzers-skill
cp -r Git-Analyzers-skill/git-analyzer ~/.claude/skills/
```

Requires Python 3 (stdlib only). Optional: `GITHUB_TOKEN` or a logged-in `gh` CLI, for higher rate limits and private repos.

### Usage

Ask your agent:
- "Analyze https://github.com/wheresryan22/anatomy and give me the prompt"
- "Draw a diagram of owner/repo"
- "Quick mode, both, for https://github.com/owner/repo"

Script alone:

```bash
python git-analyzer/scripts/fetch_repo.py owner/repo --out context.md
```

### Credits

The quick mode uses [gitreverse](https://github.com/filiksyos/gitreverse) and [gitdiagram](https://github.com/ahmedkhaleel2004/gitdiagram). Both are MIT licensed. This skill is not affiliated with either project.

---

## فارسی

### این اسکیل چه می‌کند؟

یک لینک گیت‌هاب می‌گیرد و یکی از این دو را می‌دهد:

- **پرامت**: یک پرامت کوتاه و تمیز که پروژه را از نو می‌سازد.
- **نقشه**: یک نمودار معماری با `Mermaid` که روی هر بخش آن می‌شود کلیک کرد.

### دو روش

**روش اول: لینک آماده (سریع)**

- فقط دامنه‌ی لینک عوض می‌شود.
- برای پرامت:

```
https://www.gitreverse.com/owner/repo
```

- برای نقشه:

```
https://gitdiagram.com/owner/repo
```

- اسکیل صفحه را می‌خواند و نتیجه را نشان می‌دهد.
- فقط برای ریپوهای عمومی کار می‌کند.
- اگر سایت جواب ندهد، خودکار سراغ روش دوم می‌رود.

**روش دوم: مستقل و بدون این دو سایت**

۱. اسکریپت `fetch_repo.py` از طریق `API` گیت‌هاب این‌ها را جمع می‌کند:

- مشخصات پروژه: توضیح، موضوع‌ها، زبان، مجوز
- ساختار کامل پوشه‌ها و فایل‌ها
- فایل `README`
- تکه‌هایی از فایل‌های اصلی کد

۲. همه را در یک فایل `context.md` می‌نویسد.

۳. ایجنت آن فایل را می‌خواند و:

- **برای پرامت:**
  - یک پرامت اول‌شخص و کوتاه می‌نویسد.
  - طول آن بین `80` تا `180` کلمه است.
  - فقط چیزهایی را می‌گوید که واقعاً در پروژه هست.
- **برای نقشه:**
  - بخش‌های پروژه را گروه‌بندی می‌کند.
  - هر جعبه را به یک مسیر واقعی در ریپو وصل می‌کند.
  - رابطه‌ها را با فلش نشان می‌دهد.
  - روی هر جعبه لینک فایل در گیت‌هاب را می‌گذارد.
  - قبل از تحویل چک می‌کند که همه‌ی مسیرها واقعاً وجود دارند.

### مزیت روش دوم

- به سایت دیگری وابسته نیست.
- با توکن، ریپوی خصوصی را هم می‌خواند.
- کد منبع را هم می‌بیند، نه فقط `README`.

### نصب

```bash
git clone https://github.com/codedast/Git-Analyzers-skill
```

```bash
cp -r Git-Analyzers-skill/git-analyzer ~/.claude/skills/
```

- فقط `Python 3` لازم است.
- اختیاری: متغیر `GITHUB_TOKEN` یا ورود به `gh` برای سهمیه‌ی بیشتر.

### مجوز

- مجوز `MIT`
- روش اول از دو پروژه‌ی متن‌باز `gitreverse` و `gitdiagram` استفاده می‌کند.
- این اسکیل وابسته به آن دو پروژه نیست.
