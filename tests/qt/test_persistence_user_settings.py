import pytest
from unittest.mock import patch
from tagstudio.qt.ts_qt import QtDriver
from pytestqt.qtbot import QtBot
from tagstudio.qt.views.main_window import MainWindow
from tagstudio.core.enums import SettingItems


def test_window_size_is_saved_on_close(qtbot: QtBot, qt_driver: QtDriver):
    window = MainWindow(qt_driver)
    qtbot.addWidget(window)
    qt_driver.main_window = window

    new_width = 1600
    new_height = 900
    window.resize(new_width, new_height)

    with patch("tagstudio.qt.ts_qt.QApplication.quit"):
        qt_driver.shutdown()

    settings = qt_driver.cached_values
    cached_width = settings.value(SettingItems.WINDOW_WIDTH, type=int)
    cached_height = settings.value(SettingItems.WINDOW_HEIGHT, type=int)

    assert cached_width == new_width
    assert cached_height == new_height

    new_window = MainWindow(qt_driver)
    qtbot.addWidget(new_window)


    assert new_window.width() == new_width
    assert new_window.height() == new_height


    


