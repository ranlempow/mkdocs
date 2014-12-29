# coding: utf-8

from watchdog import events
from watchdog.observers.polling import PollingObserver
#from mkdocs.build import build
from mkdocs.compat import httpserver, socketserver, urlunquote
#from mkdocs.config import load_config
import os
import posixpath
import shutil
import sys
import tempfile


class BuildEventHandler(events.FileSystemEventHandler):
    """
    Perform a rebuild when anything in the theme or docs directory changes.
    """
    def __init__(self, builder):
        super(BuildEventHandler, self).__init__()
        self.builder = builder
    
    def on_any_event(self, event):
        if not isinstance(event, events.DirModifiedEvent):
            print('Rebuilding documentation navigation...', end='')
            self.builder.setup_site_navigation()
            print(' done')

class ConfigEventHandler(BuildEventHandler):
    def on_any_event(self, event):
        if os.path.abspath(event.src_path) == os.path.abspath(self.builder.config['config_file']):
            print('Reloading config file...', end='')
            self.builder.reload_config()
            print(' done')
            super(ConfigEventHandler, self).on_any_event(event)
            
            
class ThemeEventHandler(BuildEventHandler):
    def on_any_event(self, event):
        if os.path.abspath(event.src_path) != os.path.abspath(self.builder.config['extend_theme_css']):
            print('Resetting themes...', end='')
            self.builder.setup_env()
            print(' done')

class FixedDirectoryHandler(httpserver.SimpleHTTPRequestHandler):
    """
    Override the default implementation to allow us to specify the served
    directory, instead of being hardwired to the current working directory.
    """
    base_dir = os.getcwd()

    def translate_path(self, path):
        # abandon query parameters
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        path = posixpath.normpath(urlunquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = self.base_dir
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir):
                continue
            path = os.path.join(path, word)
        return path

    def log_message(self, format, *args):
        date_str = self.log_date_time_string()
        sys.stderr.write('[%s] %s\n' % (date_str, format % args))

def serve_dry(config_file, options=None):
    import mkdocs.tw.build
    mkdocs.tw.build.monkey_patch()
    builder = mkdocs.tw.build.PageBuilder(config_file, options)
    
    event_handler = BuildEventHandler(builder)
    config_event_handler = ConfigEventHandler(builder)
    theme_event_handler = ThemeEventHandler(builder)
    
    observer = PollingObserver()
    observer.schedule(event_handler, builder.config['docs_dir'], recursive=True)
    observer.schedule(config_event_handler, builder.config['base_dir'])
    for theme_dir in builder.config['theme_dir']:
        observer.schedule(theme_event_handler, theme_dir, recursive=True)
    observer.schedule(theme_event_handler, builder.config['extend_theme_src'], recursive=True)
    observer.start()
    
    #import time
    #time.sleep(100)
    
    from bottle import route, run, template, request, static_file, abort
    
    #import sys
    #import json
    #import urllib
    
    builder.setup_site_navigation()
    builder.setup_env()
    
    
    @route('/<docname:path>/index.html', method="GET")
    def mkdocs(docname):
        print(docname)
        for page in builder.site_navigation.walk_pages():
            print(page.abs_url, ('/' if docname else '') + docname + '/index.html')
            if page.abs_url == ('/' if docname else '') + docname + '/index.html':
                context, output_content = builder.make_one(
                        page, builder.site_navigation, builder.env)
                return output_content
            #print(page.abs_url)
            #print(page.url_context)
            #print(page.output_path)
            #builder.make_one(self, page, builder.site_navigation, builder.env)
        abort(404, "No such docs")
        
    @route('/index.html', method="GET")
    def mkdocs_root():
        return mkdocs('')
        
    @route('/<filename:path>', method="GET")
    def files(filename):
        for static_dir in reversed(builder.static_dirs):
            path = os.path.join(static_dir, filename)
            if os.path.exists(path):
                return static_file(filename, root=static_dir)
        print("No such file:" + filename)
        abort(404, "No such file")
        
    import webbrowser
    webbrowser.open_new_tab("http://localhost:8080/index.html")
    
    from waitress.server import create_server
    import bottle
    application = bottle.default_app()
    server = create_server(application, host='localhost', port=8080)
    run(server="waitress", host='localhost', port=8080)



    
def serve(config, options=None):
    """
    Start the devserver, and rebuild the docs whenever any changes take effect.
    """
    # Create a temporary build directory, and set some options to serve it
    tempdir = tempfile.mkdtemp()
    options['site_dir'] = tempdir

    # Only use user-friendly URLs when running the live server
    options['use_directory_urls'] = True

    # Perform the initial build
    config = load_config(options=options)
    build(config, live_server=True)

    # Note: We pass any command-line options through so that we
    #       can re-apply them if the config file is reloaded.
    event_handler = BuildEventHandler(options)
    config_event_handler = ConfigEventHandler(options)

    # We could have used `Observer()`, which can be faster, but
    # `PollingObserver()` works more universally.
    observer = PollingObserver()
    observer.schedule(event_handler, config['docs_dir'], recursive=True)
    for theme_dir in config['theme_dir']:
        observer.schedule(event_handler, theme_dir, recursive=True)
    observer.schedule(config_event_handler, '.')
    observer.start()

    class TCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    class DocsDirectoryHandler(FixedDirectoryHandler):
        base_dir = config['site_dir']

    host, port = config['dev_addr'].split(':', 1)
    server = TCPServer((host, int(port)), DocsDirectoryHandler)

    print('Running at: http://%s:%s/' % (host, port))
    print('Live reload enabled.')
    print('Hold ctrl+c to quit.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Stopping server...')

    # Clean up
    observer.stop()
    observer.join()
    shutil.rmtree(tempdir)
    print('Quit complete')
