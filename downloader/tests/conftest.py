from collections.abc import Callable

import httpx


def make_mock_client_factory(handler: Callable[[httpx.Request], httpx.Response]):
    """Returns a transport that can be passed to ApiClient."""
    return httpx.MockTransport(handler)
