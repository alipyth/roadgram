# Changelog

## 0.2.0 (2026-11-08)

### Added
- **Client approval buttons.** Every weekly roadmap message has inline buttons **✅ Approve delivery** and **✏️ Request changes** (Persian: «✅ تأیید تحویل» and «✏️ درخواست تغییر»).
  - Approve writes `- **Approved:** @client · date` into `ROADMAP.md`, removes the buttons, shows the approval in the message and sends a DM to every owner.
  - Request changes asks the client to reply. The reply is added to the week as a new open task `- [ ] ✏️ ...` and the earlier approval is removed.
  - `approvers` limits who counts as the client. By default it is anyone in the group who is not an owner (bots never count).
- **Milestone payments.** Add `- **Payment:** <amount>` to a week. When the client approves it, an invoice is posted in a new **💳 Payments** topic, showing `payment_details`. A reminder follows every `payment_reminder_days` days until an owner taps **💰 Mark as paid** or runs `roadgram paid N`, which writes `- **Paid:** date`.
- **`roadgram watch`.** A long-running mode: it syncs within seconds of every save of the roadmap, handles button presses live, posts the first week on its own, and sends invoices and reminders. `--once` runs a single round for cron or the Task Scheduler.
- **`roadgram hook install`** adds a git post-commit hook that runs `roadgram sync` in the background. `--uninstall` removes it.
- **`roadgram approve N [--by NAME]`** and **`roadgram paid N`** record an approval or a payment that happened outside Telegram. `--undo` removes it again.
- **`require_approval`** (off by default): the next week is posted only after the client approves the current one.
- **`auto_start`** (on by default): when nothing has been posted yet, `sync`/`watch` post the first open week and the next plan.
- `/whoami` (also `/id` and `/start`) in a chat with the bot replies with your Telegram id and the chat id.
- `roadgram check` warns when a webhook is set and reminds you to fill `owners`.
- Lines inside `<!-- ... -->` in the roadmap are ignored.

### Changed
- `roadgram sync` also handles button presses made since its last run (skipped while a `watch` is running).
- The roadmap message shows the delivery status (`⏳ waiting for the client` / `✅ approved`) and the payment status.
- Topic names from an older `roadgram.json` are merged with the defaults, so the new `payments` topic works without editing the config.
- AI agent instructions (`roadgram agent install`) cover `watch`, `approve`, `paid` and the `✏️` change-request tasks.

## 0.1.0

- First release: roadmap and plan messages per week, auto-advance, announcements, English/Persian, Gregorian/Jalali dates, AI agent integrations, single-file Windows build.
