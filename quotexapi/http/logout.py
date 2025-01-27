"""Module for Quotex http logout resource."""

from ..http.resource import Resource


class Logout(Resource):
    """Class for Quotex login resource."""

    def _get(self, data=None, headers=None):
        """Send get request for Quotex API login http resource.
        :returns: The instance of :class:`navigator.Session`.
        """
        return self.send_http_request(method="GET", data=data, headers=headers)

    async def __call__(self):
        self.url = f"{self.api.https_url}/{self.api.lang}/logout"
        header_data = self.api.session_data.get("headers")
        headers = {
            "referer": f"{self.api.https_url}/{self.api.lang}/trade",
            "cookie": header_data.get("Cookie"),
            "content-type": "application/json",
            "accept": "application/json",
        }
        return self._get(headers=headers)
