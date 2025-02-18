class BaseUrl:
    def __init__(self, domain: str, relative_path: str = '', path_validation: bool = True):
        self.domain = domain
        self.relative_path = relative_path
        self.path_validation = path_validation

    def get_absolute_url(self):
        return f"{self.domain}{self.relative_path}"
