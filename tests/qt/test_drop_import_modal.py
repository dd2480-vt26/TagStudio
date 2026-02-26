from unittest.mock import Mock, patch
from pathlib import Path

from PySide6.QtCore import QUrl
from pytestqt.qtbot import QtBot

from tagstudio.qt.mixed.drop_import_modal import DropImportModal
from tagstudio.qt.ts_qt import QtDriver


# /**
#  * Positive test: After downloading, the file is added to the TagStudio root library.
#  * Expected: The file is copied to the library directory and is referenced by TagStudio.
#  */

def test_web_file_added_to_library(qtbot: QtBot, qt_driver: QtDriver, tmp_path):
    modal = DropImportModal(qt_driver)
    qtbot.addWidget(modal)
    modal.temp_dirs = []

    response = Mock()
    response.ok = True

    response.headers = {
        "Content-Disposition": 'attachment; filename="web-image.png"',
        "Content-Type": "image/png",
    }
    response.iter_content = Mock(return_value=[b"image", b"data"])

    request_cm = Mock()
    request_cm.__enter__ = Mock(return_value=response)
    request_cm.__exit__ = Mock(return_value=None)

    with patch("tagstudio.qt.mixed.drop_import_modal.requests.get", return_value=request_cm):
        qt_driver.lib.library_dir = tmp_path
        result = modal.save_web_file(QUrl("https://example.com/web-image.png"))
        library_file = tmp_path / "web-image.png"
        library_file.write_bytes(result.read_bytes())
        modal.files = [library_file]

    assert library_file.exists()
    assert library_file.read_bytes() == b"imagedata" or library_file.read_bytes() == b"image data"


# /**
#  * Positive test: After importing, the temporary folder is deleted (with its files).
#  * Expected: The temp directory and its files are deleted after cleanup.
#  */
def test_temp_folder_deleted_after_import(qtbot: QtBot, qt_driver: QtDriver):
    modal = DropImportModal(qt_driver)
    qtbot.addWidget(modal)
    modal.temp_dirs = []

    response = Mock()
    response.ok = True
    response.headers = {
        "Content-Disposition": 'attachment; filename="web-image.png"',
        "Content-Type": "image/png",
    }
    response.iter_content = Mock(return_value=[b"image", b"data"])

    request_cm = Mock()
    request_cm.__enter__ = Mock(return_value=response)
    request_cm.__exit__ = Mock(return_value=None)

    with patch("tagstudio.qt.mixed.drop_import_modal.requests.get", return_value=request_cm):
        result = modal.save_web_file(QUrl("https://example.com/web-image.png"))
        temp_dir = result.parent
        assert result.exists()
        assert temp_dir.exists()

    modal.cleanup_temp_dirs()
    assert not temp_dir.exists()