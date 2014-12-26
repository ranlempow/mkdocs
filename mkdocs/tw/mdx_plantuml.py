import subprocess

from markdown.util import etree
from markdown.extensions import Extension
from markdown.blockprocessors import BlockProcessor

def parse_plantuml(puml_string):
    
    p = subprocess.Popen([
            'java', '-jar', 'plantuml.jar', '-charset', 'utf-8', '-tsvg', '-pipe'
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    input = puml_string.encode('utf-8')
    out, err = p.communicate(input)
    if err != b'':
        print(err)
    else:
        out = out.decode('utf-8')
        # remove namespace
        out = out.replace(' xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"', '')
        # remove fixed style
        #out = out.replace('fill="#FEFECE"', '')
        #out = out.replace('style="stroke: #A80036; stroke-width: 1.5;"', '')
        return out
    
    
def clearElement(elem):
    
    for attr in [
        'fill',
        'style',
        'font-family',
        'font-size',
    ]:
        if attr in elem.attrib:
            del elem.attrib[attr]

class PlantUMLProcessor(BlockProcessor):
    def test(self, parent, block):
        return block.startswith('@startuml')

    def run(self, parent, blocks):
        enduml = None
        for i, block in enumerate(blocks):
            if '@enduml' in block:
                enduml = i + 1
                break
        
        if enduml is not None:
            
            puml_string = '\n'.join(blocks[:enduml])
            
            for block in blocks[:enduml]:
                blocks.remove(block)
            
            et = etree.fromstring(parse_plantuml(puml_string))
            for elem in et.iter():
                if elem.tag == 'rect' \
                  and elem.get('style', '') == "stroke: #A80036; stroke-width: 1.5;" \
                  and elem.get('height', '0') != '5':
                    clearElement(elem)
                    elem.set('class', 'uml object')
                elif elem.tag == 'rect' \
                  and elem.get('style', '') == "stroke: #A80036; stroke-width: 1.5;":
                    clearElement(elem)
                    elem.set('class', 'uml compdec')
                elif elem.tag == 'text':
                    clearElement(elem)
                    elem.set('class', 'uml text')
                elif elem.tag == 'path' \
                  and elem.get('style', '') == "stroke: #A80036; stroke-width: 1.0; stroke-dasharray: 7.0,7.0;":
                    clearElement(elem)
                    elem.set('class', 'uml relate_dash')
                elif elem.tag == 'path' \
                  and elem.get('style', '') == "stroke: #A80036; stroke-width: 1.0;":
                    clearElement(elem)
                    elem.set('class', 'uml relate')
                elif elem.tag == 'polygon' \
                  and elem.get('style', '') == "stroke: #A80036; stroke-width: 1.0;":
                    clearElement(elem)
                    elem.set('class', 'uml arrow')
                    
            div = etree.SubElement(parent, 'div')
            div.set('class', 'plantuml')
            div.append(et)
        else:
            blocks.pop()

class PlantUMLExtension(Extension):
    """ Add definition lists to Markdown. """

    def extendMarkdown(self, md, md_globals):
        """ Add an instance of DefListProcessor to BlockParser. """
        md.parser.blockprocessors.add('plantuml', 
                                      PlantUMLProcessor(md.parser),
                                      '_begin')

def makeExtension(configs={}):
    return PlantUMLExtension(configs=configs)