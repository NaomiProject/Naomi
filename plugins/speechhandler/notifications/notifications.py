# -*- coding: utf-8 -*-
import facebook
from collections import OrderedDict
from naomi import plugin
from naomi import profile


class NotificationsPlugin(plugin.SpeechHandlerPlugin):
    def settings(self):
        _ = self.gettext
        return OrderedDict(
            [
                (
                    ("keys", "FB_TOKEN"), {
                        "title": _("Please enter Facebook token"),
                        "description": _("I can use your Facebook token to check for incoming notifications")
                    }
                )
            ]
        )

    def intents(self):
<<<<<<< HEAD
        _ = self.gettext
        return {
            'NotificationsIntent': {
                'templates': [
                    _("DO I HAVE ANY FACEBOOK NOTIFICATIONS"),
                    _("CHECK MY NOTIFICATIONS")
                ],
=======
        return {
            'NotificationsIntent': {
                'locale': {
                    'en-US': {
                        'templates': [
                            "DO I HAVE ANY FACEBOOK NOTIFICATIONS",
                            "CHECK MY NOTIFICATIONS"
                        ]
                    },
                    'fr-FR': {
                        'templates': [
                            "AI-JE DES NOTIFICATIONS FACEBOOK",
                            "CONSULTEZ MES NOTIFICATIONS"
                        ]
                    },
                    'de-DE': {
                        'templates': [
                            "HABE ICH EINE FACEBOOK-MITTEILUNG",
                            "PRÜFEN SIE MEINE MITTEILUNGEN"
                        ]
                    }
                },
>>>>>>> 4807170d0d65eecc9e80d62e2084e7482de024c8
                'action': self.handle
            }
        }

    def handle(self, intent, mic):
        """
        Responds to user-input, typically speech text, with a summary of
        the user's Facebook notifications, including a count and details
        related to each individual notification.

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        """
        _ = self.gettext
        oauth_access_token = profile.get(['keys', 'FB_TOKEN'])

        graph = facebook.GraphAPI(oauth_access_token)

        try:
            results = graph.request("me/notifications")
        except facebook.GraphAPIError:
            mic.say(
                "".join([
                    _("I have not been authorized to query your Facebook. If"),
                    _("you would like to check your notifications in the"),
                    _("future, please visit the Naomi dashboard.")
                ])
            )
            return
        except Exception:
            mic.say(
                _("I apologize, I can't access Facebook at the moment.")
            )

        if not len(results['data']):
            mic.say(_("You have no Facebook notifications."))
            return

        updates = []
        for notification in results['data']:
            updates.append(notification['title'])

        count = len(results['data'])
        if count == 0:
            mic.say(_("You have no Facebook notifications."))
        elif count == 1:
            mic.say(_("You have one Facebook notification."))
        else:
            mic.say(
                _("You have {} Facebook notifications.").format(count)
            )

        if count > 0:
            mic.say("%s." % " ".join(updates))

        return
