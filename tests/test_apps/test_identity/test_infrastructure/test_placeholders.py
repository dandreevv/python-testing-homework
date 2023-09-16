from http import HTTPStatus
from typing import Callable

import httpretty
import pytest
from django.conf import LazySettings
from httpretty import http as http_method
from requests.exceptions import HTTPError

from server.apps.identity.intrastructure.services.placeholder import (
    LeadCreate,
    UserResponse,
)
from tests.plugins.identity.users import UserFactory, UserResponseFactory

MockApiFactory = Callable[
    [str, http_method.HttpBaseClass, HTTPStatus, str],
    None,
]


@pytest.fixture()
def api_url(settings: LazySettings) -> str:
    return settings.PLACEHOLDER_API_URL


@pytest.fixture()
def api_timeout(settings: LazySettings) -> int:
    return settings.PLACEHOLDER_API_TIMEOUT


@pytest.fixture
def mock_api_factory(api_url: str) -> MockApiFactory:

    def factory(
        path: str,
        method: http_method.HttpBaseClass,
        status: HTTPStatus = HTTPStatus.OK,
        body: str = "",
    ) -> None:
        httpretty.register_uri(
            method=method,
            status=status,
            body=body,
            uri=api_url + path,
        )

    with httpretty.httprettized():
        yield factory
        assert httpretty.has_request()


class TestLeadCreate:

    _api_path = 'users'

    def test_success(
        self,
        mock_api_factory: MockApiFactory,
        api_url: str,
        api_timeout: int,
    ) -> None:
        response_payload = UserResponseFactory.build()
        mock_api_factory(
            path=self._api_path,
            method=httpretty.POST,
            body=response_payload.json(),
        )

        placeholder = LeadCreate(api_url, api_timeout)
        user = UserFactory.build()
        response = placeholder.__call__(user=user)

        assert isinstance(response, UserResponse)
        assert response.id == response_payload.id

    @pytest.mark.parametrize(
        'http_status',
        (
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.BAD_REQUEST,
        ),
    )
    def test_http_error(
        self,
        http_status: HTTPStatus,
        mock_api_factory,
        api_url: str,
        api_timeout: int,
    ) -> None:
        mock_api_factory(
            path=self._api_path,
            method=httpretty.POST,
            status=http_status,
        )

        placeholder = LeadCreate(api_url, api_timeout)
        user = UserFactory.build()
        with pytest.raises(HTTPError) as exc_info:
            placeholder.__call__(user=user)

        assert exc_info.value.response.status_code == http_status
