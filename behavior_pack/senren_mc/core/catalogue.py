# -*- coding: utf-8 -*-
"""Stable, unrestricted line catalogue independent of the active branch."""
class StoryCatalogue(object):
    def __init__(self, document):
        self.rows = []
        self.routes = [choice["id"] for choice in document.get("choices", [])]
        groups = [(None, document["cues"])]
        groups += [(choice["id"], choice["cues"]) for choice in document.get("choices", [])]
        groups.append(("common", document.get("continuation", [])))
        for route, cues in groups:
            for cue in cues:
                self.rows.append({"id": cue["id"], "route": route, "speaker": cue["speaker"],
                                  "text": cue["text"], "number": len(self.rows) + 1})
        self.by_id = dict((row["id"], row) for row in self.rows)

    def page(self, page, count=5):
        start = max(0, page) * count
        return self.rows[start:start+count]
