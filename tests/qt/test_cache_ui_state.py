from typing import Any
from unittest.mock import Mock

from tagstudio.core.enums import SettingItems
from tagstudio.core.library.alchemy.enums import SortingModeEnum
from tagstudio.qt.ts_qt import QtDriver


# Helper: pick a deterministic default sorting mode for tests.
def first_sorting_mode() -> SortingModeEnum:
    return list(SortingModeEnum)[0]


# Helper: pick a different valid mode (or fall back) to test cache override behavior.
def second_sorting_mode() -> SortingModeEnum:
    modes = list(SortingModeEnum)
    return modes[1] if len(modes) > 1 else modes[0]


# Helper: build the minimal QtDriver mock needed by init_library_window so each
# test only provides cache inputs and expected combobox lookup results.
def make_driver_for_init_window(
    cached_values: dict[SettingItems, Any] | None = None,
    *,
    default_sorting_mode: SortingModeEnum | None = None,
    default_sorting_direction: bool = True,
    sorting_direction_index: int = 0,
    thumbnail_index: int = -1,
) -> Mock:
    driver = Mock(spec=QtDriver)

    cache = cached_values or {}
    driver.cached_values = Mock()
    driver.cached_values.value = Mock(side_effect=lambda key, type=None: cache.get(key))

    driver.browsing_history = Mock()
    driver.browsing_history.current = Mock()
    driver.browsing_history.current.sorting_mode = default_sorting_mode or first_sorting_mode()
    driver.browsing_history.current.ascending = default_sorting_direction

    driver.main_window = Mock()
    driver.main_window.search_button.clicked.connect = Mock()
    driver.main_window.search_field.returnPressed.connect = Mock()

    driver.main_window.sorting_mode_combobox.currentIndexChanged.connect = Mock()
    driver.main_window.sorting_direction_combobox.findData = Mock(
        return_value=sorting_direction_index
    )
    driver.main_window.sorting_direction_combobox.currentIndexChanged.connect = Mock()

    driver.main_window.thumb_size = 128
    driver.main_window.thumb_size_combobox.findData = Mock(return_value=thumbnail_index)
    driver.main_window.thumb_size_combobox.currentIndex = Mock(return_value=2)
    driver.main_window.thumb_size_combobox.currentIndexChanged.connect = Mock()

    driver.main_window.show_hidden_entries_checkbox.stateChanged.connect = Mock()
    driver.main_window.back_button.clicked.connect = Mock()
    driver.main_window.forward_button.clicked.connect = Mock()
    driver.main_window.pagination.index.connect = Mock()

    driver.main_window.content_splitter = Mock()
    driver.main_window.content_splitter.setSizes = Mock()

    driver.splash = Mock()
    driver.thumb_size_callback = Mock()
    driver.show_hidden_entries_callback = Mock()
    driver.navigation_callback = Mock()
    driver.page_move = Mock()
    driver.update_browsing_state = Mock()

    return driver


# /**
#  * Positive test: cache_ui_state should store sorting options when the application closes.
#  * cache_ui_state should save SORTING_MODE and SORTING_DIRECTION into cached values.
#  * Test case: Mock driver with sorting mode set and sorting direction set to True.
#  * Expected: Sorting mode and sorting direction are saved.
#  */
def test_cache_ui_state_stores_sorting_options():
    driver = Mock(spec=QtDriver)
    driver.main_window = Mock()
    driver.main_window.sorting_mode = first_sorting_mode()
    driver.main_window.sorting_direction = True
    driver.main_window.width.return_value = 800
    driver.main_window.height.return_value = 600
    driver.main_window.preview_panel.width.return_value = 200
    driver.main_window.thumb_size = 128
    driver.cached_values = Mock()

    QtDriver.cache_ui_state(driver)

    driver.cached_values.setValue.assert_any_call(
        SettingItems.SORTING_MODE, driver.main_window.sorting_mode.value
    )
    driver.cached_values.setValue.assert_any_call(SettingItems.SORTING_DIRECTION, True)


# /**
#  * Positive test: init_library_window should restore saved sorting options on startup.
#  * init_library_window should apply cached sorting mode and sorting direction.
#  * Test case: Cache contains a valid second sorting mode and sorting direction=False.
#  * Expected: Saved sorting options are restored on startup.
#  */
def test_restore_sorting_options_from_cache():
    second_mode = second_sorting_mode()
    driver = make_driver_for_init_window(
        {
            SettingItems.SORTING_MODE: second_mode.value,
            SettingItems.SORTING_DIRECTION: False,
        },
        sorting_direction_index=1,
        thumbnail_index=0,
    )

    QtDriver.init_library_window(driver)

    driver.main_window.sorting_mode_combobox.setCurrentIndex.assert_called_once_with(
        list(SortingModeEnum).index(second_mode)
    )
    driver.main_window.sorting_direction_combobox.findData.assert_called_once_with(False)
    driver.main_window.sorting_direction_combobox.setCurrentIndex.assert_called_once_with(1)


# /**
#  * Negative test: init_library_window should use defaults when no cached UI values exist.
#  * init_library_window should fall back to default sorting and layout behavior.
#  * Test case: Cache returns no values for sorting options, thumbnail size, and sidebar width.
#  * Expected: Default settings are used when no saved values exist.
#  */
def test_no_cache_uses_defaults():
    default_mode = first_sorting_mode()
    driver = make_driver_for_init_window(
        {},
        default_sorting_mode=default_mode,
        default_sorting_direction=True,
        sorting_direction_index=0,
        thumbnail_index=-1,
    )

    QtDriver.init_library_window(driver)

    driver.main_window.sorting_mode_combobox.setCurrentIndex.assert_called_once_with(
        list(SortingModeEnum).index(default_mode)
    )
    driver.main_window.sorting_direction_combobox.findData.assert_called_once_with(True)
    driver.main_window.sorting_direction_combobox.setCurrentIndex.assert_called_once_with(0)
    driver.main_window.thumb_size_combobox.findData.assert_called_once_with(128)
    driver.main_window.thumb_size_combobox.setCurrentIndex.assert_any_call(2)
    driver.main_window.content_splitter.setSizes.assert_not_called()


# /**
#  * Negative test: init_library_window should use defaults when cached UI values are invalid.
#  * init_library_window should ignore invalid sorting and sizing values from cache.
#  * Test case: Cache contains invalid sorting mode, invalid sorting direction, and negative size values.
#  * Expected: Invalid saved values are ignored and defaults are used.
#  */
def test_invalid_cache_uses_defaults():
    default_mode = first_sorting_mode()
    driver = make_driver_for_init_window(
        {
            SettingItems.SORTING_MODE: "INVALID_MODE",
            SettingItems.SORTING_DIRECTION: None,
            SettingItems.WINDOW_WIDTH: -1,
            SettingItems.WINDOW_HEIGHT: -1,
            SettingItems.SIDEBAR_WIDTH: -1,
            SettingItems.THUMB_SIZE: -1,
        },
        default_sorting_mode=default_mode,
        default_sorting_direction=True,
        sorting_direction_index=0,
        thumbnail_index=-1,
    )

    QtDriver.init_library_window(driver)

    driver.main_window.sorting_mode_combobox.setCurrentIndex.assert_called_once_with(
        list(SortingModeEnum).index(default_mode)
    )
    driver.main_window.sorting_direction_combobox.findData.assert_called_once_with(True)
    driver.main_window.sorting_direction_combobox.setCurrentIndex.assert_called_once_with(0)
    driver.main_window.thumb_size_combobox.findData.assert_called_once_with(-1)
    driver.main_window.thumb_size_combobox.setCurrentIndex.assert_any_call(2)
    driver.main_window.content_splitter.setSizes.assert_not_called()
