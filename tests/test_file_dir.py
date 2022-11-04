import pytest

from roles.server.library.file_dir import run_proper_handler


class FailException(Exception):
    pass


class FakeModule:
    def __init__(self, check_mode=False, **kwargs):
        self.params = kwargs
        self.check_mode = check_mode

    def fail_json(self, *args, **kwargs):
        self.exit_args = args
        self.exit_kwargs = kwargs
        raise FailException("FAIL")

    def exit_json(self, *args, **kwargs):
        self.exit_args = args
        self.exit_kwargs = kwargs


def test_file_creation(tmp_path):
    file_path = tmp_path / "file"
    module = FakeModule(path=file_path, state="file", nested=False)
    run_proper_handler(module)
    assert len(list(tmp_path.iterdir())) == 1


def test_nested_file_creation_fails_when_no_nested_option(tmp_path):
    file_path = tmp_path / "nest1" / "nest2" / "file"
    module = FakeModule(path=file_path, state="file", nested=False)
    with pytest.raises(FailException):
        run_proper_handler(module)


def test_nested_file_creation_success_when_no_nested_option(tmp_path):
    file_path = tmp_path / "nest1" / "nest2" / "file"
    module = FakeModule(path=file_path, state="file", nested=True)
    run_proper_handler(module)
    assert len(list(file_path.parent.iterdir())) == 1


def test_dir_creation(tmp_path):
    dir_path = tmp_path / "nest1"
    module = FakeModule(path=dir_path, state="directory", nested=False)
    run_proper_handler(module)
    assert len(list(tmp_path.iterdir())) == 1


def test_nested_dir_creation_fails_when_no_nested_option(tmp_path):
    dir_path = tmp_path / "nest1" / "nest2" / "nest3"
    module = FakeModule(path=dir_path, state="directory", nested=False)
    with pytest.raises(FailException):
        run_proper_handler(module)


def test_nested_dir_creation_success_when_nested_option(tmp_path):
    dir_path = tmp_path / "nest1" / "nest2" / "nest3"
    module = FakeModule(path=dir_path, state="directory", nested=True)
    run_proper_handler(module)
    assert len(list(dir_path.parent.iterdir())) == 1


def test_dir_created_only_once(tmp_path):
    dir_path = tmp_path / "nest1"
    module = FakeModule(path=dir_path, state="directory", nested=False)
    for i in range(3):
        run_proper_handler(module)
    assert len(list(tmp_path.iterdir())) == 1


def test_file_created_only_once(tmp_path):
    file_path = tmp_path / "file"
    module = FakeModule(path=file_path, state="file", nested=False)
    for i in range(3):
        run_proper_handler(module)
    assert len(list(tmp_path.iterdir())) == 1


def test_file_deletion(tmp_path):
    file_path = tmp_path / "file"
    module = FakeModule(path=file_path, state="file", nested=False)
    run_proper_handler(module)
    assert len(list(tmp_path.iterdir())) == 1
    module = FakeModule(path=file_path, state="absent", nested=False)
    run_proper_handler(module)
    assert len(list(tmp_path.iterdir())) == 0


def test_directory_deletion(tmp_path):
    dir_path = tmp_path / "nested1"
    module = FakeModule(path=dir_path, state="directory", nested=False)
    run_proper_handler(module)
    assert len(list(tmp_path.iterdir())) == 1
    module = FakeModule(path=dir_path, state="absent", nested=False)
    run_proper_handler(module)
    assert len(list(tmp_path.iterdir())) == 0


def test_non_existing_deletion(tmp_path):
    dir_path = tmp_path / "nested1" / "nested2"
    assert len(list(tmp_path.iterdir())) == 0
    module = FakeModule(path=dir_path, state="absent", nested=False)
    run_proper_handler(module)
    assert len(list(tmp_path.iterdir())) == 0


def test_nested_file_deletion(tmp_path):
    file_path = tmp_path / "nested1" / "nested2" / "file"
    module = FakeModule(path=file_path, state="file", nested=True)
    run_proper_handler(module)
    assert len(list(tmp_path.iterdir())) == 1
    module = FakeModule(path=file_path, state="absent", nested=False)
    run_proper_handler(module)
    assert len(list(file_path.parent.iterdir())) == 0
