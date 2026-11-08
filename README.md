<div align="center">

<img src="assets/banner.svg" alt="roadgram" width="100%">

<br>

**English** · [فارسی](README.fa.md)

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?logo=telegram&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

[🌐 Website](https://jahaniwww.com) · [📣 Telegram channel](https://t.me/tarfandoonchannel)

</div>

---

## ✨ What is roadgram?

**roadgram** keeps a project's roadmap, weekly plan and announcements inside a Telegram group, so a developer and a project manager (or a client) can follow progress in one place, with no other tool.

<div align="center">
<img src="assets/flow.svg" alt="ROADMAP.md → roadgram sync → Telegram" width="90%">
</div>

You write the roadmap as a normal Markdown checklist in your repository. After every change you run one command and the Telegram messages update themselves.

## 🚀 Features

| | Feature | Details |
|---|---|---|
| 🗺 | **Roadmap topic** | One message per week with a progress bar and ✅/⬜ per task. Edited in place, pinned. |
| 📅 | **Next-week plan** | Goals of the coming week plus what is still open. Only the newest plan stays pinned. |
| ⏭ | **Auto-advance** | When every task of the week is ticked, the next roadmap and plan are posted and pinned. |
| 📣 | **Updates topic** | Announcements and files with `roadgram post`, only when you send them. |
| 🌍 | **Two languages** | Messages in English or Persian, with Gregorian, Jalali or both dates. |
| 🤖 | **AI agent ready** | `roadgram agent install` teaches Claude Code, Codex, Cline, Cursor and Gemini CLI to use it. |
| 📦 | **Zero dependencies** | Standard library only, plus a single-file `roadgram.exe` for Windows. |

## 📥 Install from scratch

roadgram needs **Python 3.10 or newer** and **git**. It has no other dependencies. A Telegram account is needed for the bot (see [Quick start](#-quick-start)).

### Windows

```powershell
# 1. Install Python and git (skip what you already have)
winget install Python.Python.3.12
winget install Git.Git
# close and reopen PowerShell, then check:
python --version

# 2. Install roadgram
python -m pip install git+https://github.com/alipyth/roadgram.git

# 3. Check it works
roadgram --version
```

If `roadgram` is "not recognized", use `python -m roadgram --version` instead, or add Python's `Scripts` folder to `PATH`.

### macOS

```bash
# 1. Install Python and git (with Homebrew: https://brew.sh)
brew install python git
python3 --version

# 2. Install roadgram (pipx keeps it isolated and puts `roadgram` on your PATH)
brew install pipx && pipx ensurepath
pipx install git+https://github.com/alipyth/roadgram.git

# 3. Check it works (open a new terminal first)
roadgram --version
```

### Linux (Debian / Ubuntu; other distros use their own package manager)

```bash
# 1. Install Python, pip and git
sudo apt update
sudo apt install -y python3 python3-pip pipx git
python3 --version        # must be 3.10 or newer

# 2. Install roadgram
pipx ensurepath
pipx install git+https://github.com/alipyth/roadgram.git

# 3. Check it works (open a new terminal first)
roadgram --version
```

On Fedora use `sudo dnf install python3 pipx git`, on Arch `sudo pacman -S python python-pipx git`.

### From a clone (any OS, for development)

```bash
git clone https://github.com/alipyth/roadgram.git
cd roadgram
python -m pip install .            # or: python -m pip install -e .   (editable)
python -m unittest discover -s tests -t .      # optional: run the tests
```

You can also skip installing and run it straight from the clone: `python -m roadgram --version`.

### Update and uninstall

```bash
pipx upgrade roadgram          # or: python -m pip install --upgrade git+https://github.com/alipyth/roadgram.git
pipx uninstall roadgram        # or: python -m pip uninstall roadgram
```

### Windows: a single `roadgram.exe` (no Python on the target PC)

On a PC that has Python, build it once and copy `dist\roadgram.exe` anywhere:

```powershell
git clone https://github.com/alipyth/roadgram.git
cd roadgram
powershell -File build_exe.ps1     # runs the tests, installs PyInstaller, builds dist\roadgram.exe
.\dist\roadgram.exe --version
```

## 🧭 Your first run, step by step

1. Do the [Telegram setup](#1-set-up-telegram-once-5-minutes) and keep the **bot token** and **group id** at hand.
2. Open a terminal **in your project folder** (the repo you want to track).
3. `roadgram init --name "My App"` creates `roadgram.json`, `.env`, `ROADMAP.md` and updates `.gitignore`.
4. Open `.env` and paste your values:
   ```ini
   TELEGRAM_BOT_TOKEN=123456:ABC-your-token
   TELEGRAM_CHAT_ID=-1001234567890
   ```
5. Edit `ROADMAP.md` to your real weeks and tasks.
6. `roadgram check` must report that the token, group and rights are fine.
7. `roadgram week 1 --dry-run` shows the message without sending it.
8. `roadgram week 1` and `roadgram plan 2` post and pin the real messages.
9. From now on: tick tasks in `ROADMAP.md`, then run `roadgram sync`.

## 👀 What it looks like

Output of `roadgram week 1` (a message in your Telegram topic):

```text
🗺 Week 1: Foundation
Progress: 1 of 3 tasks (33%)
▰▰▰▱▱▱▱▱▱▱

✅ Set up the repository and CI
⬜ Write the first working version of the core feature
⬜ Write tests for the core feature

Week output: a working core feature with tests

📅 Last updated: 7 November 2026

#roadmap #week1 #MyApp
```

## ⚡ Quick start

### 1. Set up Telegram (once, ~5 minutes)

1. Open **@BotFather** → `/newbot` → copy the **token**.
2. Create a group (or use an existing one) and add the bot.
3. For one topic per section, turn on **Topics** in the group settings. Without topics roadgram still works and posts to the main chat.
4. Make the bot an **admin** with **Pin messages** and, if topics are on, **Manage topics**.
5. Find the group id (like `-1001234567890`): forward a group message to **@RawDataBot**.

> [!IMPORTANT]
> **Keep the token secret.** It lives only in `.env`, which `roadgram init` adds to `.gitignore`. roadgram never prints it, logs it or writes it into messages. If it leaks, run `/revoke` in @BotFather.

### 2. Run it

```powershell
# in your project folder (roadgram.exe, or: python -m roadgram ...)
roadgram init --name "My App" --lang en --calendar gregorian   # roadgram.json, .env, ROADMAP.md, .gitignore
# put TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID into .env, then:
roadgram check                 # verifies token, group, topics and the bot's rights
roadgram week 1 --dry-run      # preview the message (sends nothing)
roadgram week 1                # post (and pin) the roadmap of week 1
roadgram plan 2                # post (and pin) the plan of week 2
# ... work, tick tasks in ROADMAP.md ...
roadgram sync                  # edit every posted message; post the next week when this one is done
roadgram post --text "Release candidate is ready" --pin
roadgram post --document report.pdf --text "Weekly report"
roadgram status                # progress in the terminal, sends nothing
```

> [!TIP]
> Run `roadgram sync` after every change to `ROADMAP.md`. A git hook or CI step works well.

### 3. The roadmap file

```markdown
## Week 1: Foundation
- [x] Set up the repository and CI
- [ ] First working version of the core feature
- **Checkpoint 1: Friday**              (optional, shown in the plan)
- **Output:** a working core feature    (optional)

## Week 2: Launch
- [ ] ...
```

A heading `## Week N: ...` (also `Sprint`, `Phase`, `Milestone`, or Persian `## هفته N: ...`) starts a week. `- [ ]` and `- [x]` lines are its tasks.

## 🤖 Use it from AI coding agents

```powershell
roadgram agent install            # auto-detects Claude Code, Codex, Cline, Cursor, Gemini CLI
roadgram agent install all        # or name them: claude codex cline cursor gemini
roadgram agent install --global   # for your user instead of only this project
roadgram agent install --uninstall
```

It writes each tool's own format: a skill and `/roadgram-sync` command for Claude Code (plus a `.claude-plugin`), a marked block in `AGENTS.md` (Codex) and `GEMINI.md`, `.clinerules/roadgram.md` (Cline) and `.cursor/rules/roadgram.mdc` (Cursor). Re-running updates in place and keeps your own text. The agent is told never to read `.env`.

## 📖 Commands

| Command | What it does |
|---|---|
| `roadgram init` | Creates `roadgram.json`, a `.env` template, a sample `ROADMAP.md` and `.gitignore` entries. Never overwrites without `--force`. |
| `roadgram check` | Checks token, group, topics and the bot's admin rights. |
| `roadgram week N [--dry-run]` | Posts or edits the roadmap message of week N (pinned on first post). |
| `roadgram plan N [--dry-run]` | Posts or edits the plan message of week N; older plans are unpinned. |
| `roadgram sync` | Edits all posted messages; advances when the current week is fully ticked. |
| `roadgram post` | Sends a **new** message or file to a topic (`--topic`, `--text`, `--file`, `--document`, `--pin`, `--raw-html`, `--dry-run`). |
| `roadgram status` | Prints progress from the roadmap file. |
| `roadgram agent install` | Installs roadgram instructions for AI coding agents. |

Global option: `--dir <folder>` (default: current folder; `roadgram.json` is searched upwards).

## ⚙️ Configuration (`roadgram.json`)

| Key | Meaning | Default |
|---|---|---|
| `project` | Name | folder name |
| `hashtag` | Hashtag added to messages (`""` = none) | name without spaces |
| `language` | `en` or `fa` | `en` |
| `calendar` | `gregorian`, `jalali` or `both` | `gregorian` |
| `roadmap_file` | Path to the Markdown roadmap | `ROADMAP.md` |
| `topics` | Topic names by key: `roadmap`, `plan`, `updates` (add your own keys for `roadgram post --topic`) | per language |
| `max_item_len` | Longest task text in a message | `120` |
| `advance` | Auto-post the next week when the current one is done | `true` |

State (message and topic ids) is kept in `.roadgram/state.json`. If you delete a message in Telegram, remove its id from that file and the next run posts a new one.

## 🛠 Build the executable

```powershell
powershell -File build_exe.ps1     # runs the tests, then builds dist\roadgram.exe with PyInstaller
```

Run the tests alone: `python -m unittest discover -s tests -t .`

## 🔒 Notes and limits

- roadgram only sends what you ask for: `week`, `plan`, `sync` and `post`. It never reads group messages.
- The token never appears in output or errors; network errors show only the error class.
- Telegram messages are limited to 4096 characters. Long weeks are shortened with "… and N more".
- Windows editors may add a BOM to `.env` and `roadgram.json`; roadgram reads both correctly.

---

<div align="center">

MIT License · Made by [Ali Jahani](https://jahaniwww.com)

</div>
