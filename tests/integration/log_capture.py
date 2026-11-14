import logging
from contextlib import contextmanager


class CollectingHandler(logging.Handler):
    """Keeps the lines as the JSON formatter of production renders them."""

    def __init__(self):
        from project.infrastructure.logging_config import build_formatter

        super().__init__()
        self.setFormatter(build_formatter("json"))
        self.lines = []

    def emit(self, record):
        self.lines.append(self.format(record))


@contextmanager
def collect_lines(logger_name: str):
    handler = CollectingHandler()
    logger = logging.getLogger(logger_name)
    logger.addHandler(handler)
    try:
        yield handler.lines
    finally:
        logger.removeHandler(handler)
