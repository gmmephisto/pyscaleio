from psys import Error


class ScaleIOError(Error):
    def __init__(self, code, message, error_code=None):
        super(ScaleIOError, self).__init__(
            "ScaleIOError: code={0}, message={1}", code, message
        )
        self.status_code = code
        self.error_code = error_code or 0


class ScaleIOAuthError(ScaleIOError):
    def __init__(self):
        super(ScaleIOAuthError, self).__init__(401, "Unauthorized")


class ScaleIOMalformedError(ScaleIOError):
    def __init__(self):
        super(ScaleIOMalformedError, self).__init__(500, "Malformed response")
