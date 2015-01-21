from markdown.util import etree
from markdown.extensions import Extension
#from markdown.treeprocessors import Treeprocessor
from markdown.postprocessors import Postprocessor

class PrettyprintPostprocessor(Postprocessor):
    def run(self, text):
        return text.replace('<pre>', '<pre class="prettyprint">')
        
class PrettyprintExtension(Extension):

    def extendMarkdown(self, md, md_globals):
        postprocessor = PrettyprintPostprocessor(md)
        md.postprocessors.add("prettyprint", postprocessor, "_end")


def makeExtension(configs={}):
    return PrettyprintExtension(configs=configs)
