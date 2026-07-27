import pytest

from edutap.pass_builder_api.validation import validate_pass_id, validate_person_uid


def test_valid_values_pass_through():
    assert validate_pass_id("p-1") == "p-1"
    assert validate_person_uid("abc@lmu.de") == "abc@lmu.de"


@pytest.mark.parametrize("bad", ["", "   "])
def test_blank_pass_id_rejected(bad):
    with pytest.raises(ValueError, match="pass_id"):
        validate_pass_id(bad)


@pytest.mark.parametrize("bad", ["", "   "])
def test_blank_person_uid_rejected(bad):
    with pytest.raises(ValueError, match="person_uid"):
        validate_person_uid(bad)
