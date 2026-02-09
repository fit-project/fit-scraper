#!/usr/bin/env python3
# -*- coding:utf-8 -*-
######
# -----
# Copyright (c) 2023 FIT-Project
# SPDX-License-Identifier: LGPL-3.0-or-later
# -----
######

import logging
import os
import sys

from fit_acquisition.class_names import class_names
from fit_acquisition.logger_names import LoggerName
from fit_common.core import AcquisitionType, debug
from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QApplication

from fit_scraper.scraper import Scraper


class TestScraper(Scraper):
    def __init__(self, wizard=None):
        logger = logging.getLogger(LoggerName.SCRAPER_WEB.value)
        packages = []
        super().__init__(logger, AcquisitionType.WEB, packages, wizard)

        self.acquisition.start_tasks = [
            class_names.SCREENRECORDER,
            class_names.PACKETCAPTURE,
        ]
        self.acquisition.stop_tasks = [
            class_names.WHOIS,
            class_names.NSLOOKUP,
            class_names.HEADERS,
            class_names.SSLKEYLOG,
            class_names.SSLCERTIFICATE,
            class_names.TRACEROUTE,
            class_names.SCREENRECORDER,
            class_names.PACKETCAPTURE,
        ]
        self.__init_execution_overlay()

    def __init_execution_overlay(self):
        self.setWindowTitle("Test Scraper Window")
        self.setMinimumSize(800, 600)

        label = QtWidgets.QLabel("Questa è una finestra base di test.", self)
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.addWidget(label)

        self.acquisition.progress_bar = QtWidgets.QProgressBar()
        self.acquisition.status_bar = QtWidgets.QLabel()

        self.start_btn = QtWidgets.QPushButton("Start")
        self.stop_btn = QtWidgets.QPushButton("Stop")

        layout.addWidget(self.acquisition.progress_bar)
        layout.addWidget(self.acquisition.status_bar)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)

        self.start_btn.clicked.connect(self.execute_start_tasks_flow)
        self.stop_btn.clicked.connect(self.execute_stop_tasks_flow)

        self.setCentralWidget(central_widget)

        self._reset_acquisition_indicators(False)

    def execute_start_tasks_flow(self):
        if self.create_acquisition_directory():
            if self.create_acquisition_subdirectory("screenshot"):
                acquisition_page = os.path.join(
                    self.acquisition_directory, "acquisition_page"
                )
                os.makedirs(acquisition_page, exist_ok=True)
                self.acquisition.options = {
                    "acquisition_directory": self.acquisition_directory,
                    "screenshot_directory": os.path.join(
                        self.acquisition_directory, "screenshot"
                    ),
                    "current_widget": self,
                    "window_pos": self.centralWidget().pos(),
                    "url": "http://google.it",
                    "type": "web",
                    "case_info": self.case_info,
                    "pdf_filename": "acquisition_report.pdf",
                }

                return super().execute_start_tasks_flow()

    def execute_stop_tasks_flow(self):
        return super().execute_stop_tasks_flow()

    def on_start_tasks_finished(self):
        debug(
            "ℹ️ finito di eseguire tutti i task della lista di Acquisition start_tasks",
            context="main.fit_scraper",
        )
        return super().on_start_tasks_finished()

    def on_stop_tasks_finished(self):
        self.acquisition.start_post_acquisition()
        debug(
            "ℹ️ finito di eseguire tutti i task della lista di Acquisition  stop_tasks",
            context="main.fit_scraper",
        )

    def on_post_acquisition_finished(self):
        debug(
            "ℹ️ finito di eseguire tutti i task della lista di Acquisition post_tasks",
            context="main.fit_scraper",
        )
        return super().on_post_acquisition_finished()


def main():
    app = QApplication(sys.argv)
    window = TestScraper()

    if window.has_valid_case:
        window.show()
        sys.exit(app.exec())
    else:
        debug(
            "❌ User cancelled the case form. Nothing to display.",
            context="main.fit_scraper",
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
