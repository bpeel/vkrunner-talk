#!/usr/bin/env python3

import gi
gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg
gi.require_version('Pango', '1.0')
from gi.repository import Pango
gi.require_version('PangoCairo', '1.0')
from gi.repository import PangoCairo
import cairo
import math
import re
import collections

POINTS_PER_MM = 2.8346457

PAGE_WIDTH = 297
PAGE_HEIGHT = PAGE_WIDTH * 768 // 1366

def buf_to_text(buf):
    return "".join(buf).strip()

def get_slides(f):
    buf = []
    sep = re.compile(r'^---\s*$')
    for line in f:
        if sep.match(line):
            yield buf_to_text(buf)
            buf.clear()
        else:
            buf.append(line)
    yield buf_to_text(buf)

def line_to_layout(line):
    font = "Sans"
    font_size = 16

    layout = PangoCairo.create_layout(cr)

    md = re.match(r'(#+) +(.*)', line)
    if md:
        font_size *= 1.2 * len(md.group(1))
        line = md.group(2)
    else:
        md = re.match(r'\* +(.*)', line)
        if md:
            line = "\u2022\t" + md.group(1)
            tab_stop = 10 * POINTS_PER_MM * Pango.SCALE
            tab_array = Pango.TabArray(1, False)
            tab_array.set_tab(0, Pango.TabAlign.LEFT, tab_stop)
            layout.set_tabs(tab_array)
            layout.set_indent(-tab_stop)

    fd = Pango.FontDescription.from_string("{} {}".format(font, font_size))
    layout.set_font_description(fd)
    layout.set_width(PAGE_WIDTH * 0.7 * POINTS_PER_MM * Pango.SCALE)
    layout.set_text(line, -1)

    return layout

def layout_height(layout):
    return layout.get_pixel_extents()[1].height

def layout_width(layout):
    return layout.get_pixel_extents()[1].width

def render_paragraph(cr, text):
    cr.save()

    # Remove the mm scale
    cr.scale(1.0 / POINTS_PER_MM, 1.0 / POINTS_PER_MM)

    layouts = [line_to_layout(line) for line in text.split('\n')]

    total_height = sum(layout_height(layout) for layout in layouts)
    max_width = max(layout_width(layout) for layout in layouts)
    cr.move_to(PAGE_WIDTH / 2.0 * POINTS_PER_MM -
               max_width / 2.0,
               PAGE_HEIGHT / 2.0 * POINTS_PER_MM -
               total_height / 2.0)

    for layout in layouts:
        PangoCairo.show_layout(cr, layout)
        cr.rel_move_to(0, layout_height(layout))

    cr.restore()

def render_slide(cr, slide):
    render_paragraph(cr, slide)    

surface = cairo.PDFSurface("slides.pdf",
                           PAGE_WIDTH * POINTS_PER_MM,
                           PAGE_HEIGHT * POINTS_PER_MM)

cr = cairo.Context(surface)

# Use mm for the units from now on
cr.scale(POINTS_PER_MM, POINTS_PER_MM)

# Use ½mm line width
cr.set_line_width(0.5)

with open('slides.txt', 'rt', encoding='UTF-8') as f:
    for slide_num, slide in enumerate(get_slides(f)):
        if slide_num > 0:
            cr.show_page()
        render_slide(cr, slide)
