from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from chat_models import ChatMessage
from conversation_history import ConversationHistory


def test_load_returns_empty_for_missing_file(tmp_path: Path) -> None:
    history = ConversationHistory(tmp_path)
    assert history.load("user") == []


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    history = ConversationHistory(tmp_path)
    messages = [ChatMessage("Usuario", "Hola"), ChatMessage("Agente", "Hola, ¿qué tal?")]
    history.save("user", messages)

    reloaded = history.load("user")
    assert reloaded == messages


def test_export_markdown(tmp_path: Path) -> None:
    history = ConversationHistory(tmp_path)
    messages = [ChatMessage("Usuario", "Mensaje"), ChatMessage("Agente", "Respuesta")]
    export_path = history.export_markdown("user", messages)

    assert export_path.exists()
    content = export_path.read_text(encoding="utf-8")
    assert "**Usuario:** Mensaje" in content
    assert "**Agente:** Respuesta" in content


def test_clear_removes_history_file(tmp_path: Path) -> None:
    history = ConversationHistory(tmp_path)
    messages = [ChatMessage("Usuario", "Mensaje")]
    path = history.save("user", messages)
    assert path.exists()

    history.clear("user")
    assert not path.exists()
