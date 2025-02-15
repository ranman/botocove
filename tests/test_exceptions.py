from datetime import datetime
from unittest.mock import MagicMock

import pytest

from botocove import cove
from botocove.cove_session import CoveSession


@pytest.fixture()
def mock_boto3_session() -> MagicMock:
    mock_session = MagicMock()
    list_accounts_result = {
        "Accounts": [
            {"Id": "123123123123", "Status": "ACTIVE"},
            {"Id": "123123123123", "Status": "ACTIVE"},
        ]
    }
    mock_session.client.return_value.get_paginator.return_value.paginate.return_value.build_full_result.return_value = (  # noqa E501
        list_accounts_result
    )
    describe_account_results = [
        {
            "Account": {
                "Id": "123123123123",
                "Arn": "hello-arn",
                "Email": "email@address.com",
                "Name": "an-account-name",
                "Status": "ACTIVE",
                "JoinedMethod": "CREATED",
                "JoinedTimestamp": datetime(2015, 1, 1),
            }
        },
        {
            "Account": {
                "Id": "456456456456",
                "Arn": "hello-arn",
                "Email": "email@address.com",
                "Name": "an-account-name",
                "Status": "ACTIVE",
                "JoinedMethod": "CREATED",
                "JoinedTimestamp": datetime(2015, 1, 1),
            }
        },
    ]
    mock_session.client.return_value.describe_account.side_effect = (
        describe_account_results
    )
    # Mock out the credential requiring API call
    return mock_session


def test_no_account_id_exception(mock_boto3_session: MagicMock) -> None:
    @cove(
        assuming_session=mock_boto3_session,
        target_ids=["456456456456"],
        ignore_ids=["456456456456"],
    )
    def simple_func(session: CoveSession) -> str:
        return "hello"

    with pytest.raises(
        ValueError,
        match="There are no eligible account ids to run decorated func against",
    ):
        simple_func()


def test_handled_exception_in_wrapped_func(mock_boto3_session: MagicMock) -> None:
    @cove(assuming_session=mock_boto3_session, target_ids=["456456456456"])
    def simple_func(session: CoveSession) -> None:
        raise Exception("oh no")

    results = simple_func()
    expected = {
        "Id": "456456456456",
        "RoleName": "OrganizationAccountAccessRole",
        "AssumeRoleSuccess": True,
        "Arn": "hello-arn",
        "Email": "email@address.com",
        "Name": "an-account-name",
        "Status": "ACTIVE",
        "RoleSessionName": "OrganizationAccountAccessRole",
        "ExceptionDetails": repr(Exception("oh no")),
    }

    # Compare repr of exceptions
    results["Exceptions"][0]["ExceptionDetails"] = repr(
        results["Exceptions"][0]["ExceptionDetails"]
    )

    assert results["Exceptions"][0] == expected


def test_raised_exception_in_wrapped_func(mock_boto3_session: MagicMock) -> None:
    @cove(
        assuming_session=mock_boto3_session,
        target_ids=["456456456456"],
        raise_exception=True,
    )
    def simple_func(session: CoveSession) -> None:
        raise Exception("oh no")

    with pytest.raises(Exception, match="oh no"):
        simple_func()


def test_malformed_ignore_ids(mock_boto3_session: MagicMock) -> None:
    @cove(
        assuming_session=mock_boto3_session,
        target_ids=["456456456456"],
        ignore_ids=["cat"],
    )
    def simple_func(session: CoveSession) -> str:
        return "hello"

    with pytest.raises(
        ValueError,
        match=("provided id is neither an aws account nor an ou: cat"),
    ):
        simple_func()


def test_malformed_ignore_ids_type(mock_boto3_session: MagicMock) -> None:
    @cove(
        assuming_session=mock_boto3_session,
        target_ids=None,
        ignore_ids=[456456456456],  # type: ignore
    )
    def simple_func(session: CoveSession) -> str:
        return "hello"

    with pytest.raises(
        TypeError,
        match=(
            "456456456456 is an incorrect type: all account and ou id's must be strings not <class 'int'>"  # noqa E501
        ),
    ):
        simple_func()


def test_malformed_target_id(mock_boto3_session: MagicMock) -> None:
    @cove(
        assuming_session=mock_boto3_session,
        target_ids=["xu-gzxu-393a2l5b"],
        ignore_ids=["456456456456"],
    )
    def simple_func(session: CoveSession) -> str:
        return "hello"

    with pytest.raises(
        ValueError,
        match=("provided id is neither an aws account nor an ou: xu-gzxu-393a2l5b"),
    ):
        simple_func()


def test_malformed_target_id_type(mock_boto3_session: MagicMock) -> None:
    @cove(
        assuming_session=mock_boto3_session,
        target_ids=[456456456456],  # type: ignore
        ignore_ids=[],
    )
    def simple_func(session: CoveSession) -> str:
        return "hello"

    with pytest.raises(
        TypeError,
        match=(
            "456456456456 is an incorrect type: all account and ou id's must be strings not <class 'int'>"  # noqa E501
        ),
    ):
        simple_func()
