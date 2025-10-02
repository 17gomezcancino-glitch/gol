from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from input_controller import InputController


class DummyPyAutoGUI:
    def __init__(self):
        self.moves = []
        self.clicks = []
        self.typed = []

    def moveRel(self, x, y, duration=0):
        self.moves.append((x, y, duration))

    def click(self, button="left"):
        self.clicks.append(button)

    def typewrite(self, text):
        self.typed.append(text)


def test_move_pointer_scales_with_sensitivity():
    dummy = DummyPyAutoGUI()
    controller = InputController(sensitivity=2.0, controller=dummy)

    controller.move_pointer(3, -4)

    assert dummy.moves == [(6.0, -8.0, 0)]


def test_click_and_typing_delegate_to_controller():
    dummy = DummyPyAutoGUI()
    controller = InputController(controller=dummy)

    controller.click("right")
    controller.type_text("hola")

    assert dummy.clicks == ["right"]
    assert dummy.typed == ["hola"]


def test_unavailable_controller_noops():
    controller = InputController(controller=None)

    controller.move_pointer(1, 1)
    controller.click()
    controller.type_text("test")

    assert controller.available is False
