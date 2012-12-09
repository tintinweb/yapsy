yapsy
=====

hg-git clone of yapsy from http://sourceforge.net/projects/yapsy/



Changes:
========
* fix indents using reindent.py (Damn, that messed up the diff :( )
* added self.config to store own plugin-description/settings as __dict__ (will be linked once configparser finished parsing the description file)
* maintain a __dict__ of active plugins by category
* print warning on plugin load error (loglevel error is too much)
* initializes plugin_info.config with the __dict__ repr of config_parser output so that pluginman always has all the plugin description info and may pass the info to plugin instance
* getPluginByName() if category is None search in all categories!
* activatePlugin() add plugin[category] to active_plugins __dict__
* deactivatePlugin() remove plugin if deactivated
* new: getActivePlugins(): return only active ones based on some
category or sortCriteria or external functions or based on info in plugin-description file
* new: sortPlugins(): sort a given list of plugins based on some metrics (default uses quicksort and the value "priority" in plugin-description
* new: __qsort2d(): quicksort2d (not from me)
* new: __dict_has_keys(): check if a dict has a sequence of keys..