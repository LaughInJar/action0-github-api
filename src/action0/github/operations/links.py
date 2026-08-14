"""Reading the ``Link`` response header (RFC 8288, as GitHub sends it)."""

from __future__ import annotations

from action0.req import Response


def links(response: Response) -> dict[str, str]:
    """
    Extract the link relations of a response's ``Link`` header(s).

    >>> header = (
    ...     '<https://api.github.com/repositories/1/issues?page=2>; rel="next", '
    ...     '<https://api.github.com/repositories/1/issues?page=5>; rel="last"'
    ... )
    >>> links(Response(200, headers={"Link": header}))["next"]
    'https://api.github.com/repositories/1/issues?page=2'
    >>> links(Response(200))
    {}

    :param response: the response
    :return: a mapping of relation name (e.g. ``"next"``) to URL
    """
    result: dict[str, str] = {}
    for value in response.headers.get_all("Link"):
        # each header value holds comma-separated links: <url>; param; param
        for part in value.split(","):
            url_part, _, params = part.partition(";")
            url = url_part.strip().removeprefix("<").removesuffix(">")
            for param in params.split(";"):
                name, _, param_value = param.partition("=")
                if name.strip().lower() == "rel":
                    result[param_value.strip().strip('"')] = url
    return result
