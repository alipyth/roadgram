"""Minimal Telegram Bot API client (standard library only).

The bot token is only used to build the request URL. It is never printed, logged or included in an error.
"""
import json
import mimetypes
import os
import urllib.error
import urllib.request
import uuid
from pathlib import Path


def api(token: str, method: str, payload: dict, files: dict[str, Path] | None = None, timeout: int = 60) -> dict:
    """Call a Bot API method. Always returns the decoded JSON ({"ok": bool, ...}); never raises, never leaks the token."""
    url = f"https://api.telegram.org/bot{token}/{method}"
    if files:
        boundary = uuid.uuid4().hex
        data = multipart(boundary, payload, files)
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    else:
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json; charset=utf-8"}
    req = urllib.request.Request(url, data=data, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (fixed https host)
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read())
        except Exception:
            return {"ok": False, "description": f"HTTP {e.code}"}
    except Exception as e:  # network down, timeout, bad JSON: keep only the class, never the URL
        return {"ok": False, "description": f"network error ({type(e).__name__})"}


def multipart(boundary: str, fields: dict, files: dict[str, Path]) -> bytes:
    out = bytearray()
    for k, v in fields.items():
        value = v if isinstance(v, str) else json.dumps(v)
        out += f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{value}\r\n'.encode()
    for k, path in files.items():
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        out += (f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{path.name}"\r\n'
                f"Content-Type: {ctype}\r\n\r\n").encode()
        out += path.read_bytes() + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return bytes(out)


class Bot:
    """Thin wrapper around one bot token and one chat. `call` is injectable so tests never touch the network."""

    def __init__(self, token: str, chat: str, call=api):
        self._token, self.chat, self._call = token, chat, call

    def request(self, method: str, payload: dict | None = None, files=None) -> dict:
        return self._call(self._token, method, payload or {}, files) if files else self._call(self._token, method, payload or {})

    def me(self) -> dict:
        return self.request("getMe")

    def chat_info(self) -> dict:
        return self.request("getChat", {"chat_id": self.chat})

    def my_member(self, bot_id: int) -> dict:
        return self.request("getChatMember", {"chat_id": self.chat, "user_id": bot_id})

    def create_topic(self, name: str) -> dict:
        return self.request("createForumTopic", {"chat_id": self.chat, "name": name})

    def send(self, text: str, thread: int | None = None) -> dict:
        body = {"chat_id": self.chat, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
        if thread:
            body["message_thread_id"] = thread
        return self.request("sendMessage", body)

    def edit(self, message_id: int, text: str) -> dict:
        return self.request("editMessageText", {"chat_id": self.chat, "message_id": message_id, "text": text,
                                                "parse_mode": "HTML", "disable_web_page_preview": True})

    def pin(self, message_id: int) -> dict:
        return self.request("pinChatMessage", {"chat_id": self.chat, "message_id": message_id,
                                               "disable_notification": True})

    def unpin(self, message_id: int) -> dict:
        return self.request("unpinChatMessage", {"chat_id": self.chat, "message_id": message_id})

    def send_document(self, path: Path, caption: str = "", thread: int | None = None) -> dict:
        fields = {"chat_id": self.chat}
        if caption:
            fields.update({"caption": caption, "parse_mode": "HTML"})
        if thread:
            fields["message_thread_id"] = str(thread)
        return self.request("sendDocument", fields, files={"document": path})


def read_env_file(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def credentials(root: Path) -> tuple[str | None, str | None]:
    """Token and chat id: process environment first, then <root>/.env."""
    file_env = read_env_file(root / ".env")
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or file_env.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID") or file_env.get("TELEGRAM_CHAT_ID")
    return token, chat
