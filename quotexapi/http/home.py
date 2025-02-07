"""Module for Quotex http history resource."""

from ..http.resource import Resource


class Home(Resource):
    """Class for Quotex history resource."""

    def _get(self, data=None, headers=None):
        """Send get request for Quotex API history http resource.

        :returns: The instance of :class:`navigator.Session`.
        """
        return self.send_http_request(method="GET", data=data, headers=headers)

    def __call__(self):
        self.url = f"{self.api.https_url}/{self.api.lang}/"
        header_data = self.api.session_data.get("headers")
        headers = {
            "referer": f"{self.api.https_url}/{self.api.lang}",
            "cookie": header_data.get("Cookie"),
        }
        response = self._get(headers=headers)

        return response
