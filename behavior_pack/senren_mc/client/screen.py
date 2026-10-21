# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi
from senren_mc import config
from senren_mc.core.story import StorySession
from senren_mc.data.prologue import DOCUMENT
from senren_mc.client.audio import StoryAudio
from senren_mc.client.renderer import StoryRenderer
from senren_mc.client.progress import ProgressPicker

ScreenNode = clientApi.GetScreenNodeCls()


class StoryScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        self.session = StorySession(DOCUMENT)
        self.mode = "title"
        self.started = False
        self.active = True
        self.released = False
        self.ui_ready = False
        self.history_end = 0
        self.controls = {}
        self.audio = None
        self.storage = None
        self.checkpoint = None
        self.status_frames = 0
        self.renderer = StoryRenderer(self)
        self.progress = ProgressPicker(self)

    def Control(self, path):
        if path not in self.controls:
            control = self.GetBaseUIControl(path)
            if control is None:
                raise RuntimeError("Missing senren UI control: " + path)
            self.controls[path] = control
        return self.controls[path]

    def Label(self, path, text):
        self.Control(path).asLabel().SetText(text.encode("utf-8"))

    def Bind(self, path, callback):
        button = self.Control(path).asButton()
        button.AddTouchEventParams({"isSwallow": True})
        button.SetButtonTouchUpCallback(callback)

    def Create(self):
        self.audio = StoryAudio()
        self.storage = clientApi.GetEngineCompFactory().CreateConfigClient(clientApi.GetLevelId())
        self.checkpoint = self.storage.GetConfigData(config.SAVE_KEY, False)
        actions = (
            ("/root/title/start", self.New), ("/root/title/resume", self.Continue),
            ("/root/title/close", self.Exit), ("/root/story/next", self.Next),
            ("/root/story/toolbar/previous", self.Previous),
            ("/root/story/toolbar/auto", self.Auto), ("/root/story/toolbar/log", self.History),
            ("/root/story/toolbar/replay", self.Replay), ("/root/story/toolbar/mute", self.Mute),
            ("/root/story/toolbar/save", self.SaveButton), ("/root/story/toolbar/menu", self.Menu),
            ("/root/history/older", self.Older), ("/root/history/newer", self.Newer),
            ("/root/history/back", self.BackFromHistory), ("/root/end/restart", self.New),
            ("/root/end/menu", self.Menu), ("/root/end/close", self.Exit))
        for path, callback in actions:
            self.Bind(path, callback)
        self.Bind("/root/choice/honest", self.ChooseHonest)
        self.Bind("/root/choice/dodge", self.ChooseDodge)
        self.progress.Bind()
        self.ShowTitle()
        self.ui_ready = True

    def ShowMode(self, mode):
        self.mode = mode
        for candidate in ("title", "story", "history", "end", "choice", "progress"):
            self.Control("/root/" + candidate).SetVisible(candidate == mode or (candidate == "story" and mode == "choice"))
        self.Control("/root/story/toolbar").SetVisible(mode == "story")
        self.renderer.Layout(mode)

    def ShowTitle(self):
        self.ShowMode("title")
        valid = StorySession(DOCUMENT).restore(self.checkpoint)
        self.Control("/root/title/resume").SetVisible(valid)

    def New(self, args=None):
        self.session.reset()
        self.Start()

    def Continue(self, args=None):
        if self.session.restore(self.checkpoint):
            self.Start()

    def Start(self):
        self.started = True
        self.audio.component.DisableOriginMusic(True)
        self.ShowMode("story")
        self.RenderCue()
        if self.session.awaiting_choice:
            self.ShowMode("choice")

    def RenderCue(self):
        cue = self.session.cue
        self.renderer.Apply(cue)
        self.Label("/root/story/dialogue/speaker", cue.speaker or u"旁白")
        self.Label("/root/story/progress", u"1-1 · 亚瑟王    %03d / %03d" %
                   (self.session.catalogue.by_id[cue.id]["number"], len(self.session.catalogue.rows)))
        self.audio.Apply(cue)
        self.RenderText()
        self.RenderSettings()
        self.Save()

    def RenderText(self):
        self.Label("/root/story/dialogue/text", self.session.visible_text)
        self.Label("/root/story/dialogue/hint", u"点击继续  ▷" if self.session.complete else u"点击显示全文")

    def RenderSettings(self):
        self.Label("/root/story/toolbar/auto/label", u"自动 ●" if self.session.auto else u"自动")
        self.Label("/root/story/toolbar/mute/label", u"声音 ×" if self.audio.muted else u"声音")

    def Next(self, args=None):
        if self.mode != "story":
            return
        self.OnAdvance(self.session.advance())

    def OnAdvance(self, result):
        if result == "cue":
            self.RenderCue()
        elif result == "ended":
            self.Save()
            self.audio.Close()
            self.ShowMode("end")
        elif result == "choice":
            self.Save()
            self.ShowMode("choice")
        elif result in ("reveal", "text"):
            self.RenderText()

    def ChooseHonest(self, args=None):
        self.Choose("*001_01A")

    def ChooseDodge(self, args=None):
        self.Choose("*001_01B")

    def Choose(self, route):
        if self.mode == "choice" and self.session.choose(route):
            self.ShowMode("story")
            self.RenderCue()

    def Previous(self, args=None):
        self.session.auto = False
        if self.mode == "story" and self.session.previous():
            self.RenderCue()

    def Auto(self, args=None):
        self.session.auto = not self.session.auto
        self.RenderSettings()

    def Replay(self, args=None):
        self.audio.Replay()
        self.Status(u"重播当前配音" if self.session.cue.voice else u"这句没有配音")

    def Mute(self, args=None):
        self.audio.ToggleMute(self.session.cue)
        self.RenderSettings()

    def Save(self):
        if not self.started:
            return False
        checkpoint = self.session.snapshot()
        if self.storage.SetConfigData(config.SAVE_KEY, checkpoint, False):
            self.checkpoint = checkpoint
            return True
        self.Status(u"进度保存失败，请检查游戏日志")
        print("[senren_mc] Checkpoint save failed")
        return False

    def SaveButton(self, args=None):
        if self.Save():
            self.Status(u"阅读进度已保存")

    def Status(self, text):
        self.Label("/root/story/status", text)
        self.status_frames = 75

    def History(self, args=None):
        self.session.auto = False
        self.history_end = self.session.index
        self.ShowMode("history")
        self.RenderHistory()

    def RenderHistory(self):
        text, start, end = self.session.history(self.history_end, 3)
        self.Label("/root/history/content", text)
        self.Label("/root/history/page", u"已读记录  %d—%d / %d" % (start+1, end+1, self.session.index+1))

    def Older(self, args=None):
        self.history_end = max(0, self.history_end - 3)
        self.RenderHistory()

    def Newer(self, args=None):
        self.history_end = min(self.session.index, self.history_end + 3)
        self.RenderHistory()

    def BackFromHistory(self, args=None):
        self.ShowMode("story")
        self.RenderSettings()

    def Menu(self, args=None):
        self.session.auto = False
        self.Save()
        self.audio.Close()
        self.ShowTitle()

    def Exit(self, args=None):
        clientApi.PopScreen()

    def HandleKey(self, key):
        if self.mode == "title":
            if key == "80":
                self.progress.Open()
            elif key == "83":
                self.New()
            elif key == "67":
                self.Continue()
        elif self.mode == "progress":
            self.progress.HandleKey(key)
        elif self.mode == "story":
            if key in ("32", "13", "39"):
                self.Next()
            elif key == "37":
                self.Previous()
            elif key == "65":
                self.Auto()
            elif key == "72":
                self.History()
            elif key == "80":
                self.progress.Open()
            elif key in ("77", "27"):
                self.Menu()
        elif self.mode == "end" and key in ("80", "77", "27"):
            self.Menu()
        elif self.mode == "history" and key in ("72", "27"):
            self.BackFromHistory()
        elif self.mode == "choice" and key in ("49", "50"):
            self.ChooseHonest() if key == "49" else self.ChooseDodge()

    def Update(self):
        if not self.ui_ready or not self.active:
            return
        self.renderer.Layout(self.mode)
        if self.mode != "story":
            return
        self.OnAdvance(self.session.tick())
        if self.status_frames > 0:
            self.status_frames -= 1
            if self.status_frames == 0:
                self.Label("/root/story/status", u"")

    def OnActive(self):
        self.active = True

    def OnDeactive(self):
        self.active = False

    def Release(self):
        if self.released:
            return
        self.released = True
        if self.storage is not None:
            self.Save()
        if self.audio is not None:
            self.audio.Close()

    def Destroy(self):
        self.Release()
        system = clientApi.GetSystem(config.NAMESPACE, config.CLIENT_SYSTEM)
        if system is not None and system.screen is self:
            system.screen = None
