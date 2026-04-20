"""Legacy placeholder. Disk adapters will move to core/platform/mac/disk_adapter.py."""


def unmount_device(*_args, **_kwargs):
    raise NotImplementedError("Legacy implementation cleared.")


def format_disk(*_args, **_kwargs):
    raise NotImplementedError("Legacy implementation cleared.")


def get_disk_info(*_args, **_kwargs):
    raise NotImplementedError("Legacy implementation cleared.")
