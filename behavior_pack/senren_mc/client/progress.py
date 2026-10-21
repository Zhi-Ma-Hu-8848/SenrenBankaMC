# -*- coding: utf-8 -*-
"""Native progress menu using the game's text input control."""
class ProgressPicker(object):
    SHORTCUTS = ("intro_001", "intro_048", "walk_090", "walk_143",
                 "walk_340", "walk_439", "walk_568", "walk_669")

    def __init__(self, screen):
        self.screen = screen
        self.catalogue = screen.session.catalogue
        self.page = 0

    def Bind(self):
        screen = self.screen
        screen.Bind("/root/title/progress", self.Open)
        for i in range(5):
            screen.Bind("/root/progress/row%d" % i, lambda args, row=i: self.Row(row))
        for i in range(8):
            screen.Bind("/root/progress/scene%d" % i, lambda args, row=i: self.Jump(self.SHORTCUTS[row]))
        screen.Bind("/root/progress/go", self.Go)
        screen.Bind("/root/progress/older", lambda args: self.Page(-1))
        screen.Bind("/root/progress/newer", lambda args: self.Page(1))
        screen.Bind("/root/progress/back", lambda args: screen.ShowTitle())

    def Open(self, args=None):
        self.screen.session.auto = False
        self.screen.Save()
        self.screen.audio.Close()
        self.page = (self.catalogue.by_id[self.screen.session.cue.id]["number"] - 1) // 5
        self.screen.Control("/root/progress/number").asTextEditBox().SetEditText("")
        self.screen.ShowMode("progress")
        self.Render()

    def Render(self):
        rows = self.catalogue.page(self.page)
        for i in range(5):
            path = "/root/progress/row%d" % i
            self.screen.Control(path).SetVisible(i < len(rows))
            if i < len(rows):
                row = rows[i]
                excerpt = row["text"].replace(u"\n", u" ")
                name = row["speaker"] + u"：" if row["speaker"] else u""
                self.screen.Label(path + "/label", u"%03d  %s%s" % (row["number"], name, excerpt[:24]))
        self.screen.Label("/root/progress/page", u"第 %d / %d 页 · 共 %d 句" %
                          (self.page + 1, (len(self.catalogue.rows) + 4)//5, len(self.catalogue.rows)))

    def Page(self, direction):
        self.page = max(0, min((len(self.catalogue.rows)-1)//5, self.page + direction))
        self.Render()

    def Go(self, args=None):
        text = self.screen.Control("/root/progress/number").asTextEditBox().GetEditText()
        text = text.strip() if text else ""
        valid = 0 < len(text) <= 3 and all(char in "0123456789" for char in text)
        number = int(text) if valid else 0
        if 1 <= number <= len(self.catalogue.rows):
            self.Jump(self.catalogue.rows[number-1]["id"])
        else:
            self.screen.Label("/root/progress/page", u"请输入 1—%d 之间的编号" % len(self.catalogue.rows))

    def Row(self, index):
        rows = self.catalogue.page(self.page)
        if index < len(rows):
            self.Jump(rows[index]["id"])

    def Jump(self, cue_id):
        if self.screen.session.seek(cue_id):
            self.screen.Start()

    def HandleKey(self, key):
        if key == "33":
            self.Page(-1)
        elif key == "34":
            self.Page(1)
        elif key == "27":
            self.screen.ShowTitle()
