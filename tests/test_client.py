import json
import requests

import httmock
import mock
import pytest

from httmock import HTTMock

from pyscaleio import exceptions
from pyscaleio.client import ScaleIOSession


@httmock.urlmatch(path=r".*login")
@httmock.remember_called
def login_payload(url, request):
    return httmock.response(200,
        json.dumps("some_random_token_string"),
        request=request
    )


@httmock.urlmatch(path=r".*logout")
@httmock.remember_called
def logout_payload(url, request):
    return httmock.response(200)


def test_session_initialize():

    client = ScaleIOSession("localhost", "admin", "passwd")
    assert client.host == "localhost"
    assert client.user == "admin"
    assert client.passwd == "passwd"

    assert not client.token
    assert isinstance(
        client._ScaleIOSession__session,
        requests.Session)
    headers = client._ScaleIOSession__session.headers
    assert "Accept" in headers
    assert headers["Accept"] == "application/json; version=2.0"
    assert headers["content-type"] == "application/json"

    assert client.endpoint == "https://localhost/api/"


def test_session_login_positive():

    client = ScaleIOSession("localhost", "admin", "passwd")
    assert not client.token
    assert not client._ScaleIOSession__session.auth

    with HTTMock(login_payload):
        client.login()

    assert client.token == "some_random_token_string"
    assert client._ScaleIOSession__session.auth == ("admin", "some_random_token_string")


@pytest.mark.parametrize(("code", "message", "exc"), [
    (401, "Unauthorized", exceptions.ScaleIOAuthError),
    (500, "Server error", requests.HTTPError)
])
def test_session_login_negative(code, message, exc):

    @httmock.urlmatch(path=r".*login")
    def login_payload(url, request):
        return httmock.response(code,
            json.dumps({
                "message": message,
                "httpStatusCode": code,
                "errorCode": 0
            }), request=request)

    client = ScaleIOSession("localhost", "admin", "passwd")
    assert not client.token
    assert not client._ScaleIOSession__session.auth

    with HTTMock(login_payload):
        with pytest.raises(exc) as e:
            client.login()

    if isinstance(e, exceptions.ScaleIOError):
        assert e.status_code == code
        assert e.error_code == 0
        assert str(e) == message

    assert not client.token
    assert not client._ScaleIOSession__session.auth


def test_session_send_request():

    @httmock.urlmatch(path=r"/api/test/instance")
    def request_payload(url, request):
        return httmock.response(200,
            json.dumps({"response": "test"}),
            request=request
        )

    client = ScaleIOSession("localhost", "admin", "passwd")
    client.token = "some_token"

    with HTTMock(request_payload):
        result = client.get("test/instance")

    assert result == {"response": "test"}


@pytest.mark.parametrize(("effect", "result", "retries"), [
    (
        [
            (401, {"message": "Unauthorized", "httpStatusCode": 401}),
            (200, {"response": "test"})
        ],
        {"response": "test"}, 2
    ),
    (
        [
            (401, {"message": "Unauthorized", "httpStatusCode": 401}),
            (401, {"message": "Unauthorized", "httpStatusCode": 401}),
            (200, {"response": "test"})
        ],
        {"response": "test"}, 3
    )
])
def test_session_send_request_retries(effect, result, retries):

    mock_handler = mock.Mock(side_effect=effect)

    @httmock.all_requests
    @httmock.remember_called
    def request_payload(url, request):
        code, payload = mock_handler()
        return httmock.response(code, json.dumps(payload),
            request=request
        )

    client = ScaleIOSession("localhost", "admin", "passwd")
    client.token = "expired_token"

    with HTTMock(login_payload, request_payload):
        real_result = client.get("test/instance")

    assert real_result == result
    assert mock_handler.call_count == retries
    assert client.token == "some_random_token_string"

    assert login_payload.call["count"] == retries - 1
    assert request_payload.call["count"] == retries


def test_session_send_request_with_login():

    @httmock.all_requests
    def api_payload(url, request):
        return httmock.response(200, json.dumps({"response": "test"}))

    client = ScaleIOSession("localhost", "admin", "passwd")

    with HTTMock(login_payload, api_payload):
        result = client.get("test/instance")

    assert result == {"response": "test"}
    assert client.token == "some_random_token_string"


def test_session_send_request_negative():

    @httmock.all_requests
    def api_exception(url, request):
        return httmock.response(500, json.dumps({
            "message": "Server error",
            "httpStatusCode": 500,
            "errorCode": 0
        }))

    client = ScaleIOSession("localhost", "admin", "passwd")
    assert not client.token

    with HTTMock(login_payload, api_exception):
        with pytest.raises(exceptions.ScaleIOError) as e:
            client.get("test/instance")

    exc = e.value
    assert exc.status_code == 500
    assert exc.error_code == 0
    assert "code=500" in str(exc)
    assert "message=Server error" in str(exc)


def test_session_send_request_malformed():

    @httmock.urlmatch(path=r"/api/test/instance")
    def request_payload(url, request):
        return httmock.response(200,
            "<?xml version='1.0' encoding='UTF-8'?>",
            request=request
        )

    client = ScaleIOSession("localhost", "admin", "passwd")
    client.token = "some_token"

    with HTTMock(request_payload):
        with pytest.raises(exceptions.ScaleIOMalformedError):
            client.get("test/instance")


def test_session_logout():

    client = ScaleIOSession("localhost", "admin", "passwd")
    assert not client.token

    with HTTMock(logout_payload):
        client.logout()
    assert not logout_payload.call["called"]

    with HTTMock(login_payload, logout_payload):
        client.login()
        assert client.token

        client.logout()

    assert not client.token
