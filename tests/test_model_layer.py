from testapp.models import DummyModel


def test_model_multiple_loose_fk_fields():
    constraints = DummyModel._meta.constraints
    names = {c.name for c in constraints}

    assert len(constraints) == 1
    assert len(names) == 1
