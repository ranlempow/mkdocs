# coding: utf-8
import os

def monkey_patch():
    # patch open() for supproting utf8 
    _open = __builtins__['open']
    def utf8open(*args):
        if len(args) > 1 and 'b' not in args[1]: 
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


# copy from mkdocs.build
class PageBuilder():
    # config_file == 'mkdocs.yml'
    def __init__(self, config_file, options=None):
        self.options = options
        self.config_file = config_file
        self.reload_config()
        
    def reload_config(self):
        from mkdocs.config import load_config, validate_config
        config = load_config(filename=self.config_file, options=self.options)
        
        # patch base_dir
        config['config_file'] = self.config_file
        config['base_dir'] = os.path.dirname(self.config_file)
        
        # patch config
        config['docs_dir'] = os.path.join(config['base_dir'], config['docs_dir'])
        config['site_dir'] = os.path.join(config['base_dir'], config['site_dir'])
        config['pages'] = None
        if len(config['theme_dir']) > 1:
            config['theme_dir'] = os.path.basename(config['theme_dir'][0])
        else:
            config['theme_dir'] = None
        config = validate_config(config)
        
        if 'extend_theme' in config and config['extend_theme'] is not None:
            input, output = make_less(config['extend_theme'], pathonly=True)
            config['theme_dir'].insert(0, output)
            config['extend_theme_css'] = os.path.join(output, 'css', 'bootstrap-custom.min.css')
            config['extend_theme_src'] = input
            
            #config['theme_src'] = input
            
        # import specific "twdoc" markdown extensions
        import importlib
        exts = [
                'smart_strong',
                'footnotes',
                'attr_list',
                'def_list',
                'abbr',
                ]
        for mdx in ('bootstrap', 'plantuml', 'admonition2', 'mytoc', 'removeth',#'prettyprint',
                    'fenced_code2'):
            m = importlib.import_module('mkdocs.tw.mdx_' + mdx)
            exts.append(m.makeExtension())
        config['markdown_extensions'] = exts
        
        #print(config)
        self.config = config
       
        
    def convert_markdown(self, markdown_source, site_navigation=None, extensions=(), strict=False):
        # replace origin toc builder with patched one
        import markdown
        from mkdocs.relative_path_ext import RelativePathExtension
        # Generate the HTML from the markdown source
        builtin_extensions = ['meta', 'toc', 'tables']
        mkdocs_extensions = [RelativePathExtension(site_navigation, strict), ]
        extensions = builtin_extensions + mkdocs_extensions + list(extensions)
        md = markdown.Markdown(
            extensions=extensions
        )
        html_content = md.convert(markdown_source)
        meta = md.Meta
        table_of_contents = md.toc_list
        
        # convert toc to other style, make mkdocs acceptable
        def convert(parent):
            for node in parent:
                node['title'] = node['name']
                convert(node['children'])
        convert(table_of_contents)
        
        return (html_content, table_of_contents, meta)
        
    def get_global_context(self, nav):
        from mkdocs.build import get_global_context
        return get_global_context(nav, self.config)
        
    def get_page_context(self, page, content, nav, toc, meta):
        from mkdocs.build import get_page_context
        context = get_page_context(page, content, nav, toc, meta, self.config)
        config = self.config
        """
        if page.is_homepage or page.title is None:
            page_title = config['site_name']
        else:
            page_title = page.title + ' - ' + config['site_name']
        """
        
        # patch page_mtime
        import os
        import datetime
        st = os.stat(os.path.join(config['docs_dir'], page.input_path))
        dt = datetime.datetime.fromtimestamp(st.st_mtime)
        
        context['page_time'] = dt.strftime("%Y %b %d %H:%M:%S") #dt.isoformat()
        context['page_iso_time'] = dt.isoformat()
        
        #if not page.is_homepage:
        #    context['page_description'] = None
        
        # patch page_top_header
        context['page_top_header'] = toc[0]['name']
        
        
        #print(context['canonical_url'])
        #print(context['page_title'])
        #print(context['page_description'])
        #print(page.input_path)
        return context
        """
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
    
    def setup_site_navigation(self):
        import mkdocs.nav as nav
        self.site_navigation = nav.SiteNavigation(self.config['pages'], self.config['use_directory_urls'])
            
        return self.site_navigation
    
    def setup_env(self):
        # setup theme
        if 'extend_theme' in self.config and self.config['extend_theme'] is not None:
            make_less(self.config['extend_theme'])
        
        import jinja2
        loader = jinja2.FileSystemLoader(self.config['theme_dir'])
        self.env = jinja2.Environment(loader=loader)
        return self.env
        
    def make_one(self, page, site_navigation=None, env=None):
        config = self.config
        
        
        site_navigation = site_navigation or self.setup_site_navigation()
        env = env or self.setup_env()
        
        input_path = os.path.join(config['docs_dir'], page.input_path)
        input_content = open(input_path, 'r').read()

        # Process the markdown text
        html_content, table_of_contents, meta = self.convert_markdown(
            input_content, site_navigation,
            extensions=config['markdown_extensions'], strict=config['strict']
        )
        
        # Make context dict for rendering
        context = self.get_global_context(site_navigation)
        context.update(self.get_page_context(
            page, html_content, site_navigation,
            table_of_contents, meta
        ))

        # Allow 'template:' override in md source files.
        if 'template' in meta:
            template = env.get_template(meta['template'][0])
        else:
            template = env.get_template('base.html')

        # Render the template.
        output_content = template.render(context)
        
        return context, output_content
        
    @property
    def static_dirs(self):
        config = self.config
        return list(reversed(config['theme_dir'])) + [config['docs_dir']]
        
    def build_all(self, dump_json=False):
        config = self.config
        import mkdocs.utils as utils
        # copy static files
        if not dump_json:
            for static_dir in self.static_dirs:
                utils.copy_media_files(static_dir, config['site_dir'])
        
        site_navigation = self.setup_site_navigation()
        env = self.setup_env()
        
        for page in site_navigation.walk_pages():
            # Write the output file.
            output_path = os.path.join(config['site_dir'], page.output_path)
            context, output_content = self.make_one(page, site_navigation, env)
            if dump_json:
                json_context = {
                    'content': context['content'],
                    'title': context['current_page'].title,
                    'url': context['current_page'].abs_url,
                    'language': 'en',
                }
                utils.write_file(json.dumps(json_context, indent=4).encode('utf-8'), output_path.replace('.html', '.json'))
            else:
                utils.write_file(output_content.encode('utf-8'), output_path)
        
            
# translate less script to css
def make_less(extend_theme, pathonly=False):
    import os
    import subprocess
    package_dir = os.path.dirname(__file__)#.replace('\\', '/')
    
    input = '../../mkdocs/extend_themes/source/{}/less/build.less'.format(extend_theme)
    input = os.path.normpath(os.path.join(package_dir, input))
    output = '../../mkdocs/extend_themes/build/{}/css/bootstrap-custom.min.css'.format(extend_theme)
    output = os.path.normpath(os.path.join(package_dir, output))
    
    if not pathonly:
        p = subprocess.Popen([
                'lessc', input,
            ], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        if err != b'':
            print(err)
        else:
            out = out.decode('utf-8')
            open(output, 'w').write(out)
    
    return os.path.join(os.path.dirname(input), '..\\'), os.path.join(os.path.dirname(output), '..\\')

def build(config_file='mkdocs.yml'):
    monkey_patch()
    builder = PageBuilder(config_file)
    builder.build_all()
    