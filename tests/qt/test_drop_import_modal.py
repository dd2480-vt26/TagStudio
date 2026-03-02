from unittest.mock import Mock, patch

from PySide6.QtCore import QUrl
from pytestqt.qtbot import QtBot

from tagstudio.qt.mixed.drop_import_modal import DropImportModal
from tagstudio.qt.ts_qt import QtDriver


def test_web_file_added_to_library(qtbot: QtBot, qt_driver: QtDriver):
    """
    After importing a web file, it should be copied to the library directory with correct content.
    """
    modal = DropImportModal(qt_driver)
    qtbot.addWidget(modal)

    # Simulate a HTTP response
    fake_response = Mock()
    fake_response.ok = True
    fake_response.headers = {
        "Content-Disposition": 'attachment; filename="test_image.png"',
        "Content-Type": "image/png",
    }
    fake_response.iter_content = Mock(return_value=[b"fake_image_data"])

    request_cm = Mock()
    request_cm.__enter__ = Mock(return_value=fake_response)
    request_cm.__exit__ = Mock(return_value=None)

    # Patch requests.get in order to return our fake response
    # Patch from_iterable_function in order to avoid the UI and directly execute copy_files
    with (
        patch("requests.get", return_value=request_cm),
        patch(
            "tagstudio.qt.mixed.drop_import_modal.ProgressWidget.from_iterable_function"
        ) as mock_pw,
    ):
        # Exhaust the generator immediately
        mock_pw.side_effect = lambda copy_files, *args, **kwargs: list(copy_files())

        modal.import_urls([QUrl("https://example.com/test_image.png")])

    modal.cleanup_temp_dirs()

    library_file = qt_driver.lib.library_dir / "test_image.png"
    assert library_file.exists(), "File has not been copied to the library directory"
    assert library_file.read_bytes() == b"fake_image_data", (
        "File content does not match downloaded data"
    )


def test_temp_folder_deleted_after_import(qtbot: QtBot, qt_driver: QtDriver):
    """
    Temp directory (and its file) created during web file download
    is cleaned up after cleanup_temp_dirs().
    """
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
