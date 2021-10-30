class ScihubUnavailable(Exception):
    """
    Exception is called when Sci-Hub is unavailable
    """
    pass


class CrossrefUnavailable(Exception):
    """
    Exception is called when crossref.org API is unavailable
    """
    pass


class DoiNotFound(Exception):
    """
    Exception is called when Doi couldn't be found on crossref.org
    """
    pass

