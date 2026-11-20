---
name: git-analyzer
description: Analyze a GitHub repository from its URL and produce either (1) a short, clean "reverse-engineered" prompt that would recreate the project, or (2) a clickable Mermaid architecture diagram. Use whenever the user pastes a github.com link and asks what the project is, wants a prompt to rebuild it, wants a map/diagram/overview of its structure, or mentions gitreverse or gitdiagram. Has a quick mode (ready-made gitreverse.com / gitdiagram.com links) and a standalone mode (reads the repo directly via the GitHub API, works offline from those sites and for private repos with a token).
---

# Git Analyzer

Turn a GitHub repo URL into a **prompt** or a **diagram**.

## 1. Parse the input

Accept any of: `https://github.com/owner/repo`, `.../tree/branch/path`, `owner/repo`, or an existing
gitreverse/gitdiagram link. Extract `owner` and `repo` (strip `.git`, query, trailing slash).

Decide two things (ask once only if unclear; otherwise default to **standalone + both outputs**):
- **Output**: `prompt`, `diagram`, or `both`.
- **Method**: `quick` (link) or `standalone` (default).

## 2. Quick mode — ready-made links

Only the domain changes:

| Output  | Link |
|---------|------|
| prompt  | `https://www.gitreverse.com/{owner}/{repo}` |
| diagram | `https://gitdiagram.com/{owner}/{repo}` |
| diagram as Markdown | `https://gitdiagram.com/{owner}/{repo}.md` |

Give the user the links. If a web-fetch tool is available, fetch the page and show the result
(the prompt text, or the Mermaid block) so they don't have to open it. Limits: public repos only,
the sites may rate-limit or have no cached result yet; if fetching fails, fall back to standalone.

## 3. Standalone mode — no third-party sites

### 3a. Collect context

Run the bundled script (Python 3, stdlib only):

```bash
python scripts/fetch_repo.py owner/repo --out <scratch>/context.md
```

It writes one Markdown file with: metadata (description, topics, language, stars, license,
homepage), full recursive file tree (capped), README (capped), and excerpts of key files
(manifests like `package.json`/`pyproject.toml`, entry points, main source modules).
Set `GITHUB_TOKEN` (or have `gh` logged in — the script uses `gh auth token`) for higher rate
limits and private repos. If the script can't run, gather the same pieces with `gh api` or
web fetches of `api.github.com/repos/{owner}/{repo}`, `/readme`, `/git/trees/{branch}?recursive=1`.

Read `context.md` fully before writing anything.

### 3b. Output: prompt (gitreverse style)

Write ONE short prompt, as if the user were asking an AI coding agent to build this project
from scratch. Rules:
- First person, conversational: "Build me a … that …". 80–180 words, 1–3 paragraphs.
- Describe **what it does and how it should feel**, the key features, the main tech choices only
  when they matter (stack, runtime, format of output). No file-by-file listing.
- Ground every claim in the context; never invent features.
- End with a short title line above it: `**<Project idea in 3–6 words>**`.
Deliver it in a fenced `text` block so it can be copied.

### 3c. Output: diagram (gitdiagram style)

1. From the tree + excerpts, identify 3–7 **groups** (e.g. CLI, core, rendering, docs, examples)
   and 8–25 **components**, each tied to a real path in the tree.
2. Identify edges: data flow, calls, imports, "generates", "reads". Label edges briefly.
3. Write Mermaid `flowchart TD` with `subgraph` per group. Node ids: `[a-z0-9_]` only.
   Labels: plain text, no quotes/brackets/parentheses inside labels.
4. Add a click link for every node pointing at its real path:
   `click node_id "https://github.com/{owner}/{repo}/blob/{branch}/{path}"` (use `/tree/` for folders).
5. **Validate** before output: every node path exists in the tree, every node has ≥1 edge, ids
   unique, no unclosed subgraphs. Fix and recheck.
6. Before the diagram, give a 4–8 line plain overview of the architecture.

Deliver the Mermaid in a fenced `mermaid` block. If the user wants a file, save
`<repo>-diagram.md` (overview + mermaid) or render to an HTML page with Mermaid from a CDN.

## 4. Finish

Mention which method was used and its limits (quick: public only, third-party; standalone:
README/tree/excerpts only, large repos are sampled). Remind that the output is AI-made and
should be checked against the source.
