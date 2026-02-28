import abc
from itertools import groupby

from flask import render_template
from flask_babel import force_locale, gettext


class AbstractEmailService(abc.ABC):
    def __init__(self, default_locale):
        self.default_locale = default_locale

    def send_template_mails_to_users_async(self, users, template, **context):
        if len(users) == 0:  # pragma: no cover
            return

        # Group by locale
        def locale_func(user):
            return user.locale if user.locale else ""

        sorted_users = sorted(users, key=locale_func)
        grouped_users = groupby(sorted_users, locale_func)

        signatures = list()

        for locale, locale_users in grouped_users:
            context["locale"] = locale
            subject, body, html = self._render_mail_body_with_subject(
                template, **context
            )
            signatures.extend(
                [(user.email, subject, body, html) for user in locale_users]
            )

        return self.send_mails_with_signatures_async(signatures)

    def _render_mail_body_with_subject(self, template, **context):
        from project.views.utils import mail_template_subject_mapping

        subject_key = mail_template_subject_mapping.get(template)
        locale = context.get("locale", None) or self.default_locale

        with force_locale(locale):
            subject = gettext(subject_key, **context)
            body, html = self._render_mail_body(template, **context)

        return subject, body, html

    def _render_mail_body(self, template, **context):
        body = render_template("email/%s.txt" % template, **context)
        html = render_template("email/%s.html" % template, **context)
        return body, html

    @abc.abstractmethod
    def send_mails_with_signatures_async(self, signatures):  # pragma: no cover
        raise NotImplementedError
