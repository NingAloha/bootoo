"""Legacy placeholder. Device probing will move to core/platform/mac/device_probe.py."""


def list_all_devices():
    raise NotImplementedError("Legacy implementation cleared. Use the new platform/mac skeleton.")


def list_available_devices(*_args, **_kwargs):
    raise NotImplementedError("Legacy implementation cleared. Use the new planner + platform flow.")
