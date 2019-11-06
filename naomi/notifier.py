# -*- coding: utf-8 -*-
import atexit
import contextlib
import logging
import random
import queue
from apscheduler.schedulers.background import BackgroundScheduler
from naomi import app_utils
from naomi import i18n
from naomi import paths
from naomi import profile


class Notifier(object):

    class NotificationClient(object):

        def __init__(self, gather, timestamp):
            self.gather = gather
            self.timestamp = timestamp

        def run(self):
            self.timestamp = self.gather(self.timestamp)

    def __init__(self, mic, brain, *args, **kwargs):
        self._logger = logging.getLogger(__name__)
        self._logger.info("Setting up notifier")
        translations = i18n.parse_translations(paths.data('locale'))
        translator = i18n.GettextMixin(translations)
        self.gettext = translator.gettext
        self._mic = mic
        self._brain = brain
        self.q = queue.Queue()
        self.notifiers = []

        # check to see if we can connect to an email account
        if(app_utils.check_imap_config()):
            self.notifiers.append(
                self.NotificationClient(
                    self.handle_email_notifications,
                    None
                )
            )
            if(not app_utils.check_smtp_config()):
                self._logger.warning(
                    " ".join([
                        'Email smtp access is not configured,',
                        'I will not be able to respond.'
                    ])
                )
        else:
            self._logger.warning(
                " ".join([
                    'Email imap access is not configured,',
                    'notifier will not be used'
                ])
            )
        sched = BackgroundScheduler(timezone="UTC", daemon=True)
        sched.start()
        sched.add_job(self.gather, 'interval', seconds=30)
        atexit.register(lambda: sched.shutdown(wait=False))

    def gather(self):
        [client.run() for client in self.notifiers]

    def handle_email_notifications(self, last_date):
        """Places new Gmail notifications in the Notifier's queue."""
        self._logger.info("Checking email since {}".format(last_date))
        emails = app_utils.fetch_emails(since=last_date, email_filter="(UNSEEN)")
        self._logger.info("{} new emails".format(len(emails)))
        if emails:
            last_date = app_utils.get_most_recent_date(emails)

        def handle_email(e):
            # if the subject line matches the first line of the email, then
            # discard the subject line. If not, then append the body to the
            # subject line.
            message = app_utils.get_message_text(e)
            if(any(x in message for x in profile.get(["keyword"]))):
                # This message should be marked as read
                app_utils.mark_read(e)
                emailmic = EmailMic(
                    address=e['From'],
                    subject=e["Subject"]
                )
                intent = self._brain.query([message])
                if intent:
                    try:
                        self._logger.info(intent)
                        intent['action'](intent, emailmic)
                    except Exception:
                        self._logger.error(
                            'Failed to execute module',
                            exc_info=True
                        )
                        self.mic.say(
                            " ".join([
                                self.gettext("I'm sorry."),
                                self.gettext("I had some trouble with that operation."),
                                self.gettext("Please try again later.")
                            ])
                        )
                    else:
                        self._logger.debug(
                            " ".join([
                                "Handling of phrase '{}'",
                                "by module '{}' completed"
                            ]).format(
                                message,
                                intent
                            )
                        )
                else:
                    emailmic.say(random.choice([  # nosec
                        self.gettext("I'm sorry, could you repeat that?"),
                        self.gettext("My apologies, could you try saying that again?"),
                        self.gettext("Say that again?"),
                        self.gettext("I beg your pardon?")
                    ]))
            else:
                self._mic.say("New email from %s." % app_utils.get_sender(e))
            return True

        for e in emails:
            self.q.put(handle_email(e))

        return last_date

    def get_notification(self):
        """Returns a notification. Note that this function is consuming."""
        try:
            notif = self.q.get(block=False)
            return notif
        except Queue.Empty:
            return None

    def get_all_notifications(self):
        """
            Return a list of notifications in chronological order.
            Note that this function is consuming, so consecutive calls
            will yield different results.
        """
        notifs = []

        notif = self.get_notification()
        while notif:
            notifs.append(notif)
            notif = self.get_notification()

        return notifs


# This is a replacement for the Mic object but it sends an email.
class EmailMic(object):
    prev = None

    def __init__(self, address, subject, *args, **kwargs):
        self._to = address
        self._subject = subject
        return

    @staticmethod
    @contextlib.contextmanager
    def special_mode(name, phrases):
        yield

    def wait_for_keyword(self, keyword="NAOMI"):
        if(self.passive_listen):
            return self.active_listen()
        else:
            return

    # This gets called if the handler is supposed to wait for input.
    @staticmethod
    def active_listen(timeout=3):
        #input_text = input("YOU: ")
        #unicodedata.normalize('NFD', input_text).encode('ascii', 'ignore')
        #self.prev = input_text
        return [""]

    def listen(self):
        return self.active_listen(timeout=3)

    def say(self, phrase, OPTIONS=None):
        app_utils.send_email(
            "Re: {}".format(self._subject),
            phrase,
            self._to
        )
