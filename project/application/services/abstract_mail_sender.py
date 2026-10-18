import abc


class AbstractMailSender(abc.ABC):
    @abc.abstractmethod
    def send_mails_with_body(self, recipients, subject, body, html):  # pragma: no cover
        raise NotImplementedError
