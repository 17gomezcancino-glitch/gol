from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import List

from chat_models import ChatMessage


class ConversationHistory:
    """Persists chat transcripts for each authenticated user."""

    def __init__(self, storage_dir: Path) -> None:
        self._storage_dir = storage_dir
        self._lock = threading.Lock()

    def load(self, user_id: str) -> List[ChatMessage]:
        path = self._path_for_user(user_id)
        if not path.exists():
            return []
        try:
            with path.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except (json.JSONDecodeError, OSError):
            return []

        messages: List[ChatMessage] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            author = item.get("author")
            content = item.get("content")
            if isinstance(author, str) and isinstance(content, str):
                messages.append(ChatMessage(author, content))
        return messages

    def save(self, user_id: str, messages: List[ChatMessage]) -> Path:
        path = self._path_for_user(user_id)
        data = [{"author": message.author, "content": message.content} for message in messages]
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with path.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
        return path

    def clear(self, user_id: str) -> None:
        path = self._path_for_user(user_id)
        if path.exists():
            with self._lock:
                try:
                    path.unlink()
                except OSError:
                    pass

    def export_markdown(self, user_id: str, messages: List[ChatMessage]) -> Path:
        export_path = self._path_for_user(user_id).with_suffix(".md")
        export_path.parent.mkdir(parents=True, exist_ok=True)
        body = [f"**{message.author}:** {message.content}\n" for message in messages]
        with self._lock:
            with export_path.open("w", encoding="utf-8") as fh:
                fh.write("\n".join(body))
        return export_path

    def _path_for_user(self, user_id: str) -> Path:
        safe_id = "".join(ch if ch.isalnum() or ch in {"_", "-", "@", "."} else "_" for ch in user_id)
        return self._storage_dir / f"{safe_id}.json"
