# !/usr/bin/env python3
# -*- coding:utf-8 -*-
######
# -----
# Copyright (c) 2023 FIT-Project
# SPDX-License-Identifier: LGPL-3.0-or-later
# -----
######

import os
import re
import stat

from fit_acquisition.acquisition import Acquisition, AcquisitionStatus
from fit_acquisition.tasks.tasks_info import TasksInfo
from fit_cases.utils import show_case_info_dialog
from fit_cases.view.case_form_dialog import CaseFormDialog
from fit_common.core.utils import get_version
from fit_common.gui.error import Error
from fit_common.gui.utils import show_finish_acquisition_dialog
from fit_configurations.controller.tabs.general.general import GeneralController
from fit_configurations.utils import show_configuration_dialog
from fit_scraper.lang import load_scraper_translations
from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QMovie


class Scraper(QtWidgets.QMainWindow):

    def __init__(self, logger, acquisition_type, packages, wizard=None):
        super().__init__()

        self.__acquisition_status = AcquisitionStatus.UNSTARTED
        self.__acquisition_type = acquisition_type
        self.__has_valid_case = True
        self.__case_info = None
        self.__acquisition_directory = None
        self.__tasks_info = None

        self.__wizard = wizard

        self.scraper_translations = load_scraper_translations()

        if self.__wizard is not None:
            self.__case_info = self.__wizard.case_info
        else:
            dialog = CaseFormDialog()
            dialog.ui.save_button.setText("Start")
            result = dialog.exec()
            if result == QtWidgets.QDialog.Accepted:
                self.__case_info = dialog.get_case_info()
            else:
                error_dlg = Error(
                    QtWidgets.QMessageBox.Icon.Critical,
                    self.scraper_translations["NO_CASE_SELECTED_TITLE"],
                    self.scraper_translations["NO_CASE_SELECTED_MESSAGE"],
                    "",
                )
                error_dlg.exec()
                self.__has_valid_case = False
                return

        self.__acquisition = Acquisition(logger=logger, packages=packages)
        self.__acquisition.start_tasks_finished.connect(self.on_start_tasks_finished)
        self.__acquisition.stop_tasks_finished.connect(self.on_stop_tasks_finished)
        self.__acquisition.post_acquisition_finished.connect(
            self.on_post_acquisition_finished
        )

    @property
    def acquisition_status(self):
        return self.__acquisition_status

    @acquisition_status.setter
    def acquisition_status(self, value):
        self.__acquisition_status = value

    @property
    def acquisition_type(self):
        return self.__acquisition_type

    @acquisition_type.setter
    def acquisition_type(self, value):
        self.__acquisition_type = value

    @property
    def has_valid_case(self):
        return self.__has_valid_case

    @property
    def acquisition(self):
        return self.__acquisition

    @property
    def case_info(self):
        return self.__case_info

    @property
    def acquisition_directory(self):
        return self.__acquisition_directory

    def create_acquisition_directory(self) -> bool:
        try:
            # Folder Cases
            cases_folder = os.path.expanduser(
                GeneralController().configuration["cases_folder_path"]
            )
            if not os.path.exists(cases_folder):
                os.makedirs(cases_folder)
                os.chmod(cases_folder, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

            # Folder Case
            case_folder = os.path.join(cases_folder, self.__case_info["name"])
            if not os.path.exists(case_folder):
                os.makedirs(case_folder)
                os.chmod(case_folder, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

            # Folder Type
            acquisition_type_folder = os.path.join(case_folder, self.__acquisition_type)
            if not os.path.exists(acquisition_type_folder):
                os.makedirs(acquisition_type_folder)
                os.chmod(
                    acquisition_type_folder, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
                )

            self.__acquisition_directory = os.path.join(
                acquisition_type_folder, "acquisition_1"
            )

            if os.path.isdir(self.__acquisition_directory):
                acquisition_directories = [
                    d
                    for d in os.listdir(acquisition_type_folder)
                    if os.path.isdir(os.path.join(acquisition_type_folder, d))
                ]

                acquisition_directories = list(
                    filter(
                        lambda item: bool(re.search(r"^acquisition_(\d+)$", item)),
                        acquisition_directories,
                    )
                )

                index = max(
                    [
                        int("".join(filter(str.isdigit, item)))
                        for item in acquisition_directories
                    ],
                    default=0,
                )

                self.__acquisition_directory = os.path.join(
                    acquisition_type_folder, f"acquisition_{index + 1}"
                )

            os.makedirs(self.__acquisition_directory, exist_ok=True)
            return True

        except Exception as e:
            error = Error(
                QtWidgets.QMessageBox.Icon.Critical,
                self.scraper_translations["CREATE_DIRECTORY_ERROR_TITLE"],
                self.scraper_translations["CREATE_ACQUISITION_DIRECTORY_ERROR_MESSAGE"],
                str(e),
            )
            error.exec()
            self.__acquisition_directory = None
            return False

    def create_acquisition_subdirectory(self, sub_path: str) -> bool:
        try:
            if not self.__acquisition_directory:
                raise ValueError(
                    self.scraper_translations["ACQUISITION_DIRECTORY_DOES_NOT_EXIST"]
                )

            full_path = os.path.join(self.__acquisition_directory, sub_path)
            os.makedirs(full_path, exist_ok=True)
            os.chmod(full_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            return True

        except Exception as e:
            error = Error(
                QtWidgets.QMessageBox.Icon.Critical,
                self.scraper_translations["CREATE_DIRECTORY_ERROR_TITLE"],
                self.scraper_translations[
                    "CREATE_ACQUISITION_SUBDIRECTORY_ERROR_MESSAGE"
                ].format(sub_path),
                str(e),
            )
            error.exec()
            return False

    def execute_start_tasks_flow(self):
        self.__acquisition_status = AcquisitionStatus.STARTED
        self._reset_acquisition_indicators(True)
        self.__acquisition.load_tasks()
        self.__init_execution_overlay()
        self.__spinner_overlay.show()
        self.__movie_spinner.start()
        loop = QtCore.QEventLoop()
        QtCore.QTimer.singleShot(1000, loop.quit)
        loop.exec()
        self.__acquisition.log_start_message()
        self.__acquisition.run_start_tasks()

    def on_start_tasks_finished(self):
        loop = QtCore.QEventLoop()
        QtCore.QTimer.singleShot(2000, loop.quit)
        loop.exec()
        self.__movie_spinner.stop()
        self.__spinner_overlay.hide()
        self.__acquisition.progress_bar.setValue(100)
        self._reset_acquisition_indicators(False)

    def execute_stop_tasks_flow(self):
        self.__acquisition_status = AcquisitionStatus.STOPPED
        self._reset_acquisition_indicators(True)
        self.__tasks_info.show()
        loop = QtCore.QEventLoop()
        QtCore.QTimer.singleShot(1000, loop.quit)
        loop.exec()
        self.__acquisition.log_stop_message()
        self.__acquisition.run_stop_tasks()

    def on_stop_tasks_finished(self):
        loop = QtCore.QEventLoop()
        QtCore.QTimer.singleShot(2000, loop.quit)
        loop.exec()
        self._reset_acquisition_indicators(True)
        self.execute_post_acquisition_tasks_flow()

    def execute_post_acquisition_tasks_flow(self):
        self.__acquisition.start_post_acquisition()

    def on_post_acquisition_finished(self):
        self.__acquisition_status = AcquisitionStatus.FINISHED
        QtCore.QTimer.singleShot(3000, self.__tasks_info.close)
        self.__acquisition.log_end_message()
        self.__acquisition.set_completed_progress_bar()
        self.__acquisition.unload_tasks()
        self._reset_acquisition_indicators(False)
        self.finish_acquisition()

    def on_resize(self, event):
        self.__spinner_overlay.setGeometry(self.rect())
        self.__tasks_info.setGeometry(self.rect())
        super().resizeEvent(event)

    def finish_acquisition(self):
        show_finish_acquisition_dialog(self.__acquisition_directory)

    def configuration_dialog(self):
        show_configuration_dialog()

    def show_case_info(self):
        show_case_info_dialog(self.__case_info)

    def mousePressEvent(self, event):
        self.dragPos = event.globalPosition().toPoint()

    def move_window(self, event):
        if event.buttons() == QtCore.Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self.dragPos)
            self.dragPos = event.globalPosition().toPoint()
            event.accept()

    def _reset_acquisition_indicators(self, visible: bool):
        self.__acquisition.progress_bar_visible = visible
        self.__acquisition.status_bar_visible = visible
        self.__acquisition.reset_progress_bar
        self.__acquisition.reset_status_bar

    def _get_version(self):
        return get_version()

    def __init_execution_overlay(self):

        self.resizeEvent = self.on_resize

        self.__tasks_info = TasksInfo(parent=self)
        self.__tasks_info.setWindowFlags(QtCore.Qt.WindowType.Widget)
        self.__tasks_info.setAutoFillBackground(True)
        self.__tasks_info.setGeometry(self.rect())
        self.__tasks_info.hide()
        self.__tasks_info.raise_()

        self.__spinner_overlay = QtWidgets.QLabel(self)
        self.__spinner_overlay.setAlignment(QtCore.Qt.AlignCenter)
        self.__spinner_overlay.setStyleSheet(
            "background-color: rgba(255, 255, 255, 180);"
        )

        self.__spinner_overlay.setGeometry(self.rect())
        self.__spinner_overlay.hide()

        self.__movie_spinner = QMovie(":/images/images/spinner.gif")
        self.__spinner_overlay.setMovie(self.__movie_spinner)

    def __can_close(self) -> bool:
        if self.acquisition_status in (
            AcquisitionStatus.UNSTARTED,
            AcquisitionStatus.FINISHED,
        ):
            return True

        Error(
            QtWidgets.QMessageBox.Icon.Warning,
            self.scraper_translations["ACQUISITION_IS_RUNNING"],
            self.scraper_translations["WAR_ACQUISITION_IS_RUNNING"],
            "",
        ).exec()
        return False

    def __back_to_wizard(self):
        if self.__can_close():
            self.deleteLater()
            self.__wizard.reload_case_info()
            self.__wizard.show()

    def closeEvent(self, event):
        if self.__wizard is not None:
            event.ignore()
            self.__back_to_wizard()
        elif self.__can_close():
            event.accept()
        else:
            event.ignore()
