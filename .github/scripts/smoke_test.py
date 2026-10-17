"""Runtime smoke test: build every major screen with the pinned Flet version."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import flet as ft
import main


class _Task:
    def done(self):
        return False

    def cancel(self):
        return None


class _Page:
    def __init__(self):
        self.controls = []
        self.snack_bar = None

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self):
        return None

    def run_task(self, coroutine):
        # Keep the smoke test deterministic; the timer itself is not needed.
        coroutine.close()
        return _Task()


def _walk(control):
    if control is None or isinstance(control, (str, int, float, bool)):
        return
    if isinstance(control, (list, tuple)):
        for child in control:
            yield from _walk(child)
        return
    yield control
    content = getattr(control, "content", None)
    if content is not None and not isinstance(content, (str, int, float, bool)):
        yield from _walk(content)
    controls = getattr(control, "controls", None)
    if controls:
        for child in controls:
            yield from _walk(child)


def _click_button(page, label):
    for control in _walk(page.controls):
        if isinstance(control, ft.Button) and control.content == label:
            if not callable(control.on_click):
                raise AssertionError(f"Button {label!r} has no callable click handler")
            control.on_click(None)
            return
    raise AssertionError(f"Could not find button {label!r}")


def main_smoke_test():
    page = _Page()
    main.main(page)  # Construct home screen.
    assert page.controls, "Home screen was not rendered"

    _click_button(page, "شروع بازی")  # Construct game screen.
    _click_button(page, "تسلیم شدن")  # Construct result screen.
    _click_button(page, "بازگشت به خانه")
    print(f"Flet {getattr(ft, '__version__', 'unknown')}: home/game/result screens passed")


if __name__ == "__main__":
    main_smoke_test()
