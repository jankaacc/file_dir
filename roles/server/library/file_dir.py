#!/usr/bin/python
import enum
import shutil
from pathlib import Path

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r"""
---
module: file_dir
short_description: Manage files and directories
description:
- Create files and directories. 
- Remove files and directories.
options:
  path:
    description:
    - Path to the file/directory.
    type: path
    required: yes
  state:
    description:
    - When (state=file) file will be created under provided path if does not exist.
    - When (state=directory) directory will be created under provided path if does not exist.
    - When (state=absent) directories will be recursively deleted, and files will be unlinked.
    type: str
    required: yes
  nested:
    description:
    - Recursively create specified files/directories.
    - This applies only when (state=file or directory).
    type: bool
    default: false
attributes:
    diff_mode:
        details: changes in path and state will be shown.
        support: partial
    platform:
        platforms: posix
"""


EXAMPLES = r"""
- name: create file
  file_dir:
    path: file
    state: file

- name: create file under nested directory
  file_dir:
    path: foo/bar/file
    state: file
    nested: true

- name: create directory
  file_dir:
    path: dir
    state: directory

- name: create nested directory
  file_dir:
    path: dir/foo/bar
    state: directory
    nested: true

- name: delete file
  file_dir:
    path: file
    state: absent

- name: delete dir
  file_dir:
    path: dir
    state: absent

- name: delete non empty dir
  file_dir:
    path: foo
    state: absent

- name: delete non existing file
  file_dir:
    path: file_non_existing
    state: absent

- name: delete non existing dir
  file_dir:
    path: dir_non_existing
    state: absent

"""


class State(enum.Enum):
    FILE = "file"
    DIRECTORY = "directory"
    ABSENT = "absent"

    @classmethod
    def to_choices(cls) -> list:
        return [e.value for e in cls]


def get_current_state(path: Path):
    if path.exists():
        if path.is_dir():
            return State.DIRECTORY
        return State.FILE
    return State.ABSENT


def init_diff(path: str, next_state: State, current_state: State) -> dict:
    diff = {
        "before": {"path": path},
        "after": {"path": path},
    }

    if current_state != next_state:
        diff["before"]["state"] = current_state.value
        diff["after"]["state"] = next_state.value

    return diff


def get_check_mode_result(diff: dict, path: str) -> dict:
    return {"changed": True, "diff": diff, "path": path}


def ensure_file(path: str, nested: bool, module: AnsibleModule) -> dict:
    file = Path(path)
    current_state = get_current_state(file)

    changed = False
    result = {"path": path}

    diff = init_diff(path, State.FILE, current_state)

    if current_state == State.ABSENT:
        if module.check_mode:
            return get_check_mode_result(diff, path)
        try:
            file.parent.mkdir(parents=nested, exist_ok=True)
            file.touch()

            changed = True
        except (OSError, IOError) as e:
            module.fail_json(
                msg=f"Error, could not create file: {path}, error: {e}."
            )
    if current_state == State.DIRECTORY:
        module.fail_json(
            msg=f"Error, could not create file: {path}, path is directory."
        )

    result["changed"] = changed
    result["diff"] = diff
    return result


def ensure_directory(path: str, nested: bool, module: AnsibleModule) -> dict:
    dir = Path(path)
    current_state = get_current_state(dir)

    changed = False
    result = {"path": path}

    diff = init_diff(path, State.DIRECTORY, current_state)

    if current_state == State.ABSENT:
        if module.check_mode:
            return get_check_mode_result(diff, path)
        try:
            dir.mkdir(parents=nested, exist_ok=True)
            changed = True
        except OSError as e:
            module.fail_json(
                msg=f"Error, could not create directory: {path}, error: {e}."
            )

    result["changed"] = changed
    result["diff"] = diff
    return result


def ensure_absent(path: str, module: AnsibleModule) -> dict:
    absent = Path(path)
    current_state = get_current_state(absent)

    changed = False
    result = {"path": path}

    diff = init_diff(path, State.ABSENT, current_state)

    if current_state == State.DIRECTORY:
        if module.check_mode:
            return get_check_mode_result(diff, path)
        try:
            shutil.rmtree(path, ignore_errors=False)
            changed = True
        except Exception as e:
            module.fail_json(
                msg=f"Error, could not delete directory: {path}, error: {e}"
            )
    elif current_state == State.FILE:
        if module.check_mode:
            return get_check_mode_result(diff, path)
        try:
            absent.unlink(missing_ok=True)
            changed = True
        except OSError as e:
            module.fail_json(
                msg=f"Error, could not delete file: {path}, error: {e}"
            )

    result["changed"] = changed
    result["diff"] = diff
    return result


def run_proper_handler(module: AnsibleModule) -> dict:
    result = dict(changed=False)
    params = module.params

    state = params["state"]
    path = params["path"]
    nested = params["nested"]

    # could use match statement here
    if state == State.FILE.value:
        result = ensure_file(path, nested, module)
    elif state == State.DIRECTORY.value:
        result = ensure_directory(path, nested, module)
    elif state == State.ABSENT.value:
        result = ensure_absent(path, module)

    return result


def run_module():
    module_args = dict(
        path=dict(type="path", required=True),
        state=dict(type="str", choices=State.to_choices(), required=True),
        nested=dict(type="bool", default=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    result = run_proper_handler(module)
    module.exit_json(**result)


if __name__ == "__main__":
    run_module()
