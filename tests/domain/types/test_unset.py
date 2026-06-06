import copy

from project.domain.types.unset import _Unset, unset


def test_unset_is_falsy():
    assert bool(unset) is False


def test_unset_bool_returns_false():
    instance = _Unset()
    assert bool(instance) is False


def test_deepcopy_returns_same_instance():
    assert copy.deepcopy(unset) is unset


def test_deepcopy_on_new_instance_returns_same():
    instance = _Unset()
    assert copy.deepcopy(instance) is instance
