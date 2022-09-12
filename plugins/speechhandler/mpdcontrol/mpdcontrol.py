# -*- coding: utf-8 -*-
import difflib
import logging
from collections import OrderedDict
from naomi import plugin
from naomi import profile
from . import mpdclient


class MPDControlPlugin(plugin.SpeechHandlerPlugin):

    def __init__(self, *args, **kwargs):
        super(MPDControlPlugin, self).__init__(*args, **kwargs)
        self._logger = logging.getLogger(__name__)

        server = profile.get(['mpdclient', 'server'], 'localhost')
        try:
            port = int(profile.get(['mpdclient', 'port'], 6600))
        except ValueError:
            port = 6600
            self._logger.warning(
                "Configured port is invalid, using %d instead",
                port
            )

        password = profile.get(['mpdclient', 'password'], '')

        # In reticent mode Naomi is quieter.
        self._reticient = profile.get_profile_flag(
            ['mpdclient', 'reticient'],
            False
        )

        self._music = mpdclient.MPDClient(
            server=server,
            port=port,
            password=password
        )

    def settings(self):
        _ = self.gettext
        return OrderedDict(
            {
                ('mpdclient', 'server'): {
                    "title": _("MPD Server"),
                    "description": _("If you have set up an MPD server, please enter it here."),
                    "default": "localhost"
                },
                ('mpdclient', 'port'): {
                    "title": _("MPD Port"),
                    "description": _("What port should I use to contact MPD on that server?"),
                    "default": 6600
                },
                ('mpdclient', 'reticent'): {
                    "type": "boolean",
                    "title": "Should I try to be quiet while music is playing?",
                    "default": False
                }
            }
        )

    def intents(self):
        playlists = [pl.upper() for pl in self._music.get_playlists()]
        return {
            'MPDControlIntent': {
                'locale': {
                    'en-US': {
                        'keywords': {
                            'PlayList': playlists
                        },
                        'templates': [
                            "PLAY SOMETHING",
                            "PLAY MUSIC",
                            "PLAY {PlayList}",
                            "PLAY NEXT",
                            "PLAY PREVIOUS",
                            "PAUSE",
                            "RESUME",
                            "STOP PLAYING",
                            "INCREASE VOLUME",
                            "DECREASE VOLUME"
                        ]
                    },
                    'fr-FR': {
                        'keywords': {
                            'PlayList': playlists
                        },
                        'templates': [
                            "JOUER QUELQUE CHOSE",
                            "JOUER DE LA MUSIQUE",
                            "JOUER {PlayList}"
                        ]
                    },
                    'de-DE': {
                        'keywords': {
                            'PlayList': playlists
                        },
                        'templates': [
                            "SPIELEN SIE ETWAS",
                            "SPIELEN MUSIK",
                            "SPIELE {PlayList}"
                        ]
                    }
                },
                'action': self.handle
            }
        }

    def handle(self, intent, mic):
        """
        Responds to user-input, typically speech text, by playing music

        Arguments:
            intent -- the returned intent object
            mic -- used to interact with the user (for both input and output)
        """
        _ = self.gettext  # Alias for better readability
        command = intent['input']

        if('PlayList' in intent['matches']):
            playlist = intent['matches']['PlayList'][0]
            print("Loading playlist {}".format(playlist))
            self.load_playlist(playlist)
            self.say(mic, _('Playlist %s loaded.') % playlist)
            self._music.play()

            self._music.play()
            song = self._music.get_current_song()
            if song and not self._reticient:
                self.say(
                    mic,
                    _(
                        'Playing {song.title} by {song.artist}...'
                    ).format(song=song)
                )

        elif _('STOP').upper() in command:
            self.stop(intent, mic)
        elif _('PLAY').upper() in command or _('RESUME').upper() in command:
            self._music.play()
            song = self._music.get_current_song()
            if song and not self._reticient:
                self.say(
                    mic,
                    _(
                        'Playing {song.title} by {song.artist}...'
                    ).format(song=song)
                )
        elif _('PAUSE').upper() in command:
            playback_state = self._music.get_playback_state()
            if playback_state == mpdclient.PLAYBACK_STATE_PLAYING:
                self._music.pause()
                self.say(mic, _('Music paused.'))
            else:
                self.say(mic, _('Music is not playing.'))
        elif _('LOUDER').upper() in command or (_('INCREASE').upper() in command and _('VOLUME').upper() in command):
            self.say(mic, _('Increasing volume.'))
            self._music.volume(10, relative=True)
        elif _('SOFTER').upper() in command or (_('DECREASE').upper() in command and _('VOLUME').upper() in command):
            mic.say(_('Decreasing volume.'))
            self._music.volume(-10, relative=True)
        elif any(cmd.upper() in command for cmd in (
                _('NEXT'), _('PREVIOUS'))):
            if _('NEXT').upper() in command:
                self.say(mic, _('Next song'))
                self._music.play()  # backwards necessary to get mopidy to work
                self._music.next()
            else:
                self.say(mic, _('Previous song'))
                self._music.play()  # backwards necessary to get mopidy to work
                self._music.previous()
            song = self._music.get_current_song()
            if song and not self._reticient:
                self.say(
                    mic,
                    _(
                        'Playing {song.title} by {song.artist}...'
                    ).format(song=song)
                )
        return True

    def stop(self, intent, mic):
        _ = self.gettext  # Alias for better readability
        playback_state = self._music.get_playback_state()
        # stop playback even if playback appears to already be stopped
        self._music.stop()
        # if music is playing or paused, tell the user that playback is stopped
        if playback_state != mpdclient.PLAYBACK_STATE_STOPPED:
            self.say(mic, _('Music stopped.'))

    def load_playlist(self, playlist):
        playlists = self._music.get_playlists()
        playlists_upper = [pl.upper() for pl in playlists]
        matches = difflib.get_close_matches(
            playlist,
            playlists_upper
        )
        if len(matches) > 0:
            playlist_index = playlists_upper.index(matches[0])
            playlist = playlists[playlist_index]

        self._music.load_playlist(playlist)

    # This is a special say mode for MPDClient
    # If playback is occurring, pause it before speaking
    # This is especially important when using the alsa engine
    # since that engine does not seem to be able to play two
    # streams of audio simultaneously
    def say(self, mic, text):
        playback_state = self._music.get_playback_state()
        if playback_state == mpdclient.PLAYBACK_STATE_PLAYING:
            self._music.pause()
            mic.say(text)
            self._music.play()
        else:
            mic.say(text)
