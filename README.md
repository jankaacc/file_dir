## Test role for file dir creation/deletion

This repository contains custom module for file and directory
creation and deletion.

## Ansible version compatibility

Tested with the Ansible Core 2.13

## Python version compatibility

This repository was written with python 3.10

## Example of usage

```
- name: create file under nested directory
  file_dir:
    path: foo/bar/file
    state: file
    nested: true
```

This creates a file under nested directory which doesn't need to
exist, parent folders will be created along with the file.

For more example please check example role and tasks in repo

## Run test playbook

```ansible-playbook ./test_server.yml```
