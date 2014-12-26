import sys
sys.path.insert(0, "../")

__version__ = '0.1'

import mkdocs.tw.build
from mkdocs.exceptions import MkDocsException

def arg_to_option(arg):
    """
    Convert command line arguments into two-tuples of config key/value pairs.
    """
    arg = arg.lstrip('--')
    option = True
    if '=' in arg:
        arg, option = arg.split('=', 1)
    return (arg.replace('-', '_'), option)

def main(cmd, args, options=None):
    if cmd == 'build':
        #config = load_config(options=options)
        #build(config, clean_site_dir=clean_site_dir)
        mkdocs.tw.build.build(args[0])
    elif cmd == 'new':
        # TODO:
        #new(args, options)
        pass
    else:
        print('TwDocs (version {0})'.format(__version__))
        print('mkdocs [new|build] {options}')
        
def run_main():
    cmd = sys.argv[1] if len(sys.argv) >= 2 else None
    opts = [arg_to_option(arg) for arg in sys.argv[2:] if arg.startswith('--')]
    try:
        main(cmd, args=sys.argv[2:], options=dict(opts))
    except MkDocsException as e:
        print(e.args[0], file=sys.stderr)


if __name__ == '__main__':
    run_main()

