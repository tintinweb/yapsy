#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Defines plugin managers that can handle configuration files similar to
the ini files manipulated by Python's ConfigParser module.
"""

import sys, os
import logging
import ConfigParser

from IPlugin import IPlugin


from PluginManager import PluginManager
from PluginManager import PLUGIN_NAME_FORBIDEN_STRING



class ConfigurablePluginManager(PluginManager):
	"""
	A plugin manager that also manages a configuration file.

	The configuration file will be accessed through a ``ConfigParser``
	derivated object. The file can be used for other purpose by the
	application using this plugin manager as it will only add a new
	specific section ``[Plugin Management]`` for itself and also new
	sections for some plugins that will start with [Plugin:***] (only
	the plugins that explicitly requires to save configuration options
	will have this kind of section).
	"""
	
	CONFIG_SECTION_NAME = "Plugin Management"

	def __init__(self,
				 categories_filter={"Default":IPlugin}, 
				 directories_list=[os.path.dirname(__file__)], 
				 plugin_info_ext="yapsy-plugin",
				 configparser_instance=None,
				 config_change_trigger= lambda x:True):
		"""
		Create the plugin manager and record the ConfigParser instance
		that will be used afterwards.
		
		The ``config_change_trigger``argument can be used to set a
		specific method to call when the configuration is
		altered. This will let the client application manage the way
		they want the configuration to be updated (e.g. write on file
		at each change or at precise time intervalls or whatever....)
		"""
		PluginManager.__init__(self, 
							   categories_filter, 
							   directories_list, 
							   plugin_info_ext)
		self.setConfigParser(configparser_instance)
		# set the (optional) fucntion to be called when the
		# configuration is changed:
		self.config_has_changed = config_change_trigger

	def setConfigParser(self,configparser_instance):
		"""
		Set the ConfigParser instance.
		"""
		self.config_parser = configparser_instance
		
	def __getCategoryPluginsListFromConfig(self, plugin_list_str):
		"""
		Parse the string describing the list of plugins to activate,
		to discover their actual names and return them.
		"""
		return plugin_list_str.strip(" %s"%PLUGIN_NAME_FORBIDEN_STRING)

	def __getCategoryPluginsConfigFromList(self, plugin_list):
		"""
		Compose a string describing the list of plugins to activate
		"""
		return PLUGIN_NAME_FORBIDEN_STRING.join(plugin_list)
		
	def __getCategoryOptionsName(self,category_name):
		"""
		Return the appropirately formated version of the category's
		option.
		"""
		return "%s_plugins_to_load" % category_name.replace(" ","_")

	def __addPluginToConfig(self,category_name, plugin_name):
		"""
		Utility function to add a plugin to the list of plugin to be
		activated.
		"""
		# check that the section is here
		if not self.config_parser.has_section(CONFIG_SECTION_NAME):
			self.config_parser.add_section(CONFIG_SECTION_NAME)
		# check that the category's list of activated plugins is here too
		option_name = self.__getCategoryOptionsName(category_name)
		if not self.config_parser.has_option(option_name):
			# if there is no list yet add a new one
			self.config_parser.set(CONFIG_SECTION_NAME,option_name,plugin_name)
		else:
			# get the already existing list and append the new
			# activated plugin to it.
			past_list_str = self.config_parser.get_option(option_name)
			past_list = self.__getCategoryPluginsListFromConfig(past_list)
			past_list.append(plugin_name)
			new_list_str = self.__getCategoryPluginsConfigFromList(past_list)
			self.config_parser.set(CONFIG_SECTION_NAME,option_name,new_list_str)
		self.config_has_changed()

	def __removePluginFromConfig(self,category_name, plugin_name):
		"""
		Utility function to add a plugin to the list of plugin to be
		activated.
		"""
		# check that the section is here
		if not self.config_parser.has_section(CONFIG_SECTION_NAME):
			self.config_parser.add_section(CONFIG_SECTION_NAME)


	def registerOptionFromPlugin(self, 
								 category_name, plugin_name, 
								 option_name, option_value):
		"""
		To be called from a plugin object, register a given option in
		the name of a given plugin.
		"""
		section_name = "%s plugin: %s" % (category_name,plugin_name)
		self.config_parser.set(section_name,option_name,option_value)
		self.config_has_changed()

	def hasOptionFromPlugin(self, 
							category_name, plugin_name, option_name):
		"""
		To be called from a plugin object, return True if the option
		has already been registered.
		"""
		section_name = "%s plugin: %s" % (category_name,plugin_name)
		return self.config_parser.has_section(section_name) and self.config_parser.has_option(section_name,option_name)

	def readOptionFromPlugin(self, 
							 category_name, plugin_name, option_name):
		"""
		To be called from a plugin object, read a given option in
		the name of a given plugin.
		"""
		section_name = "%s plugin: %s" % (category_name,plugin_name)
		return self.config_parser.get(section_name,option_name)


	def __decoratePluginObject(self, plugin_object):
		"""
		Add two methods to the plugin objects that will make it
		possible for it to benefit from this class's api concerning
		the management of the options.
		"""
		plugin_object.setConfigOption = lambda x,y: return self.registerOptionFromPlugin(plugin_object.category,
																						 plugin_object.name,
																						 x,y)
		plugin_object.setConfigOption.__doc__ = self.registerOptionFromPlugin.__doc__
		plugin_object.getConfigOption = lambda x: return self.readOptionFromPlugin(plugin_object.category,
																					 plugin_object.name,
																					 x)
		plugin_object.getConfigOption.__doc__ = self.readOptionFromPlugin.__doc__
		plugin_object.hasConfigOption = lambda x: return self.hasOptionFromPlugin(plugin_object.category,
																				  plugin_object.name,
																				  x)
		plugin_object.hasConfigOption.__doc__ = self.hasOptionFromPlugin.__doc__


	def activatePluginByName(self, category_name, plugin_name):
		"""
		Activate a plugin, if you want the plugin's activation to be
		registered in the config file it is crucial to use this method
		to activate a plugin and not call the plugin object's
		``activate`` method.

		This method will also "decorate" the plugin object so that it
		can use this class's methods to register its own options.
		"""
		# activate the plugin
		plugin_object = PluginManager.activatePluginByName(self,category_name,plugin_name)
		if plugin_object is None:
			return None
		# check the activation and then set the config option
		if plugin_object.is_activated:
			self.__addPluginToConfig(category_name,plugin_name)
			# now decorate the plugin
			self.__decoratePluginObject(plugin_object)		
			return plugin_object
		return None

	def collectPlugins(self):
		"""
		Walk through the plugins' places and look for plugins.  Then
		for each plugin candidate look for its category, load it and
		stores it in the appropriate slot of the category_mapping.
		"""
		PluginManager.collectPlugins(self)
		# now load the plugins according to the recorded configuration
		if self.config_parser.has_section(CONFIG_SECTION_NAME):
			# browse all the categories
			for category_name in self.category_mapping.keys():
				# get the list of plugins to be activated for this
				# category
				option_name = "%s_plugins_to_load"%category_name
				if self.config_parser.has_option(CONFIG_SECTION_NAME,
												 option_name):
					plugin_list_str = self.config_parser.get(CONFIG_SECTION_NAME,
															 option_name)
					plugin_list = self.__getPluginListFromConfig(plugin_list_str)
					# activate all the plugins that should be
					# activated
					for plugin_name in plugin_list:
						self.activatePluginByName(category_name, plugin_name)

				