# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi


class StoryAudio(object):
    def __init__(self):
        self.component = clientApi.GetEngineCompFactory().CreateCustomAudio(clientApi.GetLevelId())
        self.voice = ""
        self.voices = []
        self.music = ""
        self.ambience = ""
        self.effect = ""
        self.muted = False
        self.errors = []
        self.component.DisableOriginMusic(True)

    @staticmethod
    def SoundName(name):
        return (u"senren_mc." + name).encode("utf-8")

    def Stop(self, name):
        if name:
            self.component.StopCustomMusic(self.SoundName(name), 0)

    def PlayLocal(self, name, volume, loop=False):
        result = self.component.PlayCustomMusic(self.SoundName(name), (0, 0, 0),
                                                volume, 1, loop, clientApi.GetLocalPlayerId())
        if result in ("-1", "-2", "-3", "-4", "-5", "-6", -1, -2, -3, -4, -5, -6):
            self.errors.append((name, result))
            print("[senren_mc] Sound failed: %s (%s)" % (name, result))

    def Apply(self, cue, replay_voice=True, play_effect=True):
        for voice in self.voices:
            self.Stop(voice)
        self.Stop(self.effect)
        self.voice = cue.voice
        self.voices = cue.voices
        self.effect = cue.effect if play_effect else ""
        if cue.music != self.music:
            self.Stop(self.music)
            self.music = cue.music
            if self.music and not self.muted:
                if not self.component.PlayGlobalCustomMusic(self.SoundName(self.music), 0.45, True):
                    print("[senren_mc] Background music failed: %s" % self.music)
        if cue.ambience != self.ambience:
            self.Stop(self.ambience)
            self.ambience = cue.ambience
            if self.ambience and not self.muted:
                self.PlayLocal(self.ambience, 0.38, True)
        if self.muted:
            return
        if replay_voice:
            for voice in self.voices:
                self.PlayLocal(voice, 1.0)
        if self.effect:
            self.PlayLocal(self.effect, 0.7)

    def Replay(self):
        for voice in self.voices:
            self.Stop(voice)
            if not self.muted:
                self.PlayLocal(voice, 1.0)

    def ToggleMute(self, cue):
        muted = not self.muted
        self.Close(restore_origin=False)
        self.muted = muted
        self.component.DisableOriginMusic(True)
        self.Apply(cue, replay_voice=False, play_effect=False)

    def Close(self, restore_origin=True):
        for name in self.voices + [self.music, self.ambience, self.effect]:
            self.Stop(name)
        self.voice = self.music = self.ambience = self.effect = ""
        self.voices = []
        if restore_origin:
            self.component.DisableOriginMusic(False)
