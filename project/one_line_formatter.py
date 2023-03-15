import logging


class OneLineFormatter(logging.Formatter):
    def format(self, record):  # pragma: no cover
        result = super(OneLineFormatter, self).format(record)
        return result.replace("\n", "\\n")


def init_logger_with_one_line_formatter(logger):
    if not logger:  # pragma: no cover
        return

    for handler in logger.handlers:
        if handler.formatter:
            fmt = handler.formatter._fmt

            if fmt:
                fmt = fmt.replace(" %(levelname)s", " [%(levelname)s]")

            handler.formatter = OneLineFormatter(fmt, handler.formatter.datefmt)
        else:  # pragma: no cover
            handler.formatter = OneLineFormatter()
