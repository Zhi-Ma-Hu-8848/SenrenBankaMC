# -*- coding: utf-8 -*-
"""Route the native /senren command to the invoking player's client."""
import mod.server.extraServerApi as serverApi
from senren_mc import config

ServerSystem = serverApi.GetServerSystemCls()


class StoryServerSystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        self.destroyed = False
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(),
                            "CustomCommandTriggerServerEvent", self, self.OnCommand)

    def OnCommand(self, args):
        if args.get("command") != config.OPEN_COMMAND:
            return
        player_id = args.get("origin", {}).get("entityId")
        if not player_id:
            args["return_failed"] = True
            args["return_msg_key"] = u"请由玩家在聊天栏输入 /senren".encode("utf-8")
            return
        self.NotifyToClient(player_id, config.OPEN_STORY_EVENT, {})
        args["return_msg_key"] = u"正在打开千恋＊万花".encode("utf-8")

    def Destroy(self):
        if self.destroyed:
            return
        self.destroyed = True
        self.UnListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(),
                              "CustomCommandTriggerServerEvent", self, self.OnCommand)
