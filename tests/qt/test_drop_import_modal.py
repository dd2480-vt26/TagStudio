from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QUrl
from pytestqt.qtbot import QtBot

from tagstudio.qt.mixed.drop_import_modal import DropImportModal
from tagstudio.qt.ts_qt import QtDriver


@pytest.mark.parametrize(
    "url, status_code",
    [
        ("https://fakeurl.com/image.jpg", 404),
        ("https://fakeurl.com/file.png", 500),
    ],
)
def test_save_web_file_failed_download_returns_none(
    qtbot: QtBot, qt_driver: QtDriver, url, status_code
):
    """
    DropImportModal.save_web_file() should return None
    when the download fails (e.g. when response.ok is False)
    """
    fake_response = MagicMock()
    fake_response.ok = False
    fake_response.status_code = status_code

    modal = DropImportModal(qt_driver)
    qtbot.addWidget(modal)

    with patch("tagstudio.qt.mixed.drop_import_modal.requests.get") as mock_get:
        mock_get.return_value.__enter__.return_value = fake_response
        result = modal.save_web_file(QUrl(url))

    assert result is None
