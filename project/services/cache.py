from flask import current_app

from project import img_path
from project.utils import clear_files_in_dir


def clear_images():
    current_app.logger.info("Clearing images..")
    clear_files_in_dir(img_path)
    current_app.logger.info("Done.")
