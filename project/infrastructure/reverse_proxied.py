class ReverseProxied(object):
    def __init__(self, app, preferred_url_scheme):
        self.app = app
        self.preferred_url_scheme = preferred_url_scheme

    def __call__(self, environ, start_response):
        # if one of x_forwarded or preferred_url is https, prefer it.
        forwarded_scheme = environ.get("HTTP_X_FORWARDED_PROTO", None)
        preferred_scheme = self.preferred_url_scheme
        if "https" in [forwarded_scheme, preferred_scheme]:  # pragma: no cover
            environ["wsgi.url_scheme"] = "https"
        return self.app(environ, start_response)
