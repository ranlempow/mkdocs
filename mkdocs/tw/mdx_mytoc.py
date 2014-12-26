
from markdown.util import etree, parseBoolValue
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from markdown.extensions.toc import TocTreeprocessor, order_toc_list
from markdown.extensions.headerid import slugify, unique, itertext, stashedHTML2text
import re

class MyTocTreeprocessor(TocTreeprocessor):
    def run(self, doc):

        div = etree.Element("div")
        div.attrib["class"] = "toc"
        header_rgx = re.compile("[Hh][123456]")
        
        self.use_anchors = parseBoolValue(self.config["anchorlink"])
        self.use_permalinks = parseBoolValue(self.config["permalink"], False)
        if self.use_permalinks is None:
            self.use_permalinks = self.config["permalink"]
        
        # Get a list of id attributes
        used_ids = set()
        for c in doc.getiterator():
            if "id" in c.attrib:
                used_ids.add(c.attrib["id"])

        toc_list = []
        marker_found = False
        for (p, c) in self.iterparent(doc):
            text = ''.join(itertext(c)).strip()
            if not text:
                continue

            # To keep the output from screwing up the
            # validation by putting a <div> inside of a <p>
            # we actually replace the <p> in its entirety.
            # We do not allow the marker inside a header as that
            # would causes an enless loop of placing a new TOC 
            # inside previously generated TOC.
            if c.text and c.text.strip() == self.config["marker"] and \
               not header_rgx.match(c.tag) and c.tag not in ['pre', 'code']:
                for i in range(len(p)):
                    if p[i] == c:
                        p[i] = div
                        break
                marker_found = True
                            
            if header_rgx.match(c.tag):
                
                # Do not override pre-existing ids 
                if not "id" in c.attrib:
                    elem_id = stashedHTML2text(text, self.markdown)
                    elem_id = unique(self.config["slugify"](elem_id, '-'), used_ids)
                    c.attrib["id"] = elem_id
                else:
                    elem_id = c.attrib["id"]

                tag_level = int(c.tag[-1])
                
                toc_list.append({'level': tag_level,
                    'id': elem_id,
                    'name': text})

                if self.use_anchors:
                    self.add_anchor(c, elem_id)
                if self.use_permalinks:
                    self.add_permalink(c, elem_id)
                
        toc_list_nested = order_toc_list(toc_list)
        self.build_toc_etree(div, toc_list_nested)
        prettify = self.markdown.treeprocessors.get('prettify')
        if prettify: prettify.run(div)
        if not marker_found:
            # serialize and attach to markdown instance.
            toc = self.markdown.serializer(div)
            for pp in self.markdown.postprocessors.values():
                toc = pp.run(toc)
            self.markdown.toc = toc
        self.markdown.toc_list = toc_list_nested
        
    
        
class MyTocExtension(Extension):
    
    TreeProcessorClass = MyTocTreeprocessor
    
    def __init__(self, configs=[]):
        self.config = { "marker" : ["[TOC]", 
                            "Text to find and replace with Table of Contents -"
                            "Defaults to \"[TOC]\""],
                        "slugify" : [slugify,
                            "Function to generate anchors based on header text-"
                            "Defaults to the headerid ext's slugify function."],
                        "title" : [None,
                            "Title to insert into TOC <div> - "
                            "Defaults to None"],
                        "anchorlink" : [0,
                            "1 if header should be a self link"
                            "Defaults to 0"],
                        "permalink" : [0,
                            "1 or link text if a Sphinx-style permalink should be added",
                            "Defaults to 0"]
                       }

        for key, value in configs:
            self.setConfig(key, value)

    def extendMarkdown(self, md, md_globals):
        tocext = self.TreeProcessorClass(md)
        tocext.config = self.getConfigs()
        # Headerid ext is set to '>prettify'. With this set to '_end',
        # it should always come after headerid ext (and honor ids assinged 
        # by the header id extension) if both are used. Same goes for 
        # attr_list extension. This must come last because we don't want
        # to redefine ids after toc is created. But we do want toc prettified.
        md.treeprocessors.add("mytoc", tocext, "_end")


def makeExtension(configs={}):
    return MyTocExtension(configs=configs)
