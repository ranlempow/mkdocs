from markdown.util import etree
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

class RemoveTopHeaderTreeprocessor(Treeprocessor):
    # Iterator wrapper to get parent and child all at once
    def iterparent(self, root):
        for parent in root.getiterator():
            for child in parent:
                yield parent, child
    
    def addcls(self, elem, cls):
        elem.set('class', (elem.get('class', '') + ' ' + cls).strip())
        
    def run(self, doc):
        for (p, c) in self.iterparent(doc):
            if c.tag == 'h1':
                p.remove(c)
                break
            

class RemoveTopHeaderExtension(Extension):

    def extendMarkdown(self, md, md_globals):
        treeprocessor = RemoveTopHeaderTreeprocessor(md)
        md.treeprocessors.add("removeth", treeprocessor, "_end")


def makeExtension(configs={}):
    return RemoveTopHeaderExtension(configs=configs)
