"""
dBus System Notifications.

Allows processes running as root to send notifications to all users.
"""

import os
import dbus


def get_user_paths(bus, clss='user'):
    """Get all dBus `User` object paths of class `clss`."""
    user_paths = set()

    logind = bus.get_object('org.freedesktop.login1', '/org/freedesktop/login1')
    loginm = dbus.Interface(logind, 'org.freedesktop.login1.Manager')

    for sess_spec in loginm.ListSessions():
        sess_path = sess_spec[4]

        sess = bus.get_object('org.freedesktop.login1', sess_path)
        sess_p = dbus.Interface(sess, 'org.freedesktop.DBus.Properties')

        if sess_p.Get('org.freedesktop.login1.Session', 'Class') == clss:
            user_path = sess_p.Get('org.freedesktop.login1.Session', 'User')[1]
            user_paths |= {user_path}

    return user_paths


def get_user_runtime_paths(bus=dbus.SystemBus()):
    """Get dBus user runtime paths of all active "human" users."""
    for user_path in get_user_paths(bus):
        user = bus.get_object('org.freedesktop.login1', user_path)
        user_p = dbus.Interface(user, 'org.freedesktop.DBus.Properties')

        uid = user_p.Get('org.freedesktop.login1.User', 'UID')
        rt_path = user_p.Get('org.freedesktop.login1.User', 'RuntimePath')
        yield uid, rt_path


def _notify_all_show(n):
    """Show notification to all active "human" users."""
    ids = dict()

    for uid, path in get_user_runtime_paths():
        os.seteuid(uid)     # bypass systemd access check

        addr = "unix:path={}/bus".format(path)
        sess = dbus.bus.BusConnection(addr)

        notif_o = sess.get_object('org.freedesktop.Notifications', '/org/freedesktop/Notifications')
        notif_i = dbus.Interface(notif_o, 'org.freedesktop.Notifications')

        notif_id = notif_i.Notify(n.app_name, n.replaces_id, n.app_icon, n.summary, n.body,
                                  n.actions, n.hints, n.timeout)

        os.seteuid(0)

        ids[uid] = notif_id

    return ActiveSystemNotification(n, ids)


def _notify_all_close(n):
    """Close the notification on all sessions it is active."""
    for uid, path in get_user_runtime_paths():
        if uid not in n.ids:
            continue

        os.seteuid(uid)     # bypass systemd access check

        addr = "unix:path={}/bus".format(path)
        sess = dbus.bus.BusConnection(addr)

        notif_o = sess.get_object('org.freedesktop.Notifications', '/org/freedesktop/Notifications')
        notif_i = dbus.Interface(notif_o, 'org.freedesktop.Notifications')

        notif_i.CloseNotification(n.ids[uid])

        os.seteuid(0)


class SystemNotification:
    """A notification that can be sent to all users."""

    def __init__(self, app_name, summary="", body="", replaces_id=0, timeout=-1, app_icon=''):
        """Create a new notification."""
        self.app_name = app_name
        self.app_icon = app_icon
        self.summary = summary
        self.body = body
        self.replaces_id = replaces_id
        self.timeout = timeout
        self.hints = dict()
        self.actions = list()

    def show(self):
        """Show this notification to all "human" users."""
        return _notify_all_show(self)


class ActiveSystemNotification:
    """A SystemNotification that has already been sent and is active."""

    def __init__(self, notif, ids):
        self.notif = notif
        self.ids = ids

    def close(self):
        """Close this notification on all session it is active."""
        _notify_all_close(self)
