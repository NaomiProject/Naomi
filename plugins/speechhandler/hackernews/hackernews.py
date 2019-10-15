# -*- coding: utf-8 -*-
import collections
import requests
from naomi import app_utils
from naomi import plugin
from naomi import profile

HN_TOPSTORIES_URL = 'https://hacker-news.firebaseio.com/v0/topstories.json'
HN_ITEM_URL = 'https://hacker-news.firebaseio.com/v0/item/%d.json'

Article = collections.namedtuple('Article', ['title', 'link'])


def get_top_articles(num_headlines=5):
    r = requests.get(HN_TOPSTORIES_URL)
    item_ids = r.json()
    articles = []
    for i, item_id in enumerate(item_ids, start=1):
        r = requests.get(HN_ITEM_URL % item_id)
        item = r.json()
        try:
            articles.append(Article(title=item['title'], link=item['url']))
        except KeyError as e:
            print(e)
        if i >= num_headlines:
            break
    return articles


class HackerNewsPlugin(plugin.SpeechHandlerPlugin):
    def intents(self):
        return {
            'HackerNewsIntent': {
                'templates': [
                    "READ HACKER NEWS",
                    "WHAT'S IN HACKER NEWS"
                ],
                'action': self.handle
            }
        }

    def handle(self, text, mic):
        """
        Responds to user-input, typically speech text, with a summary of
        the day's top news headlines, sending them to the user over email
        if desired.

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
        num_headlines = profile.get(['hacker-news', 'num-headlines'], 4)

        mic.say(
            _("Getting the top {} stories from Hacker News...").format(
                num_headlines
            )
        )

        articles = get_top_articles(num_headlines=num_headlines)
        if len(articles) == 0:
            mic.say(
                " ".join([
                    _("Sorry, I'm unable to get the top stories from"),
                    _("Hacker News right now.")
                ])
            )
            return

        text = _('These are the current top stories... ')
        text += '... '.join(
            f'{i}) {a.title}' for i, a in enumerate(articles, start=1)
        )
        mic.say(text)

        if profile.get_profile_flag(['prefers_email']):
            mic.say(_('Would you like me to send you these articles?'))

            answers = mic.active_listen()
            if any(
                _('YES').upper(
                ) in answer.upper(
                ) for answer in answers
            ):
                mic.say(_("Sure, just give me a moment."))
                email_text = self.make_email_text(articles)
                email_sent = app_utils.email_user(
                    SUBJECT=_("Top Stories from Hacker News"),
                    BODY=email_text
                )
                if email_sent:
                    mic.say(
                        _("Okay, I've sent you an email.")
                    )
                else:
                    mic.say(
                        _("Sorry, I'm having trouble sending you these articles.")
                    )
            else:
                mic.say(_("Okay, I will not send any articles."))

    def make_email_text(self, articles):
        _ = self.gettext
        text = _('These are the Hacker News articles you requested:')
        text += '\n\n'
        for article in articles:
            text += '- %s\n  %s\n' % (article.title, article.link)
        return text
