"""Module for Quotex http profile resource."""

from ..http.resource import Resource


class GetProfile(Resource):
    """Class for Quotex profile resource."""

    def _get(self, data=None, headers=None):
        """Send get request for Quotex API profile http resource.
        :returns: The instance of :class:`navigator.Session`.
        """
        return self.send_http_request(method="GET", data=data, headers=headers)

    async def __call__(self):
        self.url = f"{self.api.https_url}/api/v1/cabinets/digest"
        header_data = self.api.session_data.get("headers")
        headers = {
            "referer": f"{self.api.https_url}/{self.api.lang}/trade",
            "cookie": header_data.get("Cookie"),
            "content-type": "application/json",
            "accept": "application/json",
        }

        response = self._get(headers=headers)
        if response:
            return response.json()
        return {}
