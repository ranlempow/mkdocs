# coding: utf-8
from watchdog import events
from watchdog.observers.polling import PollingObserver

import os


class BuildEventHandler(events.FileSystemEventHandler):
    """
    Perform a rebuild when anything in the theme or docs directory changes.
    """
    def __init__(self, builder):
        super(BuildEventHandler, self).__init__()
        self.builder = builder
    
    def on_any_event(self, event):
        if not isinstance(event, events.DirModifiedEvent):
            print('Reloading config file...', end='')
            self.builder.reload_config()
            print(' done')
            
            print('Rebuilding documentation navigation...', end='')
            self.builder.setup_site_navigation()
            print(' done')

class ConfigEventHandler(BuildEventHandler):
    def on_any_event(self, event):
        if os.path.abspath(event.src_path) == os.path.abspath(self.builder.config['config_file']):
            super(ConfigEventHandler, self).on_any_event(event)
            
            
class ThemeEventHandler(BuildEventHandler):
    def on_any_event(self, event):
        if 'extend_theme' in self.builder.config and self.builder.config['extend_theme'] is not None:
            if os.path.abspath(event.src_path) == os.path.abspath(self.builder.config['extend_theme_css']):
                return
                
        print('Resetting themes...', end='')
        self.builder.setup_env()
        print(' done')

def observe(builder):
    event_handler = BuildEventHandler(builder)
    config_event_handler = ConfigEventHandler(builder)
    theme_event_handler = ThemeEventHandler(builder)
    
    config = builder.config
    observer = PollingObserver()
    observer.schedule(event_handler, config['docs_dir'], recursive=True)
    observer.schedule(config_event_handler, config['base_dir'])
    for theme_dir in config['theme_dir']:
        if os.path.exists(theme_dir):
            observer.schedule(theme_event_handler, theme_dir, recursive=True)
    if 'extend_theme' in config and config['extend_theme'] is not None:
        if os.path.exists(config['extend_theme_src']):
            observer.schedule(theme_event_handler, config['extend_theme_src'], recursive=True)
    observer.start()
    builder.observer = observer
    
