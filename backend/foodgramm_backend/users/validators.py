import re

from django.core.exceptions import ValidationError

from .constants import REGEX_USERNAME


def validator_username(value):
    newstr = " ".join(set(re.sub(REGEX_USERNAME, '', value)))
    if newstr:
        raise ValidationError(f'Имя не должно содержать: {newstr}')
    return value
