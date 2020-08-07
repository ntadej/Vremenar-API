"""Helper utilities."""


def join_url(*args: str, trailing_slash: bool = False) -> str:
    """Join url."""
    url = '/'.join(arg.strip('/') for arg in args)
    if trailing_slash:
        return f'{url}/'
    return url
