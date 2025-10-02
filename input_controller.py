"""Abstractions for optional OS-level input control used by the communication app."""

from __future__ import annotations

from typing import Optional

try:  # pragma: no-cover - optional dependency
    import pyautogui

    pyautogui.FAILSAFE = False
except Exception:  # pragma: no-cover - optional dependency
    pyautogui = None  # type: ignore


class InputController:
    """Wrapper around optional OS-level input control helpers."""

    def __init__(self, sensitivity: float = 1.0, controller: Optional[object] = None) -> None:
        self._controller = controller if controller is not None else pyautogui
        self._available = self._controller is not None
        self._sensitivity = sensitivity

    @property
    def available(self) -> bool:
        return self._available

    @property
    def sensitivity(self) -> float:
        return self._sensitivity

    def update_sensitivity(self, value: float) -> None:
        self._sensitivity = max(0.1, value)

    def move_pointer(self, delta_x: float, delta_y: float) -> None:
        if not self._available:
            return
        self._controller.moveRel(delta_x * self._sensitivity, delta_y * self._sensitivity, duration=0)

    def click(self, button: str = "left") -> None:
        if not self._available:
            return
        self._controller.click(button=button)

    def type_text(self, text: str) -> None:
        if not self._available:
            return
        self._controller.typewrite(text)
