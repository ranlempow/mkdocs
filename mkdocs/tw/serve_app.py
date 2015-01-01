import os
from bottle import Bottle, route, run, template, request, static_file, abort

def make_app(builder):
    builder.setup_site_navigation()
    builder.setup_env()
    
    app = Bottle()
    
    if builder.config['use_directory_urls']:
        @app.route('/<docname:path>/', method="GET")
        def mkdocs(docname):
            output_content = None
            for page in builder.site_navigation.walk_pages():
                if page.abs_url == ('/' if docname else '') + docname + '/':
                    context, output_content = builder.make_one(
                            page, builder.site_navigation, builder.env)
            
            if output_content is None:
                abort(404, "No such docs")
            else:
                return output_content
    else:
        @app.route('/<docname:path>/index.html', method="GET")
        def mkdocs(docname):
            output_content = None
            for page in builder.site_navigation.walk_pages():
                if page.abs_url == ('/' if docname else '') + docname + '/index.html':
                    context, output_content = builder.make_one(
                            page, builder.site_navigation, builder.env)
            
            if output_content is None:
                abort(404, "No such docs")
            else:
                return output_content
    
    @app.route('/', method="GET")
    @app.route('/index.html', method="GET")
    def mkdocs_root():
        return mkdocs('')
        
    @app.route('/<filename:path>', method="GET")
    def files(filename):
        # fixed a bug on waitress
        # see https://github.com/Pylons/waitress/issues/76
        if 'wsgi.file_wrapper' in request.environ:
            del request.environ['wsgi.file_wrapper']
        
        for static_dir in reversed(builder.static_dirs):
            path = os.path.join(static_dir, filename)
            if os.path.exists(path):
                return static_file(filename, root=static_dir)
        
        if builder.config['use_directory_urls']:
            return mkdocs(filename)
            
        print("No such file:" + filename)
        abort(404, "No such file")
    
    builder.app = app
    return app