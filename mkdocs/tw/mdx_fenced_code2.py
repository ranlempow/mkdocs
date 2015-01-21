"""
Fenced Code Extension for Python Markdown
=========================================

This extension adds Fenced Code Blocks to Python-Markdown.

    >>> import markdown
    >>> text = '''
    ... A paragraph before a fenced code block:
    ...
    ... ~~~
    ... Fenced code block
    ... ~~~
    ... '''
    >>> html = markdown.markdown(text, extensions=['fenced_code'])
    >>> print html
    <p>A paragraph before a fenced code block:</p>
    <pre><code>Fenced code block
    </code></pre>

Works with safe_mode also (we check this because we are using the HtmlStash):

    >>> print markdown.markdown(text, extensions=['fenced_code'], safe_mode='replace')
    <p>A paragraph before a fenced code block:</p>
    <pre><code>Fenced code block
    </code></pre>

Include tilde's in a code block and wrap with blank lines:

    >>> text = '''
    ... ~~~~~~~~
    ...
    ... ~~~~
    ... ~~~~~~~~'''
    >>> print markdown.markdown(text, extensions=['fenced_code'])
    <pre><code>
    ~~~~
    </code></pre>

Language tags:

    >>> text = '''
    ... ~~~~{.python}
    ... # Some python code
    ... ~~~~'''
    >>> print markdown.markdown(text, extensions=['fenced_code'])
    <pre><code class="python"># Some python code
    </code></pre>

Optionally backticks instead of tildes as per how github's code block markdown is identified:

    >>> text = '''
    ... `````
    ... # Arbitrary code
    ... ~~~~~ # these tildes will not close the block
    ... `````'''
    >>> print markdown.markdown(text, extensions=['fenced_code'])
    <pre><code># Arbitrary code
    ~~~~~ # these tildes will not close the block
    </code></pre>

If the codehighlite extension and Pygments are installed, lines can be highlighted:

    >>> text = '''
    ... ```hl_lines="1 3"
    ... line 1
    ... line 2
    ... line 3
    ... ```'''
    >>> print markdown.markdown(text, extensions=['codehilite', 'fenced_code'])
    <pre><code><span class="hilight">line 1</span>
    line 2
    <span class="hilight">line 3</span>
    </code></pre>

Copyright 2007-2008 [Waylan Limberg](http://achinghead.com/).

Project website: <http://packages.python.org/Markdown/extensions/fenced_code_blocks.html>
Contact: markdown@freewisdom.org

License: BSD (see ../docs/LICENSE for details)

Dependencies:
* [Python 2.4+](http://python.org)
* [Markdown 2.0+](http://packages.python.org/Markdown/)
* [Pygments (optional)](http://pygments.org)

"""

from markdown.util import etree
from markdown.extensions import Extension
from markdown.blockprocessors import BlockProcessor

#from . import Extension
#from ..preprocessors import Preprocessor
#from .codehilite import CodeHilite, CodeHiliteExtension, parse_hl_lines
import re


class FencedCodeExtension(Extension):

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        md.parser.blockprocessors.add('fenced_code2',
                                 FencedBlockprocessor(md.parser),
                                 "_begin")


class FencedBlockprocessor(BlockProcessor):
    FENCED_BLOCK_RE = re.compile(r'''
(?P<fence>^(?:~{3,}|`{3,}))[ ]*         # Opening ``` or ~~~
(\{?\.?(?P<lang>[a-zA-Z0-9_+-]*))?[ ]*  # Optional {, and lang
# Optional highlight lines, single- or double-quote-delimited
(hl_lines=(?P<quot>"|')(?P<hl_lines>.*?)(?P=quot))?[ ]*
}?[ ]*\n                                # Optional closing }
(?P<code>.*?)(?<=\n)
(?P=fence)[ ]*$''', re.MULTILINE | re.DOTALL | re.VERBOSE)

    FENCED_BLOCK_TEST = re.compile(r'''
(?P<fence>^(?:~{3,}|`{3,}))         # Opening ``` or ~~~
''', re.MULTILINE | re.DOTALL | re.VERBOSE)


    CODE_WRAP = '<pre><code%s>%s</code></pre>'
    LANG_TAG = ' class="%s"'
    
    def test(self, parent, block):
        m = self.FENCED_BLOCK_TEST.search(block)
        if m:
            self.fence = m.group('fence')
            return True
        return False
        
    def run(self, parent, blocks):
        
        lines_of_block = []
        start, end = None, None
        for i, block in enumerate(blocks):
            #print("blockstart==============")
            #print(block)
            #print("blockend  ==============")
            
            lines = block.split('\n')
            lines_of_block.append(lines)
            for j, line in enumerate(lines):
                if line.startswith(self.fence):
                    if start == None:
                        start = (i, j)
                    elif end == None:
                        end = (i, j)
                    else:
                        break
            
            if start is not None and end is not None:
                break
            
        #print(start, end)
        assert start[0] == 0
        
        
        block_0 = '\n'.join(lines_of_block[0][start[1]:])
        block_c = [blocks[i] for i in range(1, end[0])]
        block_n = '\n'.join(lines_of_block[end[0]][:end[1]+1])
        block_remain = '\n'.join(lines_of_block[end[0]][end[1]+1:])
        
        text = "\n\n".join([block_0] + block_c + [block_n])
        for block in blocks[:end[0]+1]:
            blocks.remove(block)
        blocks.insert(0, block_remain)
        
        '''
        print("start==============")
        print(text)
        print("end  ==============")
        '''
        
        m = self.FENCED_BLOCK_RE.search(text)
        if m:
            pre = etree.SubElement(parent, 'pre')
            pre.set('class', '.prettyprint')
            code = etree.SubElement(pre, 'code')
            if m.group('lang'):
                code.set('class', m.group('lang'))
            code.text = m.group('code') #self._escape(m.group('code'))
            
    
    def _escape(self, txt):
        """ basic html escaping """
        txt = txt.replace('&', '&amp;')
        txt = txt.replace('<', '&lt;')
        txt = txt.replace('>', '&gt;')
        txt = txt.replace('"', '&quot;')
        return txt


def makeExtension(configs=None):
    return FencedCodeExtension(configs=configs)
