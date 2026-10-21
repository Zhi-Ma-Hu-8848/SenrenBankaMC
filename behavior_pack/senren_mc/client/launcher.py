# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi
from senren_mc import config

ScreenNode = clientApi.GetScreenNodeCls()


class LauncherScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)

    def Create(self):
        button = self.GetBaseUIControl("/open_story").asButton()
        button.AddTouchEventParams({"isSwallow": True})
        button.SetButtonTouchUpCallback(self.Open)

    def Open(self, args):
        system = clientApi.GetSystem(config.NAMESPACE, config.CLIENT_SYSTEM)
        if system is not None:
            system.OpenStory()
