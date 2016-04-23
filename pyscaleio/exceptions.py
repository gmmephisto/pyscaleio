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


class ScaleIOInvalidClient(Error):
    def __init__(self):
        super(ScaleIOInvalidClient, self).__init__("Invalid ScaleIO client instance.")


class ScaleIOClientAlreadyRegistered(Error):
    def __init__(self, key):
        super(ScaleIOClientAlreadyRegistered, self).__init__(
            "ScaleIOClient with key '{0}' already registered.", key)


class ScaleIOClientNotRegistered(Error):
    def __init__(self, key):
        super(ScaleIOClientNotRegistered, self).__init__(
            "ScaleIOClient with key '{0}' not registered.", key)


class ScaleIOEmptyClientRegistry(Error):
    def __init__(self):
        super(ScaleIOEmptyClientRegistry, self).__init__(
            "Clients for ScaleIO not registered.")


class ScaleIOValidationError(Error):
    def __init__(self, exc):
        super(ScaleIOValidationError, self).__init__(
            "Resource validation error: {0}", exc)


class ScaleIOConfigError(Error):
    def __init__(self, exc):
        super(ScaleIOConfigError, self).__init__(
            "Config validation error: {0}", exc)


class ScaleIOInvalidParameters(Error):
    def __init__(self, *args, **kwargs):
        super(ScaleIOInvalidParameters, self).__init__(*args, **kwargs)


class ScaleIONotBothParameters(ScaleIOInvalidParameters):
    def __init__(self, first, second):
        super(ScaleIONotBothParameters, self).__init__(
            "Use either '{0}' or '{1}', not both", first, second)
