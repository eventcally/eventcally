from flask import current_app

from project.shared.paths import img_path
from project.shared.utils import clear_files_in_dir


def clear_images():
    current_app.logger.info("Clearing images..")
    clear_files_in_dir(img_path)
    current_app.logger.info("Done.")
