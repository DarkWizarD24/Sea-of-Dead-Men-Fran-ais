import os
import math
import tempfile
from dataclasses import dataclass, field
import xml.etree.cElementTree as ET
from PyPDF2 import PdfFileMerger, PdfFileReader, PdfFileWriter, utils as PdfUtils


def export_pdf(filename_in, filename_out, background, layers, extra_pages=[]):
    input = filename_in + '.svg'
    print('Export des ' + input)
    with tempfile.TemporaryDirectory() as tmpdir:
        merger = PdfFileMerger()

        for layer in layers:
            print('\t- calque ' + layer)
            os.system('inkscape --actions "select-all:layers; object-set-attribute:style, display:none;select-clear;select-by-id:' + background + ',' + layer + '; object-set-attribute:style, display:inline" --export-area-page --export-filename=' + tmpdir + '/' + layer + '.pdf "' + input + '"')
            merger.append(tmpdir + '/' + layer + '.pdf')

        for extra_page in extra_pages:
            print('\t- pages supplémentaire ' + extra_page)
            os.system('inkscape --export-area-page --export-filename="' + tmpdir + '/' + extra_page + '.pdf" "' + extra_page + '.svg"')
            merger.append(tmpdir + '/' + extra_page + '.pdf')

        output = 'export/' + filename_out + '.pdf'
        merger.write(output)
        merger.close()
        print('\tExporté dans ' + output)


def export_carte(filename, output, layers):
    print('\t- ' + output)
    os.system('gimp-console-2.10 -idf --batch-interpreter=python-fu-eval  -b "import sys;sys.path=[\'.\']+sys.path;import export_cartes;export_cartes.convert(\'' + filename + '\', \'' + output + '\', [\'' + '\', \''.join(layers) + '\'])" -b "pdb.gimp_quit(1)"')


def generate_booklet(input, output):
    # Based on https://github.com/Nimdraug/booklet (MIT License)
    ROTATE = True
    
    def iter_pages( pages ):

        if pages % 4:
            pages = pages + 4 - pages % 4

        for output_page in range(int(pages / 4)):
            first = output_page * 2
            last = pages - 1 - first

            # Front
            yield first,     not ROTATE, 1, 0
            yield last,      not ROTATE, 0, 0

            # Back
            yield first + 1, ROTATE, 1, .5
            yield last  - 1, ROTATE, .5, .5

    with open(input, 'rb') as input_file, open(output, 'wb') as output_file:
        src = PdfFileReader(input_file)
        out = PdfFileWriter()

        size = src.getPage(0).mediaBox.upperRight

        for i, (page, rotate, tx, ty) in enumerate(iter_pages(src.numPages)):
            if i % 2 == 0:
                outpage = out.addBlankPage(size[0] * 2, size[1])
        
            if page < src.numPages:
                src_page = src.getPage(page)
                if rotate:
                    outpage.mergeRotatedTranslatedPage(src_page, 180, float(size[0]) * tx, float(size[1]) * ty, expand=False)
                else:
                    outpage.mergeTranslatedPage(src_page, float(size[0]) * tx, float(size[1]) * ty, expand=False)

        out.write(output_file)


@dataclass
class Bookmark:
     title: str = field(default="")
     level: int = field(default=0)
     page: int = field(default=0)


def extract_bookmarks_sla(file):
    bookmarks = [Bookmark("Sommaire", 1, 1), Bookmark()]

    tree = ET.parse(file)

    toc = tree.find("./DOCUMENT/PAGEOBJECT[@ANNAME = 'Texte_TOC_1']")
    bookmark_index = 1
    for toc_entry in toc[0]:
        if toc_entry.tag == 'ITEXT':
            bookmarks[bookmark_index].title = toc_entry.get('CH')
        elif toc_entry.tag == 'para':
            bookmarks[bookmark_index].level = 1 if toc_entry.get('PARENT') == 'Sommaire titre 1' else 2
            bookmark_index += 1
            bookmarks.append(Bookmark())

    toc_numbers = tree.find("./DOCUMENT/PAGEOBJECT[@ANNAME = 'Texte_TOC_num_1']")
    bookmark_index = 1
    for toc_entry in toc_numbers[0]:
        if toc_entry.tag == 'ITEXT':
            bookmarks[bookmark_index].page = int(toc_entry.get('CH'))
        elif toc_entry.tag == 'para':
            bookmark_index += 1

    return bookmarks


def add_pdf_bookmarks(pdf_in, bookmarks, pdf_out):
    writer = PdfFileWriter()  # open output
    reader = PdfFileReader(pdf_in)  # open input
    writer.cloneDocumentFromReader(reader)
    parent_bookmark = None
    for bookmark in bookmarks:
        if bookmark.level == 1:
            parent_bookmark = writer.addBookmark(bookmark.title, bookmark.page, parent=None)  # add bookmark
        else:
            writer.addBookmark(bookmark.title, bookmark.page, parent=parent_bookmark)  # add bookmark
        
    writer.setPageMode("/UseOutlines")
    with open(pdf_out, "wb") as fp:  # creating result pdf JCT
        writer.write(fp)  # writing to result pdf JCT


if __name__ == '__main__':
    export_dir = 'export'
    if not os.path.exists(export_dir):
        os.mkdir(export_dir)

    export_pdf('livrets personnages', 'Sea of Dead Men - Livrets de personnages', 'fond', ['commandant', 'fierabras', 'marin', 'occultiste', 'ravageur', 'scelerat'])
    export_pdf('livrets équipages', "Sea of Dead Men - Livrets d'équipages", 'fond', ['loyalistes', 'maraudeurs', 'renegats', 'spectres'], ['factions et raffuts'])
    export_pdf('fiche MJ', 'Sea of Dead Men - Fiche MJ', 'fond', ['actionrecto', 'actionverso', 'objetrecto', 'objetverso', 'carterecto'])

    print('Export des cartes')
    export_carte('cartes.xcf', export_dir + '/Les régions de la mer Carrascane.png', ['Fond', 'Iles', 'Frontières', 'Noms', 'Bordure'])
    export_carte('cartes.xcf', export_dir + '/Les régions de la mer Carrascane avec scores.png', ['Fond', 'Iles', 'Frontières', 'Noms', 'Score', 'Bordure'])
    export_carte('cartes.xcf', export_dir + '/Les routes de la mer Carrascane.png', ['Fond', 'Traits', 'Iles', 'Routes', 'Noms', 'Bordure'])
    export_carte('cartes.xcf', export_dir + '/La mer Carrascane.png', ['Fond', 'Traits', 'Iles', 'Noms', 'Bordure'])

    print('Export des règles')
    os.system("scribus -g -py export_regles.py -- Règles.sla")
    regles_tmp = export_dir + '/Règles.pdf'
    regles = export_dir + '/Sea of Dead Men - Règles.pdf'
    add_pdf_bookmarks(regles_tmp, extract_bookmarks_sla('Règles.sla'), regles)
    print('\tExporté dans ' + regles)

    regles_livret = export_dir + '/Sea of Dead Men - Règles livret A4.pdf'
    generate_booklet(regles_tmp, regles_livret)
    print('\tExporté dans ' + regles_livret)
    
    os.remove(regles_tmp)