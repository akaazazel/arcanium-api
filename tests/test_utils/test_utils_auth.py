from datetime import timedelta, datetime

import pytest
from app.utils.auth import (
    create_token,
    decode_token,
    generate_tokens,
    hash_password,
    is_token_revoked,
    verify_password,
    verify_token,
)
from jwt.exceptions import InvalidSubjectError, InvalidTokenError
from fastapi import Response


def test_hashing_correct_password():
    password = "My_H0rrible_PAssWord"

    hashed_pwd = hash_password(password)

    result = verify_password(password, hashed_pwd)

    assert result == True


def test_hashing_wrong_password():
    correect_pwd = "My_H0rrible_PAssWord"
    wrong_pwd = "Wrong_Password"

    hashed_pwd = hash_password(correect_pwd)

    result = verify_password(wrong_pwd, hashed_pwd)

    assert result == False


def test_hashing_same_password():
    password = "My_password_01"

    hash_1 = hash_password(password)
    hash_2 = hash_password(password)

    assert hash_1 != hash_2


@pytest.mark.parametrize(
    "data, is_data_invalid",
    [
        ({"sub": "user_id_01"}, False),
        ({"sub": "user_id_02", "test": "some_data"}, False),
        ({"sub": 2}, True),
    ],
)
@pytest.mark.parametrize(
    "expire_delta",
    [
        timedelta(days=10),
    ],
)
@pytest.mark.parametrize(
    "token_type",
    ["access", "refresh"],
)
def test_token_processing(
    data,
    expire_delta,
    token_type,
    is_data_invalid,
):
    result = create_token(data, expire_delta, token_type)

    if is_data_invalid:
        with pytest.raises(InvalidSubjectError):
            verify_token(result, token_type)
    else:
        user_id = verify_token(result, token_type)
        assert user_id == str(data["sub"])


@pytest.mark.parametrize(
    "actual_token_type",
    ["access", "refresh"],
)
@pytest.mark.parametrize(
    "comparing_token_type",
    ["access", "refresh"],
)
def test_decode_token(actual_token_type, comparing_token_type):
    user_data = {"sub": "1"}
    expire_delta = timedelta(days=10)

    token = create_token(
        data=user_data,
        expire_delta=expire_delta,
        token_type=actual_token_type,
    )

    if (actual_token_type != comparing_token_type) and (
        comparing_token_type != "access"
    ):
        with pytest.raises(InvalidTokenError):
            decode_token(token, comparing_token_type)
    else:
        decoded_token = decode_token(token, comparing_token_type)
        assert decoded_token is not None
        assert decoded_token["sub"] == "1"
