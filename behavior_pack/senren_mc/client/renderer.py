# -*- coding: utf-8 -*-
"""Apply complete cue snapshots, including after arbitrary progress jumps."""

STAGE_ASPECT = 16.0 / 9.0


class StoryRenderer(object):
    def __init__(self, screen):
        self.screen = screen
        self.cue = None
        self.layout_key = None

    def Layout(self, mode, force=False):
        scene = "story" if mode == "choice" else mode
        if scene not in ("title", "story", "end"):
            return
        control = self.screen.Control
        path = "/root/" + scene
        width, height = control(path).GetSize()
        if width <= 0 or height <= 0:
            return
        key = (scene, width, height)
        if not force and self.layout_key == key:
            return
        self.layout_key = key
        stage_height = min(height, width / STAGE_ASPECT)
        stage_width = stage_height * STAGE_ASPECT
        stage = control(path + "/stage")
        stage.SetSize((stage_width, stage_height))
        stage.SetPosition(((width - stage_width) / 2, (height - stage_height) / 2))
        control(path + "/stage/background").SetSize((stage_width, stage_height))
        fill_width = max(width, height * STAGE_ASPECT)
        fill_height = fill_width / STAGE_ASPECT
        backdrop = control(path + "/backdrop")
        backdrop.SetSize((fill_width, fill_height))
        backdrop.SetPosition(((width - fill_width) / 2, (height - fill_height) / 2))
        if scene == "story" and self.cue is not None:
            self.ApplyVisuals(stage_width, stage_height)

    def Apply(self, cue):
        self.cue = cue
        control = self.screen.Control
        control("/root/story/stage/background").asImage().SetSprite(
            (u"textures/senren_mc/backgrounds/" + cue.background).encode("utf-8"))
        fill_texture = u"backgrounds/" + cue.background
        for visual in cue.visuals:
            if visual.get("full") and (visual["texture"].startswith("visuals/ev") or
                                       visual["texture"] == "visuals/white"):
                fill_texture = visual["texture"]
        control("/root/story/backdrop").asImage().SetSprite(
            (u"textures/senren_mc/backdrops/" + fill_texture).encode("utf-8"))
        self.Layout("story", force=True)

    def ApplyVisuals(self, width, height):
        control = self.screen.Control
        cue = self.cue
        for index in range(6):
            node = control("/root/story/stage/visual%d" % index)
            node.SetVisible(index < len(cue.visuals))
            if index >= len(cue.visuals):
                continue
            visual = cue.visuals[index]
            node.asImage().SetSprite((u"textures/senren_mc/" + visual["texture"]).encode("utf-8"))
            visual_height = height * visual["height"]
            visual_width = width if visual.get("full") else visual_height * visual["aspect"]
            node.SetSize((visual_width, visual_height))
            node.SetPosition((width * visual["x"] - visual_width / 2, height * visual["y"]))
            node.SetAlpha(visual.get("alpha", 1))
