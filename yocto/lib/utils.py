## Users collection identifiers ##
USERNAME_IDENTIFIER = "username"
PASSWORD_HASH_IDENTIFIER = "password_hash"
ACCOUNT_CREATION_DATE_IDENTIFIER = "creation_date"

## Urls collection identifiers ##
LONG_URL_IDENTIFIER = "long_url"
SHORT_ID_IDENTIFIER = "short_id"
URL_CREATION_DATE_IDENTIFIER = "creation_date"
CREATOR_USERNAME_IDENTIFIER = "creator_username"

def _verify_type(parameter, expected_type):
    if not isinstance(parameter, expected_type):
        raise TypeError(f"Expected type '{expected_type}'")
