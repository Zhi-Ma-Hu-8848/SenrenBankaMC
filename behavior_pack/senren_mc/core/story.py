# -*- coding: utf-8 -*-
"""Engine-independent visual novel state; all display text stays Unicode."""
from senren_mc.core.catalogue import StoryCatalogue


class Cue(object):
    def __init__(self, document):
        self.id = document["id"]
        self.speaker = document["speaker"]
        self.text = document["text"]
        self.background = document["background"]
        self.character = document.get("character", "")
        self.visuals = document.get("visuals", [])
        self.voice = document.get("voice", "")
        self.voices = document.get("voices", [self.voice] if self.voice else [])
        self.voice_frames = int(document.get("voice_seconds", 0) * 30)
        self.music = document.get("music", "")
        self.ambience = document.get("ambience", "")
        self.effect = document.get("effect", "")


class StorySession(object):
    CHARS_PER_SECOND = 32.0

    def __init__(self, document):
        self.story_id = document["id"]
        self.legacy_ids = document.get("legacy_ids", [])
        self.catalogue = StoryCatalogue(document)
        self.prefix = [Cue(row) for row in document["cues"]]
        self.choices = dict((row["id"], [Cue(cue) for cue in row["cues"]])
                            for row in document.get("choices", []))
        self.continuation = [Cue(row) for row in document.get("continuation", [])]
        all_cues = self.prefix + self.continuation + [cue for branch in self.choices.values() for cue in branch]
        if not self.prefix or len(set(cue.id for cue in all_cues)) != len(all_cues):
            raise ValueError("Story needs non-empty, unique cue IDs")
        self.cues = self.prefix
        self.route = None
        self.awaiting_choice = False
        self.index = 0
        self.revealed = 0.0
        self.age_frames = 0
        self.auto = False
        self.ended = False

    @property
    def cue(self):
        return self.cues[self.index]

    @property
    def complete(self):
        return int(self.revealed) >= len(self.cue.text)

    @property
    def visible_text(self):
        return self.cue.text[:int(self.revealed)]

    def reset(self):
        self.auto = False
        self.cues = self.prefix
        self.route = None
        self.goto(0)

    def goto(self, index):
        if not 0 <= index < len(self.cues):
            return False
        self.index = index
        self.revealed = 0.0
        self.age_frames = 0
        self.ended = False
        self.awaiting_choice = False
        return True

    def advance(self):
        if self.ended:
            return "ended"
        if self.awaiting_choice:
            return "choice"
        if not self.complete:
            self.revealed = float(len(self.cue.text))
            return "reveal"
        if self.index + 1 == len(self.cues):
            if self.choices and self.route is None:
                self.awaiting_choice = True
                self.auto = False
                return "choice"
            self.ended = True
            self.auto = False
            return "ended"
        self.goto(self.index + 1)
        return "cue"

    def choose(self, route):
        if not self.awaiting_choice or route not in self.choices:
            return False
        self.route = route
        self.cues = self.prefix + self.choices[route] + self.continuation
        return self.goto(len(self.prefix))

    def previous(self):
        if self.index == 0:
            return False
        return self.goto(self.index - 1)

    def seek(self, cue_id):
        row = self.catalogue.by_id.get(cue_id)
        if row is None:
            return False
        route = row["route"]
        if route == "common":
            route = self.route or self.catalogue.routes[0]
        candidates = self.prefix if route is None else self.prefix + self.choices[route] + self.continuation
        for index, cue in enumerate(candidates):
            if cue.id == cue_id:
                self.route = route
                self.cues = candidates
                self.auto = False
                return self.goto(index)
        return False

    def tick(self):
        if self.ended or self.awaiting_choice:
            return "idle"
        before = int(self.revealed)
        self.age_frames += 1
        self.revealed = min(float(len(self.cue.text)), self.revealed + self.CHARS_PER_SECOND / 30)
        reading_frames = int(len(self.cue.text) * 30 / self.CHARS_PER_SECOND) + 60
        if self.auto and self.complete and self.age_frames >= max(reading_frames, self.cue.voice_frames + 15):
            return self.advance()
        return "text" if int(self.revealed) != before else "idle"

    def snapshot(self):
        return {"schema": 2, "story_id": self.story_id, "cue_id": self.cue.id,
                "finished": self.ended, "route": self.route, "awaiting_choice": self.awaiting_choice}

    def restore(self, data):
        if not isinstance(data, dict) or data.get("schema") != 2:
            return False
        if data.get("story_id") not in [self.story_id] + self.legacy_ids:
            return False
        route = data.get("route")
        if route is not None and route not in self.choices:
            return False
        candidates = self.prefix if route is None else self.prefix + self.choices[route] + self.continuation
        for index, cue in enumerate(candidates):
            if cue.id == data.get("cue_id"):
                self.cues = candidates
                self.route = route
                self.auto = False
                self.goto(index)
                self.awaiting_choice = bool(data.get("awaiting_choice") and route is None and index == len(self.prefix)-1)
                return True
        return False

    def history(self, end_index=None, count=5):
        end = self.index if end_index is None else max(0, min(self.index, end_index))
        start = max(0, end - count + 1)
        lines = []
        for cue in self.cues[start:end+1]:
            name = (cue.speaker + u"：") if cue.speaker else u""
            lines.append(name + cue.text)
        return u"\n\n".join(lines), start, end
