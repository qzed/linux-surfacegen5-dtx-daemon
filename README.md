# Linux DTX Daemon for Surface Book 2

**DEPRECATED:**
This project has been deprecated by https://github.com/qzed/linux-surface-dtx-daemon/.
Development will continue there.

Linux User-Space Detachment System (DTX) Daemon for the Surface ACPI Driver (and Surface Book 2).

## What is this?

This daemon allows proper clipboard detachment on the Surface Book 2.
It allows you to run commands before the clipboard is unlocked, after it has been re-attached, or when the unlocking-process has been aborted (e.g. by pressing the detach-button a second time).
This daemon also provides desktop-notifications to indicate when the clipboard can be physically removed from the base and when the re-attachmend process has been completed.

## Installation

If you have an Arch Linux or Debian based distributions, have a look at the [releases page][releases] for official packages.
After installation you may want to enable the systemd service using `systemctl enable surface-dtx.service`.

Alternatively, you can build these packages yourself, using the provided `PKGBUILD` (Arch Linux) or `make-debpkg` script in the respective `pkg` sub-directories.

### Installation without a Package

If you don't find a package for your distribution (or want to create a package for it), you can also install this daemon via `make install` (and uninstall it via `make uninstall`, an optional `DESTDIR=...` is supported).
As this bypasses the package-manager, this way of installation is not recommended.

## Configuration

The main configuration files can be found under `/etc/surface-dtx/surface-dtx.cfg`.
Here you can specify the handler-scripts for supported events and other options.
All options are explanined in this file, the configuration language is TOML.


[releases]: https://github.com/qzed/linux-surfacegen5-dtx-daemon/releases
