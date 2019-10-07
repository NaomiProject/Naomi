# -*- coding: utf-8 -*-
import difflib
import logging
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
        self._autoplay = profile.get(['mpdclient', 'autoplay'], False)

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

    def intents(self):
        _ = self.gettext
        playlists = [pl.upper() for pl in self._music.get_playlists()]
        return {
            'MPDControlIntent': {
                'keywords': {
                    'PlayList': playlists
                },
                'templates': [
                    "PLAY SOMETHING",
                    "PLAY MUSIC",
                    "PLAY {PlayList}"
                ],
                'action': self.handle
            }
        }

    def handle(self, intent, mic):
        """
        Responds to user-input, typically speech text, by playing music

        Arguments:
            text -- user-input, typically transcribed speech
            mic -- used to interact with the user (for both input and output)
        """

        _ = self.gettext  # Alias for better readability

        self.say(mic, _("Wait, I'm starting the music mode."))

        phrases = [
            _('PLAY'),
            _('PAUSE'),
            _('STOP'),
            _('NEXT'),
            _('PREVIOUS'),
            _('LOUDER'),
            _('SOFTER'),
            _('PLAYLIST'),
            _('CLOSE'),
            _('EXIT')
        ]
        if(mic.passive_listen):
            # If we are using passive listening mode,
            # make sure naomi knows its keyword so it
            # does not confuse it with one of the commands
            if(mic._keyword not in phrases):
                phrases.append(mic._keyword)

        self._logger.debug('Loading playlists...')
        phrases.extend([pl.upper() for pl in self._music.get_playlists()])

        if self._autoplay:
            self._music.play()
            song = self._music.get_current_song()
            if song and not self._reticient:
                self.say(
                    mic,
                    _(
                        'Playing {song.title} by {song.artist}...'
                    ).format(song=song)
                )

        self._logger.debug('Starting music mode...')
        with mic.special_mode('music', phrases):
            self._logger.debug('Music mode started.')
            self.say(mic, _('Music mode started!'))
            mode_not_stopped = True
            while mode_not_stopped:
                if(mic.passive_listen):
                    texts = mic.wait_for_keyword()
                else:
                    mic.wait_for_keyword()

                    # Pause if necessary
                    playback_state = self._music.get_playback_state()
                    if playback_state == mpdclient.PLAYBACK_STATE_PLAYING:
                        self._music.pause()
                        texts = mic.active_listen()
                        self._music.play()
                    else:
                        texts = mic.active_listen()

                text = ''
                if texts:
                    text = ', '.join(texts).upper()

                if not text:
                    self.say(mic, _('Pardon?'))
                    continue

                mode_not_stopped = self.handle_music_command(text, mic)

        self.say(mic, _('Music Mode stopped!'))
        self._logger.debug("Music mode stopped.")

    def handle_music_command(self, command, mic):
        _ = self.gettext  # Alias for better readability

        if _('PLAYLIST').upper() in command:
            # Find playlist name
            texts = command.replace(_('PLAYLIST'), '').strip()
            playlists = self._music.get_playlists()
            playlists_upper = [pl.upper() for pl in playlists]
            matches = []
            for text in texts.split(', '):
                matches.extend(difflib.get_close_matches(text,
                                                         playlists_upper))
            if len(matches) > 0:
                playlist_index = playlists_upper.index(matches[0])
                playlist = playlists[playlist_index]
            else:
                playlist = None

            # Load playlist
            if playlist:
                playback_state = self._music.get_playback_state()
                self._music.load_playlist(playlist)
                self.say(mic, _('Playlist %s loaded.') % playlist)
                if playback_state == mpdclient.PLAYBACK_STATE_PLAYING:
                    self._music.play()
            else:
                self.say(
                    mic,
                    _("Sorry, I can't find a playlist with that name.")
                )
        elif _('STOP').upper() in command:
            self._music.stop()
            self.say(mic, _('Music stopped.'))
        elif _('PLAY').upper() in command:
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
        elif _('LOUDER').upper() in command:
            self.say(mic, _('Increasing volume.'))
            self._music.volume(10, relative=True)
        elif _('SOFTER').upper() in command:
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
        elif any(cmd.upper() in command for cmd in (_('CLOSE'), _('EXIT'))):
            if _('EXIT').upper() in command:
                self._music.stop()
                self.say(mic, _('Music stopped.'))
            return False

        return True

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
