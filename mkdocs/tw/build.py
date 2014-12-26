
def monkey_patch():
    # patch open() for supproting utf8 
    _open = __builtins__['open']
    def utf8open(*args):
        if 'b' not in args[1]: 
            return _open(*args, encoding='utf8')
        else:
            return _open(*args)
    __builtins__['open'] = utf8open

    # patch relpath() for supproting windows slash
    import os
    _relpath = os.path.relpath
    def win_relpath(*args):
        return _relpath(*args).replace('\\', '/')
    os.path.relpath = win_relpath

    # patch convert_markdown() for better toc render
    import markdown
    import mkdocs.build
    from mkdocs.relative_path_ext import RelativePathExtension
    
    def convert_markdown(markdown_source, site_navigation=None, extensions=(), strict=False):

        # Generate the HTML from the markdown source
        builtin_extensions = ['meta', 'toc', 'tables', 'fenced_code']
        mkdocs_extensions = [RelativePathExtension(site_navigation, strict), ]
        extensions = builtin_extensions + mkdocs_extensions + list(extensions)
        md = markdown.Markdown(
            extensions=extensions
        )
        html_content = md.convert(markdown_source)
        meta = md.Meta
        table_of_contents = md.toc_list

        return (html_content, table_of_contents, meta)

    '''
    def convert_markdown(markdown_source, extensions=()):
        # Generate the HTML from the markdown source
        md = markdown.Markdown(
            extensions=['meta', 'toc', 'tables', 'fenced_code'] + list(extensions)
        )
        html_content = md.convert(markdown_source)
        
        toc = md.toc_list
        meta = md.Meta
        print(toc)
        return (html_content, toc, meta)
    '''
    mkdocs.build.convert_markdown = convert_markdown
    
    import mkdocs.build
    _get_page_context = mkdocs.build.get_page_context
    def get_page_context(page, content, nav, toc, meta, config):
        context = _get_page_context(page, content, nav, toc, meta, config)
        """
        if page.is_homepage or page.title is None:
            page_title = config['site_name']
        else:
            page_title = page.title + ' - ' + config['site_name']
        """
        
        import os
        import datetime
        st = os.stat(os.path.join(config['docs_dir'], page.input_path))
        dt = datetime.datetime.fromtimestamp(st.st_mtime)
        context['page_mtime'] = dt.isoformat()
        
        if not page.is_homepage:
            context['page_description'] = None
        
        context['page_top_header'] = toc[0]['name']
        
        
        #print(context['canonical_url'])
        #print(context['page_title'])
        #print(context['page_description'])
        #print(page.input_path)
        return context
        """
        if config['site_url']:
            base = config['site_url']
            if not base.endswith('/'):
                base += '/'
            canonical_url = urljoin(base, page.abs_url.lstrip('/'))
        else:
            canonical_url = None

        return {
            'page_title': page_title,
            'page_description': page_description,

            'content': content,
            'toc': toc,
            'meta': meta,


            'canonical_url': canonical_url,

            'current_page': page,
            'previous_page': page.previous_page,
            'next_page': page.next_page,
        }
        """
    mkdocs.build.get_page_context = get_page_context
    
# translate less script to css
def make_less(extend_theme):
    import os
    import subprocess
    package_dir = os.path.dirname(__file__)#.replace('\\', '/')
    
    input = '../../mkdocs/extend_themes/source/{}/less/build.less'.format(extend_theme)
    input = os.path.normpath(os.path.join(package_dir, input))
    output = '../../mkdocs/extend_themes/build/{}/css/bootstrap-custom.min.css'.format(extend_theme)
    output = os.path.normpath(os.path.join(package_dir, output))
    
    p = subprocess.Popen([
            'lessc', input,
        ], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    if err != b'':
        print(err)
    else:
        out = out.decode('utf-8')
        open(output, 'w').write(out)
    
    return os.path.join(os.path.dirname(output), '..\\')

def build(config_file='mkdocs.yml'):
    #make_less()
    
    from mkdocs.build import build
    from mkdocs.config import load_config, validate_config
    from mkdocs.exceptions import ConfigurationError
    import os
    
    try:
        monkey_patch()
        config = load_config(filename=config_file)
        
        config['docs_dir'] = os.path.join(os.path.dirname(config_file), config['docs_dir'])
        config['site_dir'] = os.path.join(os.path.dirname(config_file), config['site_dir'])
        config['pages'] = None
        config['theme_dir'] = os.path.basename(config['theme_dir'][0])
        config = validate_config(config)
        
        if 'extend_theme' in config and config['extend_theme'] is not None:
            config['theme_dir'].insert(0, make_less(config['extend_theme']))
        
        import importlib
        exts = ['extra', 'def_list']
        for mdx in ('bootstrap', 'plantuml', 'admonition2', 'mytoc', 'removeth'):
            m = importlib.import_module('mkdocs.tw.mdx_' + mdx)
            exts.append(m.makeExtension())
        config['markdown_extensions'] = exts
        
        print(config)
        build(config, clean_site_dir=False)
    except ConfigurationError as e:
            print(e.args[0], file=sys.stderr)
