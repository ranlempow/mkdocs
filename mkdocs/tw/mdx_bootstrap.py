from markdown.util import etree
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

class BootstrapTreeprocessor(Treeprocessor):
    
    # Iterator wrapper to get parent and child all at once
    def iterparent(self, root):
        for parent in root.getiterator():
            for child in parent:
                yield parent, child
    
    def addcls(self, elem, cls):
        elem.set('class', (elem.get('class', '') + ' ' + cls).strip())
        
    def run(self, doc):
        
        for (p, c) in self.iterparent(doc):
            #text = ''.join(itertext(c)).strip()
            #if not text:
            #    continue
            
            if c.tag == 'table':
                self.addcls(c, 'table table-bordered')
            if c.tag == 'dl':
                self.addcls(c, 'dl-horizontal')
            '''
            if c.tag == 'div' and 'admonition' in c.get('class'):
                self.addcls(c, 'alert')
                if 'note' in c.get('class'):
                    self.addcls(c, 'alert-info')
            '''
            

class BootstrapExtension(Extension):

    def extendMarkdown(self, md, md_globals):
        treeprocessor = BootstrapTreeprocessor(md)
        md.treeprocessors.add("bootstrap", treeprocessor, "_end")


def makeExtension(configs={}):
    return BootstrapExtension(configs=configs)
