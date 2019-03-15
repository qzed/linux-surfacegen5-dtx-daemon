# Linux DTX Daemon for Surface Book 2

Linux User-Space Detachment System (DTX) Daemon for the Surface ACPI Driver (and Surface Book 2).

Work in progress.
At the moment the daemon requires the [surface-acpi module](https://github.com/qzed/linux-surfacegen5-acpi/tree/master/module) to be installed and loaded, the patch version (as included in [jakeday/linux-surface](https://github.com/jakeday/linux-surface/)) has not been updated yet.
This will follow once the user-space API has been stabilized.

At the moment this provides the following functionality:

- Immediate unlocking of the base when the button has been pressed.

- Notifications indicating when the base can be detached.

Run with `sudo python src/daemon.py`.
