import logging

from project.shared.paths import img_path
from project.shared.utils import clear_files_in_dir

logger = logging.getLogger(__name__)


def clear_images():
    logger.info("Clearing images")
    clear_files_in_dir(img_path)
    logger.info("Cleared images")
