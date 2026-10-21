# -*- coding: utf-8 -*-
from mod.common.mod import Mod
import mod.client.extraClientApi as clientApi
import mod.server.extraServerApi as serverApi
from senren_mc import config


@Mod.Binding(name=config.NAMESPACE, version="0.1.0")
class SenrenMod(object):
    @Mod.InitServer()
    def InitServer(self):
        serverApi.RegisterSystem(config.NAMESPACE, config.SERVER_SYSTEM,
                                 "senren_mc.server.system.StoryServerSystem")

    @Mod.InitClient()
    def InitClient(self):
        clientApi.RegisterSystem(config.NAMESPACE, config.CLIENT_SYSTEM,
                                 "senren_mc.client.system.StoryClientSystem")
