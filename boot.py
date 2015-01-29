import sys
import os
from virtualenv import Logger, call_subprocess


base_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(base_dir, "bootconfig.json")) as f:
    import json
    bootconfig = json.loads(f.read())

venv_dir = bootconfig['venv_dir']
extra_packages = bootconfig['extra_packages']
requirements = bootconfig['requirements']

home_dir = os.path.join(base_dir, venv_dir)

installer_cache_dir = "__installer_cache__"
installer_dir = os.path.join(home_dir, installer_cache_dir)
platform_suffix = '.win32-py3.4.exe'


logger = None


def pip(*args):
    cmd = [os.path.abspath(os.path.join(home_dir, 'Scripts', 'pip'))] + list(args)
    cwd = os.path.abspath(home_dir)
    call_subprocess(
        cmd,
        cwd=cwd,
    )
        
def download_from_uci():
    import urllib.request
    import http.client
    site = 'http://www.lfd.uci.edu/~gohlke/pythonlibs/girnt9fk/'
    conn = http.client.HTTPConnection('www.lfd.uci.edu')
    headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "http://www.lfd.uci.edu/~gohlke/pythonlibs/",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0",}
    
    
    if not os.path.exists(installer_dir):
        os.mkdir(installer_dir)
    
    for exefile in extra_packages:
        exefile += platform_suffix
        local = os.path.join(installer_dir, exefile)
        if not os.path.exists(local):
            logger.notify("downloading... " + site + exefile)
            conn.request("GET", site + exefile, headers=headers)
            res = conn.getresponse()
            logger.notify("{} {}".format(res.status, res.reason))
            data = res.read()
            res.close()
            with open(local, "wb") as f:
                f.write(data)
                logger.notify("write to file: " + local)
            
            
    
def install_requirements():
    txtfile = os.path.join(installer_dir, "requirements.txt")
    with open( txtfile, 'w' ) as f:
        f.write('\n'.join(requirements) + '\n')
    pip( 'install', '-r', txtfile)
    
    for exefile in extra_packages:
        exefile += platform_suffix
        call_subprocess(
                [os.path.abspath(os.path.join(home_dir, 'Scripts', 'easy_install')), 
                    os.path.join(installer_dir, exefile)],
                cwd=os.path.abspath(home_dir),
                #filter_stdout=filter_python_develop,
                #show_stdout=False,
            )
    
def inject_logger():
    from virtualenv import Logger
    global logger
    logger = Logger([
        (Logger.level_for_integer(1), sys.stdout),
        (Logger.level_for_integer(1), open('boot.log', 'w')),
    ])
    import virtualenv
    virtualenv.logger = logger
    
def install():
    from virtualenv import file_search_dirs, create_environment
    default_search_dirs = file_search_dirs()
    
    create_environment(home_dir,
           site_packages=False,
           search_dirs=default_search_dirs,
           symlink=False)
    
    download_from_uci()
    install_requirements()
    
    
def main():
    inject_logger()
    
    def show_help():
        print("""使用方式: boot.py [指令]
目前有以下指令可以使用
----------------------
install - 重新安裝
update - 更新(可以在 git pull 之後使用)
""")
        for cmd in bootconfig['cmd']:
            print(cmd + " - " + bootconfig['cmd'][cmd])
            
    if len(sys.argv) <= 1:
        return show_help()
    
    if sys.argv[1] == 'boot':
        if not os.path.exists(home_dir):
            install()
    elif sys.argv[1] == 'install':
        install()
    elif sys.argv[1] == 'update':
        install()
    else:
        if sys.argv[1] in bootconfig['cmd']:
            call_subprocess(
                cmd=bootconfig['cmd'][sys.argv[1]],
                cwd=os.path.abspath(home_dir),
            )
        else:
            show_help()
            
    '''
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('integers', metavar='N', type=int, nargs='+',
                       help='an integer for the accumulator')
    parser.add_argument('--sum', dest='accumulate', action='store_const',
                       const=sum, default=max,
                       help='sum the integers (default: find the max)')

    args = parser.parse_args()
    print args.accumulate(args.integers)
    '''
    
    
    '''
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose", default=True,
                      help="don't print status messages to stdout")

    (options, args) = parser.parse_args()
    '''
    
    

if __name__ == "__main__":
    main()

