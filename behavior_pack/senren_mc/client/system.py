# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi
from senren_mc import config

ClientSystem = clientApi.GetClientSystemCls()


class StoryClientSystem(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        self.screen = None
        self.ready = False
        self.registered = False
        self.opening = False
        self.destroyed = False
        engine_namespace = clientApi.GetEngineNamespace()
        engine_system = clientApi.GetEngineSystemName()
        self.events = ((engine_namespace, engine_system, "UiInitFinished", self.OnUiReady),
                       (engine_namespace, engine_system, "OnKeyPressInGame", self.OnKey),
                       (config.NAMESPACE, config.SERVER_SYSTEM, config.OPEN_STORY_EVENT, self.OnOpenRequested))
        for event_namespace, event_system, event, callback in self.events:
            self.ListenForEvent(event_namespace, event_system, event, self, callback)

    def OnUiReady(self, args=None):
        if not self.registered:
            story_ok = clientApi.RegisterUI(config.NAMESPACE, config.STORY_UI,
                                            "senren_mc.client.screen.StoryScreen", "senren_ui.senren_screen")
            launcher_ok = clientApi.RegisterUI(config.NAMESPACE, config.LAUNCHER_UI,
                                               "senren_mc.client.launcher.LauncherScreen", "senren_ui.launcher")
            self.registered = bool(story_ok and launcher_ok)
        if not self.registered:
            print("[senren_mc] UI registration failed")
            return
        self.ready = True
        if clientApi.GetUI(config.NAMESPACE, config.LAUNCHER_UI) is None:
            launcher = clientApi.CreateUI(config.NAMESPACE, config.LAUNCHER_UI, {"isHud": 1})
            if launcher is None:
                print("[senren_mc] HUD button creation failed")

    def OpenStory(self):
        if self.destroyed or not self.ready or self.screen is not None or self.opening:
            return
        self.opening = True
        self.screen = clientApi.PushScreen(config.NAMESPACE, config.STORY_UI)
        self.opening = False
        if self.screen is None:
            print("[senren_mc] Story screen creation failed")

    def OnOpenRequested(self, args=None):
        self.OpenStory()

    def OnKey(self, args):
        if args.get("isDown") != "1":
            return
        key = args.get("key")
        if key == "117" and self.screen is None:
            self.OpenStory()
            return
        if self.screen is not None and clientApi.GetTopUI() == config.SCREEN_NAME:
            self.screen.HandleKey(key)

    def Destroy(self):
        if self.destroyed:
            return
        self.destroyed = True
        for event_namespace, event_system, event, callback in self.events:
            self.UnListenForEvent(event_namespace, event_system, event, self, callback)
        if self.screen is not None:
            self.screen.Release()
        self.screen = None
        self.ready = False
