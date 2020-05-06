# -*- coding: utf-8 -*-
import atexit
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from naomi import pluginstore


class Notifier(object):
    def __init__(self, mic, brain, *args, **kwargs):
        self._logger = logging.getLogger(__name__)
        self._logger.info("Setting up notifier")
        self.notifiers = []

        # add all notifier plugins
        notification_clients = pluginstore.PluginStore()
        notification_clients.detect_plugins("notificationclient")
        for info in notification_clients.get_plugins():
            notifier = info.plugin_class(
                info,
                mic=mic,
                brain=brain,
                timestamp=None
            )
            if(hasattr(notifier, "gather")):
                self.notifiers.append(
                    notifier
                )

        sched = BackgroundScheduler(timezone="UTC", daemon=True)
        sched.start()
        sched.add_job(self.gather, 'interval', seconds=30)
        atexit.register(lambda: sched.shutdown(wait=False))

    def gather(self):
        [client.run() for client in self.notifiers]
