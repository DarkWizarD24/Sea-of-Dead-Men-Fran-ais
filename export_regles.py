#!/usr/bin/env python
# -*- coding: utf-8 -*-

from scribus import *

def main(argv):
    pdf = scribus.PDFfile()
    pdf.pages = list(range(1,pageCount()+1))
    pdf.version = 16
    pdf.file = 'export/Règles.pdf'
    pdf.save()

if __name__ == '__main__':
    if haveDoc():
        main(sys.argv)
