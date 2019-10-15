# -*- coding: utf-8 -*-
import imaplib
import email
import re
from collections import OrderedDict
from dateutil import parser
from naomi import plugin
from naomi import profile


def get_sender(msg):
    """
        Returns the best-guess sender of an email.

        Arguments:
        email -- the email whose sender is desired

        Returns:
        Sender of the email.
    """
    sender = msg['From']
    m = re.match(r'(.*)\s<.*>', sender)
    if m:
        return m.group(1)
    return sender


def get_date(email):
    return parser.parse(email.get('date'))


def get_most_recent_date(emails):
    """
        Returns the most recent date of any email in the list provided.

        Arguments:
        emails -- a list of emails to check

        Returns:
        Date of the most recent email.
    """
    dates = [get_date(e) for e in emails]
    dates.sort(reverse=True)
    if dates:
        return dates[0]
    return None


class CheckEmailPlugin(plugin.SpeechHandlerPlugin):

    def settings(self):
        _ = self.gettext
        return OrderedDict(
            [
                (
                    ("email", "address"), {
                        "title": _("Please enter your email address"),
                        "description": _("I can use your email address to check your mail and send you notifications"),
                        "validation": "email"
                    }
                ),
                (
                    ("email", "imap", "server"), {
                        "title": _("Please enter your IMAP email server url"),
                        "description": _("I need to know the url of your email server if you want me to check your emails for you"),
                        "active": lambda: True if len(profile.get_profile_var(["email", "address"]).strip()) > 0 else False
                    }
                ),
                (
                    ("email", "imap", "port"), {
                        "title": _("Please enter your IMAP email server port"),
                        "description": _("I need to know I have the correct port to access your email"),
                        "default": "993",
                        "validation": "int",
                        "active": lambda: True if(len(profile.get_profile_var(["email", "address"]).strip()) > 0) and (len(profile.get_profile_var(["email", "imap"])) > 0) else False
                    }
                ),
                (
                    ("email", "username"), {
                        "title": _("Please enter your IMAP email server username"),
                        "description": _("Your username is normally either your full email address or just the part before the '@' symbol"),
                        "active": lambda: True if len(profile.get_profile_var(["email", "address"]).strip()) > 0 else False
                    }
                ),
                (
                    ("email", "password"), {
                        "type": "password",
                        "title": _("Please enter your IMAP email password"),
                        "description": _("I need your email address in order to check your emails"),
                        "active": lambda: True if(len(profile.get_profile_var(["email", "address"]).strip()) > 0) and (len(profile.get_profile_var(["email", "imap"])) > 0) else False
                    }
                )
            ]
        )

    def intents(self):
        _ = self.gettext
        return {
            'CheckEmailIntent': {
                'templates': [
                    _("READ MY EMAIL"),
                    _("CHECK MY INBOX"),
                    _("DO I HAVE ANY EMAIL"),
                    _("ARE THERE ANY NEW EMAILS")
                ],
                'action': self.handle
            }
        }

    @staticmethod
    def fetch_unread_emails(since=None, markRead=False, limit=None):
        """
            Fetches a list of unread email objects from a user's Email inbox.

            Arguments:
            since -- if provided, no emails before this date will be returned
            markRead -- if True, marks all returned emails as read in target
                        inbox

            Returns:
            A list of unread email objects.
        """
        host = profile.get_profile_var(['email', 'imap', 'server'])
        port = int(profile.get_profile_var(['email', 'imap', 'port'], "993"))
        conn = imaplib.IMAP4_SSL(host, port)
        conn.debug = 0

        password = profile.get_profile_password(['email', 'password'])
        conn.login(
            profile.get_profile_var(['email', 'username']),
            password
        )
        conn.select(readonly=(not markRead))

        msgs = []
        (retcode, messages) = conn.search(None, '(UNSEEN)')

        if retcode == 'OK' and messages != ['']:
            numUnread = len(messages[0].split(b' '))
            if limit and numUnread > limit:
                return numUnread

            for num in messages[0].split(b' '):
                # parse email RFC822 format
                ret, data = conn.fetch(num, '(RFC822)')
                raw_email = data[0][1]
                raw_email_str = raw_email.decode("utf-8")
                msg = email.message_from_string(raw_email_str)

                if not since or get_date(msg) > since:
                    msgs.append(msg)
        conn.close()
        conn.logout()

        return msgs

    def handle(self, intent, mic):
        """
        Responds to user-input, typically speech text, with a summary of
        the user's IMAP inbox, reporting on the number of unread emails
        in the inbox, as well as their senders.

        Arguments:
        intent -- intentparser result with the following layout:
            intent['action'] = the action to take when the intent is activated
            intent['input'] = the original words
            intent['matches'] = dictionary of lists with matching elements,
                each with a list of the actual words matched
            intent['score'] = how confident Naomi is that it matched the
                correct intent.
        mic -- used to interact with the user (for both input and output)
        """
        _ = self.gettext
        try:
            messages = self.fetch_unread_emails(limit=5)
        except imaplib.IMAP4.error:
            mic.say(
                _("I'm sorry. I'm not authenticated to work with your Email account.")
            )
            return

        if isinstance(messages, int):
            if messages == 0:
                response = _("You have no unread emails.")
            elif messages == 1:
                response = _("You have one unread email.")
            else:
                response = (
                    _("You have {} unread emails.").format(messages)
                )
            mic.say(response)
            return

        senders = [get_sender(e) for e in messages]

        if not senders:
            mic.say(_("You have no unread emails."))
        elif len(senders) == 1:
            mic.say(
                _("You have one unread email from {}.").format(senders[0])
            )
        else:
            response = _("You have {} unread emails.").format(
                len(senders)
            )
            unique_senders = list(set(senders))
            if len(unique_senders) > 1:
                response += " " + _("Senders include {} and {}").format(
                    ', '.join(unique_senders[:-1]),
                    unique_senders[-1]
                )
            else:
                response += " " + _("They are all from {}.").format(
                    unique_senders[0]
                )
            mic.say(response)
