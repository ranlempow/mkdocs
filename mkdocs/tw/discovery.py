# coding: utf-8
import os
import glob

def fileNamesRetrieve( top, maxDepth, pattern):
    matchedFiles = []
    for d in range( 1, maxDepth+1 ):
        maxGlob = "/".join( "*" * d )
        topGlob = os.path.join( top, maxGlob, pattern )
        allFiles = glob.glob( topGlob )
        matchedFiles.extend(allFiles)
    return matchedFiles

class Shelf(object):
    def __init__(self, site_configs=None, options=None):
        import mkdocs.tw.build
        
        # auto site discovery
        if site_configs is None:
            site_configs = fileNamesRetrieve( os.path.expanduser('~'), 4, 'mkdocs.yml')
        
        #print(site_configs)
        
        self.site_builders = []
        for config_file in site_configs:
            print(config_file)
            try:
                builder = mkdocs.tw.build.PageBuilder(config_file, options)
                self.site_builders.append(builder)
            except:
                import traceback
                print(traceback.format_exc())
                
    def walk_sites(self):
        for site in self.site_builders:
            yield site
            