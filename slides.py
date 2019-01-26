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

class RenderObject:
    pass

class LayoutRenderObject(RenderObject):
    def __init__(self, layout):
        self.layout = layout

    def get_height(self):
        return self.layout.get_pixel_extents()[1].height / POINTS_PER_MM

    def get_width(self):
        return self.layout.get_pixel_extents()[1].width / POINTS_PER_MM

    def render(self, cr):
        cr.save()
        # Remove the mm scale
        cr.scale(1.0 / POINTS_PER_MM, 1.0 / POINTS_PER_MM)
        PangoCairo.show_layout(cr, self.layout)
        cr.restore()

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

def line_to_render_object(line):
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

    return LayoutRenderObject(layout)

def render_slide(cr, text):
    cr.save()

    objects = [line_to_render_object(line) for line in text.split('\n')]

    total_height = sum(obj.get_height() for obj in objects)
    max_width = max(obj.get_width() for obj in objects)

    cr.move_to(PAGE_WIDTH / 2.0 - max_width / 2.0,
               PAGE_HEIGHT / 2.0 - total_height / 2.0)

    for obj in objects:
        obj.render(cr)
        cr.rel_move_to(0, obj.get_height())

    cr.restore()

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
