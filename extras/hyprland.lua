hl.config({
  general = {
    gaps_in = 4,
    gaps_out = 8,
    border_size = 1,
    col = {
      active_border = "#b6aa8b",
      inactive_border = "#45443d",
    },
  },
  group = {
    col = {
      border_active = "#b6aa8b",
      border_inactive = "#45443d",
    },
  },
  decoration = {
    rounding = 18,
    active_opacity = 1.0,
    inactive_opacity = 1.0,
    shadow = {
      enabled = true,
      range = 18,
      render_power = 3,
      color = "rgba(00000055)",
    },
    blur = {
      enabled = true,
      size = 4,
      passes = 2,
    },
  },
})
