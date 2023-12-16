import io
import os

from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.colors import red

from .constants import (SHOP_LIST_TITLE, SHOP_LIST_HEAD,
                        SHOP_LIST_ITEMS_PER_PAGE)


def prepare_pdf_buffer(shopping_list):
    def _page_create(p, page):
        p.saveState()
        p.setStrokeColor(red)
        p.setLineWidth(5)
        p.line(66, 72, 66, p._pagesize[1] - 72)
        p.setFont('FreeSans', 24)
        p.drawString(108, p._pagesize[1] - 108, SHOP_LIST_TITLE)
        p.setFont('FreeSans', 12)
        p.drawString(66, p._pagesize[1] - 42, SHOP_LIST_HEAD + f'{page}')
        filename = os.path.join(settings.MEDIA_ROOT, 'shop_cart.png')
        p.drawImage(filename, 450, p._pagesize[1] - 138,
                    width=100, height=100, mask='auto')

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    page = 1
    n = 1
    _page_create(p, page)
    for elem in shopping_list:
        p.drawString(108, p._pagesize[1] - 138 - n * 20 + (page - 1) * 600,
                     f'{n}. {elem["ingredient__name"]} - '
                     f'{elem["amount"]} '
                     f'{elem["ingredient__measurement_unit"]}')
        n += 1
        if n % SHOP_LIST_ITEMS_PER_PAGE == 1:
            page += 1
            p.restoreState()
            p.showPage()
            _page_create(p, page)
    p.save()
    buffer.seek(0)
    return buffer
