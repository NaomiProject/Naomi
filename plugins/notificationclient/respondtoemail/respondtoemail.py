# -*- coding: utf-8 -*-
import contextlib
import random
from collections import OrderedDict
from naomi import app_utils
from naomi import plugin
from naomi import profile


class RespondToEmailPlugin(plugin.NotificationClientPlugin):
    def settings(self):
        _ = self.gettext
        return OrderedDict(
            [
                (
                    ('Safe Addresses',), {
                        'title': _('Safe email addresses for me to respond to'),
                        'description': "".join([
                            _('If you would like to be able to communicate with me over email or text messages, please enter a comma separated list of addresses that it is safe for me to respond to (otherwise, just leave this blank)'),
                        ]),
                        "return_type": "list"
                    }
                )
            ]
        )

    def __init__(self, *args, **kwargs):
        super(RespondToEmailPlugin, self).__init__(*args, **kwargs)
        # check to see if we can connect to an email account
        if(app_utils.check_imap_config()):
            self.gather = self.handle_email_notifications
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

    def handle_email_notifications(self, last_date):
        """Places new Gmail notifications in the Notifier's queue."""
        def handle_email(e):
            # if the subject line matches the first line of the email, then
            # discard the subject line. If not, then append the body to the
            # subject line.
            subject = e["Subject"]
            body = app_utils.get_message_text(e)
            if(body[:len(subject)] != subject):
                body = " ".join([subject, body])
            message = self._brain._intentparser.cleantext(body)
            keywords = profile.get(["keyword"], ['NAOMI'])
            if(isinstance(keywords, str)):
                keywords = [keywords]
            handleEmail = False
            respond_to_emails = profile.get(['Safe Addresses'], None)
            if(isinstance(respond_to_emails, list)):  # check respond_to_email exists
                # Lower case every member
                respond_to_emails = [email.lower() for email in respond_to_emails]
                if((len(respond_to_emails) == 0) or (app_utils.get_sender_email(e).lower() in respond_to_emails)):  # sender is okay
                    self._logger.info("sender okay")
                    if(any(x.upper() in message for x in keywords)):  # wake word detected
                        self._logger.info("wake word detected")
                        handleEmail = True
            if(handleEmail):
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
                        emailmic.say(
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

        self._logger.info("Checking email since {}".format(last_date))
        try:
            emails = app_utils.fetch_emails(since=last_date, email_filter="(UNSEEN)")
            self._logger.info("{} new emails".format(len(emails)))
            if emails:
                last_date = app_utils.get_most_recent_date(emails)
            for e in emails:
                handle_email(e)
        except Exception as ex:
            self._logger.warn(str(ex))

        return last_date


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
        # input_text = input("YOU: ")
        # unicodedata.normalize('NFD', input_text).encode('ascii', 'ignore')
        # self.prev = input_text
        return [""]

    def listen(self):
        return self.active_listen(timeout=3)

    def say(self, phrase, OPTIONS=None):
        app_utils.send_email(
            "Re: {}".format(self._subject),
            phrase,
            self._to
        )
