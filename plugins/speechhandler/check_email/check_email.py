# -*- coding: utf-8 -*-
import imaplib
import re
from naomi import app_utils
from naomi import plugin


class CheckEmailPlugin(plugin.SpeechHandlerPlugin):

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
            messages = app_utils.fetch_emails(filter="(UNSEEN)", limit=5)
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

        senders = [app_utils.get_sender(e) for e in messages]

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
