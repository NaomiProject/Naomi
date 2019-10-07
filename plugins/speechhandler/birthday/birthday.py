# -*- coding: utf-8 -*-
import datetime
import facebook
from collections import OrderedDict
from naomi import app_utils
from naomi import plugin
from naomi import profile


class BirthdayPlugin(plugin.SpeechHandlerPlugin):
    def __init__(self, *args, **kwargs):
        super(BirthdayPlugin, self).__init__(*args, **kwargs)
        _ = self.gettext
        self.settings = OrderedDict(
            [
                (
                    ("keys", "FB_TOKEN"), {
                        "title": _("Please enter Facebook token"),
                        "description": _("I can use your Facebook token to notify you when your friends have birthdays")
                    }
                )
            ]
        )

    def intents(self):
        _ = self.gettext
        return {
            'FBBirthdayIntent': {
                'templates': [
                    _("WHOSE BIRTHDAY IS IT TODAY"),
                    _("ARE THERE ANY BIRTHDAYS TODAY"),
                    _("DO ANY OF MY FRIENDS HAVE BIRTHDAYS TODAY")
                ],
                'action': self.handle
            }
        }

    def handle(self, intent, mic):
        """
        Responds to user-input, typically speech text, by listing the user's
        Facebook friends with birthdays today.

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
        oauth_access_token = profile.get(['keys', 'FB_TOKEN'])
        _ = self.gettext
        graph = facebook.GraphAPI(oauth_access_token)

        try:
            results = graph.request(
                "me/friends",
                args={'fields': 'id,name,birthday'}
            )
        except facebook.GraphAPIError:
            mic.say(
                " ".join([
                    _("I have not been authorized to query your Facebook."),
                    _("If you would like to check birthdays in the future,"),
                    _("please visit the Naomi dashboard.")
                ])
            )
            return
        except Exception:
            mic.say(
                " ".join([
                    _("I apologize,"),
                    _("there's a problem with that service at the moment.")
                ])
            )
            return

        needle = datetime.datetime.now(
            tz=app_utils.get_timezone()
        ).strftime("%m/%d")

        people = []
        for person in results['data']:
            try:
                if needle in person['birthday']:
                    people.append(person['name'])
            except Exception:
                continue

        if len(people) > 0:
            if len(people) == 1:
                output = _("%s has a birthday today.") % people[0]
            else:
                output = _(
                    "Your friends with birthdays today are {} and {}."
                ).format(", ".join(people[:-1]), people[-1])
        else:
            output = _("None of your friends have birthdays today.")

        mic.say(output)
