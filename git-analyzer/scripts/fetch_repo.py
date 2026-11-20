#!/usr/bin/env python3
"""Collect GitHub repo context (metadata, tree, README, key file excerpts) into one Markdown file.

Usage: python fetch_repo.py <github-url | owner/repo> [--out context.md] [--max-tree 600]
Token: GITHUB_TOKEN / GH_TOKEN env var, else `gh auth token` if available. Stdlib only.
"""
import argparse, base64, json, os, re, subprocess, sys, urllib.error, urllib.request

API = "https://api.github.com"
KEY_FILES = ["package.json", "pyproject.toml", "setup.py", "requirements.txt", "Cargo.toml",
             "go.mod", "pom.xml", "build.gradle", "Gemfile", "composer.json", "Dockerfile",
             "docker-compose.yml", "SKILL.md", "CLAUDE.md", "AGENTS.md"]
ENTRY = re.compile(r"(^|/)(main|index|app|cli|server|__main__|lib|mod)\.(py|js|ts|tsx|mjs|go|rs|java|rb)$")
SRC_EXT = (".py", ".js", ".ts", ".tsx", ".mjs", ".go", ".rs", ".java", ".rb", ".c", ".cpp", ".cs", ".swift", ".kt")
SKIP = re.compile(r"(^|/)(node_modules|dist|build|vendor|\.git|__pycache__|test|tests|examples?|fixtures)/")


def token():
    t = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if t:
        return t
    try:
        return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10).stdout.strip() or None
    except Exception:
        return None


TOKEN = token()


def get(path):
    req = urllib.request.Request(API + path, headers={"Accept": "application/vnd.github+json",
                                                       "User-Agent": "git-analyzer-skill"})
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            sys.exit("GitHub rate limit hit. Set GITHUB_TOKEN or log in with `gh auth login`.")
        if e.code == 404:
            return None
        raise


def parse(s):
    s = s.strip()
    m = re.search(r"(?:github|gitreverse|gitdiagram)\.com/([^/\s]+)/([^/\s?#]+)", s)
    if m:
        owner, repo = m.groups()
    elif re.fullmatch(r"[\w.-]+/[\w.-]+", s):
        owner, repo = s.split("/")
    else:
        sys.exit("Could not parse repo from: " + s)
    return owner, re.sub(r"\.(git|md)$", "", repo)


def content(owner, repo, path, limit):
    d = get(f"/repos/{owner}/{repo}/contents/{path}")
    if not d or isinstance(d, list) or "content" not in d:
        return None
    text = base64.b64decode(d["content"]).decode("utf-8", "replace")
    return text if len(text) <= limit else text[:limit] + "\n… [truncated]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--out", default="context.md")
    ap.add_argument("--max-tree", type=int, default=600)
    ap.add_argument("--max-readme", type=int, default=15000)
    ap.add_argument("--max-files", type=int, default=8)
    a = ap.parse_args()

    owner, repo = parse(a.repo)
    meta = get(f"/repos/{owner}/{repo}")
    if not meta:
        sys.exit(f"Repo {owner}/{repo} not found (private? set a token).")
    branch = meta["default_branch"]
    tree = get(f"/repos/{owner}/{repo}/git/trees/{branch}?recursive=1") or {}
    items = tree.get("tree", [])
    paths = [("/" if i["type"] == "tree" else "") + i["path"] for i in items]
    files = [i["path"] for i in items if i["type"] == "blob"]

    out = [f"# {owner}/{repo}", "",
           f"- URL: {meta['html_url']}", f"- Default branch: {branch}",
           f"- Description: {meta.get('description') or '-'}",
           f"- Topics: {', '.join(meta.get('topics') or []) or '-'}",
           f"- Language: {meta.get('language') or '-'}",
           f"- Stars: {meta.get('stargazers_count')}  Forks: {meta.get('forks_count')}",
           f"- License: {(meta.get('license') or {}).get('spdx_id') or '-'}",
           f"- Homepage: {meta.get('homepage') or '-'}",
           f"- Private: {meta.get('private')}", ""]

    out += [f"## File tree ({len(files)} files{', GitHub truncated' if tree.get('truncated') else ''})",
            "Folders start with `/`.", "```"]
    shown = sorted(paths, key=lambda p: p.lstrip("/"))[: a.max_tree]
    out += [p.lstrip("/") + ("/" if p.startswith("/") else "") for p in shown]
    if len(paths) > a.max_tree:
        out.append(f"… and {len(paths) - a.max_tree} more")
    out += ["```", ""]

    rd = get(f"/repos/{owner}/{repo}/readme")
    if rd and "content" in rd:
        text = base64.b64decode(rd["content"]).decode("utf-8", "replace")
        if len(text) > a.max_readme:
            text = text[: a.max_readme] + "\n… [truncated]"
        out += [f"## README ({rd['path']})", "", text, ""]

    picks = [f for f in files if f.split("/")[-1] in KEY_FILES and f.count("/") <= 1]
    picks += [f for f in files if ENTRY.search(f) and not SKIP.search(f) and f not in picks]
    picks += sorted((f for f in files if f.endswith(SRC_EXT) and not SKIP.search(f) and f not in picks),
                    key=lambda f: (f.count("/"), f))
    out.append("## Key file excerpts")
    for f in picks[: a.max_files]:
        txt = content(owner, repo, f, 3000)
        if txt:
            out += ["", f"### {f}", "```", txt, "```"]

    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"Wrote {a.out}: {len(files)} files in tree, {min(len(picks), a.max_files)} excerpts.")


if __name__ == "__main__":
    main()
