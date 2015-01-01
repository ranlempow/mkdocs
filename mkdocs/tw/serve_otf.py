# coding: utf-8
import os

# fixed a bug on bottle
# see https://github.com/bottlepy/bottle/issues/602
def _handle(self, environ):
    from bottle import request, response, HTTPResponse, HTTPError, RouteReset, py3k, _e
    from traceback import format_exc
    converted = 'bottle.raw_path' in environ
    path = environ['bottle.raw_path'] = environ['PATH_INFO']
    if py3k and not converted:
        try:
            environ['PATH_INFO'] = path.encode('latin1').decode('utf8')
        except UnicodeError:
            return HTTPError(400, 'Invalid path string. Expected UTF-8**')

    try:
        environ['bottle.app'] = self
        request.bind(environ)
        response.bind()
        try:
            self.trigger_hook('before_request')
            route, args = self.router.match(environ)
            environ['route.handle'] = route
            environ['bottle.route'] = route
            environ['route.url_args'] = args
            return route.call(**args)
        finally:
            self.trigger_hook('after_request')

    except HTTPResponse:
        return _e()
    except RouteReset:
        route.reset()
        return self._handle(environ)
    except (KeyboardInterrupt, SystemExit, MemoryError):
        raise
    except Exception:
        if not self.catchall: raise
        stacktrace = format_exc()
        environ['wsgi.errors'].write(stacktrace)
        return HTTPError(500, "Internal Server Error", _e(), stacktrace)
import bottle
bottle.Bottle._handle = _handle


def serve_common(sites, application, host='localhost', port=8080, homepage='index.html'):
    import webbrowser
    webbrowser.open_new_tab("http://{}:{}/{}".format(host, port, homepage) )
    
    from waitress.server import create_server
    import bottle
    #application = bottle.default_app()
    #server = create_server(application, host=host, port=8080)
    
    print('Live reload enabled.')
    print('Hold ctrl+c to quit.')
    try:
        bottle.run(app=application, server="waitress", host=host, port=port)
    except KeyboardInterrupt:
        print('Stopping server...')

    # Clean up
    for site in sites:
        site.observer.stop()
        site.observer.join()
    print('Quit complete')
    
def serve_site(config_file, options=None):
    import mkdocs.tw.build
    mkdocs.tw.build.monkey_patch()
    builder = mkdocs.tw.build.PageBuilder(config_file, options)
    
    from mkdocs.tw.observe import observe
    builder.setup_site_navigation()
    builder.setup_env()
    observe(builder)

    from serve_app import make_app
    app = make_app(builder)
    
    #import bottle
    #root_app = bottle()
    #root_app.mount(prefix="", app=app)
    
    host, port = config['dev_addr'].split(':', 1)
    serve_common([builder], app, host, int(port), homepage='index.html')


def serve_shelf(config_files=None, options=None):
    import mkdocs.tw.build
    import mkdocs.tw.discovery
    mkdocs.tw.build.monkey_patch()
    #config_files = fileNamesRetrieve(os.path.expanduser('~'), 4, )
    
    shalf = mkdocs.tw.discovery.Shelf(config_files)
    
    from bottle import Bottle
    root_app = Bottle()
    
    for site in shalf.walk_sites():
        from mkdocs.tw.observe import observe
        site.setup_site_navigation()
        site.setup_env()
        observe(site)
        
        from mkdocs.tw.serve_app import make_app
        app = make_app(site)
        root_app.mount(prefix=site.config['site_name'], app=app)
        
        # TODO:
        host, port = site.config['dev_addr'].split(':', 1)
    
    @root_app.route('/index.html', method="GET")
    def homepage():
        links = []
        for site in shalf.walk_sites():
            links.append('<a href="{0}/index.html">{0}</a><br>'.format(site.config['site_name']))
        return ''.join(links)
    
    print(root_app)
    
    serve_common(list(shalf.walk_sites()) ,root_app, host, int(port), homepage='index.html')
