# -*- coding: utf-8 -*-
import collections
import urllib
import feedparser
from naomi import plugin
from naomi import profile
from naomi import app_utils


FEED_URL = 'https://news.google.com/news/feeds'
Article = collections.namedtuple('Article', ['title', 'link'])


def get_top_articles(language='en', num_headlines=5):
    feed = feedparser.parse("{url}?{query}".format(
        url=FEED_URL,
        query=urllib.parse.urlencode({
            'ned': language,
            'output': 'rss',
        })))

    articles = []
    for entry in feed.entries:
        # Remove News source
        title = entry.title.rsplit(' - ', 1)[0].strip()
        # Skip headlines that aren't complete
        if title.endswith('...'):
            continue
        # Remove '+++'
        title = ''.join([s.strip() for s in title.split('+++')])

        try:
            link = urllib.parse.parse_qs(
                urllib.parse.urlsplit(entry.link).query)['url'][0]
        except Exception:
            link = entry['link']
        articles.append(Article(title=title, link=link))
        if len(articles) >= num_headlines:
            break

    return articles


class NewsPlugin(plugin.SpeechHandlerPlugin):
    def intents(self):
        return {
            'NewsIntent': {
                'locale': {
                    'en-US': {
                        'templates': [
                            "READ THE NEWS",
                            "WHAT IS IN THE NEWS",
                            "WHAT IS HAPPENING IN THE NEWS",
                            "WHAT ARE TODAY'S HEADLINES"
                        ]
                    },
                    'fr-FR': {
                        'templates': [
                            "LIRE LES NOUVELLES",
                            "CE QUI EST DANS LES NOUVELLES",
                            "CE QUI SE PASSE DANS LES NOUVELLES",
                            "QUELS SONT LES TITRES D'AUJOURD'HUI"
                        ]
                    },
                    'de-DE': {
                        'templates': [
                            "LIES DIE NACHRICHTEN",
                            "WAS IST IN DEN NACHRICHTEN",
                            "WAS PASSIERT IN DEN NACHRICHTEN",
                            "WAS SIND HEUTE SCHLAGZEILEN"
                        ]
                    }
                },
                'action': self.handle
            }
        }

    def handle(self, text, mic):
        """
        Responds to user-input, typically speech text, with a summary of
        the day's top news headlines, sending them to the user over email
        if desired.

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        """
        _ = self.gettext
        mic.say(self.gettext("Pulling up the news..."))

        lang = profile.get(['language'], 'en-US').split('-')[0]

        articles = get_top_articles(language=lang, num_headlines=5)
        if len(articles) == 0:
            mic.say(
                _("Sorry, I'm unable to get the latest headlines right now.")
            )
            return
        del articles[0]  # fixing "This RSS feed URL is deprecated"
        text = _('These are the current top headlines...')
        text += ' '
        text += '... '.join(
            '%d) %s' % (i, a.title)
            for i, a in enumerate(articles, start=1)
        )
        mic.say(text)

        email = profile.get(['email', 'address'])
        if not email:
            return

        if profile.get_profile_flag(['allows_email'], False):

            mic.say(_('Would you like me to send you these articles?'))

            answers = mic.active_listen()
            if any(
                self.gettext('YES').upper(
                ) in answer.upper(
                ) for answer in answers
            ):
                mic.say(self.gettext("Sure, just give me a moment."))
                SUBJECT = self.gettext("Your Top Headlines")
                email_text = self.make_email_text(articles)
                email_sent = app_utils.email_user(
                    SUBJECT=SUBJECT,
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
                mic.say(self.gettext("Okay, I will not send any articles."))

    def make_email_text(self, articles):
        text = self.gettext('These are the articles you requested:')
        text += '\n\n'
        del articles[1]  # to fix 'This RSS feed URL is deprecated'
        for article in articles:
            text += '- %s\n  %s\n' % (article.title, article.link)
        return text
