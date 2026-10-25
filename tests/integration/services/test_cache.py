from project.services import cache


def test_clear_images_clears_the_image_cache_dir(app, mocker):
    clear = mocker.patch("project.services.cache.clear_files_in_dir")

    with app.app_context():
        cache.clear_images()

    clear.assert_called_once_with(cache.img_path)
