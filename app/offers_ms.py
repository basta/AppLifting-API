from typing import Optional, Any

import requests

import app.models as models


class APIError(Exception):
    pass


class OffersAPI:
    """
    Offers MS communication object.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url
        self._token: Optional[str] = None

    @property
    def token(self) -> str:
        if self._token:
            return self._token
        else:
            raise ValueError(
                "Tried to get token without setting it first using refresh_token"
            )

    def refresh_token(self):
        """
        Refresh and load token of this offerAPI object.

        :return: True on success, False on fail
        :raises requests.exceptions.ConnectionError: If
        """
        data = self.send_request("POST", "/auth", use_token=False)
        self._token = data["access_token"]

    def send_request(
        self, method, endpoint: str, data: Optional[dict] = None, use_token=True
    ):
        """
        Send request to API endpoint, parse the response and return response data.

        Can raise errors on unsuccessful API calls

        :param method: HTTP verb to use with request
        :param endpoint: API endpoint (e.g. /auth) must start with a leading "/"
        :param data: Data to send in request body, json format
        :param use_token: Enable adding access token to the request
        :raises APIError: On unsuccessful
        :raises ValueError: If using token before setting it using refresh_token
        :return: Response from API
        """
        request_kwargs = {}
        if data:
            request_kwargs["json"] = data
        if use_token:
            request_kwargs["headers"] = {"Bearer": self.token}

        response = requests.request(
            method, f"{self.base_url}{endpoint}", **request_kwargs
        )

        if not response.ok:
            if method != "GET":
                raise APIError(
                    f"Unsuccessful status code: {response.status_code} "
                    f"for {endpoint} with message: \"{response.json()['msg']}\""
                )
            else:
                # 404 error for GET method is not in json format
                raise APIError(
                    f"Unsuccessful status code: {response.status_code} "
                    f"for {endpoint}"
                )

        return response.json()

    def register_product(self, product: models.Product) -> dict:
        return self.send_request(
            "POST",
            "/products/register",
            data={"id": product.id, "name": product.name, "description": product.desc},
        )

    def get_offers_for_product(self, product: models.Product) -> list[dict]:
        """
        :return: List of json dicts representing offers
        """
        return self.send_request("GET", f"/products/{product.id}/offers")
