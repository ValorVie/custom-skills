-- Git status indicators
th.git = th.git or {}
th.git.modified = ui.Style():fg("blue")
th.git.added = ui.Style():fg("green")
th.git.untracked = ui.Style():fg("yellow")
th.git.deleted = ui.Style():fg("red"):bold()
th.git.ignored = ui.Style():fg("darkgray")

th.git.modified_sign = "M"
th.git.added_sign = "A"
th.git.untracked_sign = "?"
th.git.deleted_sign = "D"

require("git"):setup {
  order = 1500,
}
