"""
Exports your list as XML from MAL using Selenium
"""

import os
import time
import shutil
import gzip
from typing import List

from selenium.webdriver.support.ui import WebDriverWait  # type: ignore[import]
from selenium.webdriver.common.by import By  # type: ignore[import]
from selenium.webdriver.support import expected_conditions as EC  # type: ignore[import]

from .driver import driver, driver_login, wait, TEMP_DOWNLOAD_DIR
from ..list_type import ListType
from ..paths import LocalDir
from ..log import logger

EXPORT_PAGE = "https://myanimelist.net/panel.php?go=export"
EXPORT_BUTTON_CSS = "input[value='Export My List']"
DOWNLOAD_BUTTON = ".goodresult>a"


class ExportDownloader:
    """
    Downloads the XML exports for your account
    """

    def __init__(self, localdir: LocalDir) -> None:
        self.localdir = localdir
        self.animelist_path = self.localdir.data_dir / "animelist.xml"
        self.mangalist_path = self.localdir.data_dir / "mangalist.xml"

    def authenticate(self) -> None:
        """Logs in to MAL using your MAL username/password"""
        driver_login(self.localdir)

    def export_lists(self) -> None:
        """Exports the anime/manga lists, then extracts the gz files into the data dir"""
        self.authenticate()
        self.export_list(ListType.ANIME)
        self.export_list(ListType.MANGA)
        self.extract_gz_files()

    def export_list(self, list_type: ListType) -> None:
        """
        Exports a particular list types' XML file, waits a while so that it can finish downloading
        The only difference between anime and manga is what is selected in the dialog
        """
        d = driver()
        time.sleep(1)
        logger.info(f"Downloading {list_type.value} export")
        d.get(EXPORT_PAGE)
        export_button_selector = tuple([By.CSS_SELECTOR, EXPORT_BUTTON_CSS])
        WebDriverWait(d, 10).until(
            EC.visibility_of_element_located(export_button_selector)
        )
        if list_type == ListType.MANGA:
            d.execute_script("""$("#dialog select.inputtext").val(2)""")
        d.find_element_by_css_selector(EXPORT_BUTTON_CSS).click()
        WebDriverWait(d, 10).until(EC.alert_is_present())
        alert = d.switch_to.alert
        alert.accept()
        download_button_selector = tuple([By.CSS_SELECTOR, DOWNLOAD_BUTTON])
        WebDriverWait(d, 10).until(EC.element_to_be_clickable(download_button_selector))
        d.find_element_by_css_selector(DOWNLOAD_BUTTON).click()
        logger.debug("Waiting for download...")
        wait()

    def _list_files(self, path: str = TEMP_DOWNLOAD_DIR) -> List[str]:
        """
        List files in the temporary download directory, warn if there
        are multiple files/partially downloaded files
        """
        files = os.listdir(path)
        animelist_gzs = [f for f in files if f.startswith("animelist_")]
        mangalist_gzs = [f for f in files if f.startswith("mangalist_")]
        for search_results in (animelist_gzs, mangalist_gzs):
            if len(search_results) != 1:
                logger.warning(f"Found more than 1 matching file {search_results}")
        archive_files = animelist_gzs + mangalist_gzs
        logger.debug(archive_files)
        return archive_files

    def extract_gz_files(self) -> None:
        """
        Wait till two files (the anime/manga gz files) exist in the temporary download
        directory, then extract them to the data directory
        """
        while len(self._list_files()) != 2:
            logger.info(
                f"Waiting till 2 list files exist, currently {os.listdir(TEMP_DOWNLOAD_DIR)}"
            )
            time.sleep(0.5)

        for (archive_name, target) in zip(
            self._list_files(), [self.animelist_path, self.mangalist_path]
        ):
            archive_path = os.path.join(TEMP_DOWNLOAD_DIR, archive_name)
            logger.info(f"Extracting {archive_path} to {target}")
            with gzip.open(archive_path, "rb") as gz_in:
                with target.open("wb") as f:
                    shutil.copyfileobj(gz_in, f)