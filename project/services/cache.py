from project import app, img_path
from project.utils import clear_files_in_dir


def clear_images():
    app.logger.info("Clearing images..")
    clear_files_in_dir(img_path)
    app.logger.info("Done.")
