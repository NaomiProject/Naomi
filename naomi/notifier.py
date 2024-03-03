# -*- coding: utf-8 -*-
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from naomi import profile


class Notifier(object):
    def __init__(self, mic, brain, *args, **kwargs):
        self.mic = mic
        self._logger = logging.getLogger(__name__)
        self._logger.info("Setting up notifier")
        self.notifiers = []

        # add all notifier plugins
        for info in profile.get_arg('plugins').get_plugins_by_category(
            category="notificationclient"
        ):
            notifier = info.plugin_class(
                info,
                mic=mic,
                brain=brain,
                timestamp=None
            )
            if hasattr(notifier, "gather"):
                self.notifiers.append(
                    notifier
                )
                print("Added notifier notification client {}".format(info.name))

        self.sched = BackgroundScheduler(timezone="UTC", daemon=True)
        self.sched.start()
        # FIXME add an interval setting to profile so this can be overridden
        self.sched.add_job(self.gather, 'interval', seconds=30)

    def gather(self):
        [client.run() for client in self.notifiers]
        if self.mic.Continue is False:
            print("Notifier shutting down")
            self.sched.shutdown(wait=False)
