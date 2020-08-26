import os
import configparser
import sys

from common_paths import config_dir, data_dir
from common_types import ConfigValueType
from io_utils import ensure_exist
from info.system_info import systems, computer_systems

#Static paths I guess
_main_config_path = os.path.join(config_dir, 'config.ini')
_ignored_dirs_path = os.path.join(config_dir, 'ignored_directories.txt')
_system_config_path = os.path.join(config_dir, 'systems.ini')

def parse_string_list(value):
	if not value:
		return []
	return [item for item in value.split(';') if item]

def parse_path_list(value):
	if not value:
		return []
	return [os.path.expanduser(p) for p in parse_string_list(value)]

def parse_value(section, name, value_type, default_value):
	if value_type == ConfigValueType.Bool:
		return section.getboolean(name, default_value)
	if value_type in (ConfigValueType.FilePath, ConfigValueType.FolderPath):
		return os.path.expanduser(section[name])
	if value_type == ConfigValueType.StringList:
		return parse_string_list(section[name])
	if value_type in (ConfigValueType.FilePathList, ConfigValueType.FolderPathList):
		return parse_path_list(section[name])
	if value_type == ConfigValueType.Integer:
		return section.getint(name, default_value)
	return section[name]

def parse_command_line_bool(value):
	#I swear there was some inbuilt way to do this oh well
	lower = value.lower()
	if lower in ('yes', 'true', 'on', 't', 'y', 'yeah'):
		return True
	if lower in ('no', 'false', 'off', 'f', 'n', 'nah', 'nope'):
		return False

	raise TypeError(value)

def convert_value_for_ini(value):
	if value is None:
		return ''
	if isinstance(value, list):
		return ';'.join(value)
	return str(value)

class ConfigValue():
	def __init__(self, section, value_type, default_value, name, description):
		self.section = section
		self.type = value_type
		self.default_value = default_value
		self.name = name #This is for humans to read!
		self.description = description

runtime_option_section = '<runtime option section>'

_config_ini_values = {
	'output_folder': ConfigValue('Paths', ConfigValueType.FolderPath, os.path.join(data_dir, 'apps'), 'Output folder', 'Folder to put launchers'),
	'organized_output_folder': ConfigValue('Paths', ConfigValueType.FolderPath, os.path.join(data_dir, 'organized_apps'), 'Organized output folder', 'Folder to put subfolders in for the organized folders frontend'),
	'image_folder': ConfigValue('Paths', ConfigValueType.FolderPath, os.path.join(data_dir, 'images'), 'Image folder', 'Folder to store images extracted from games with embedded images'),

	'get_series_from_name': ConfigValue('General', ConfigValueType.Bool, False, 'Get series from name', 'Attempt to get series from parsing name'),
	'use_banner_as_icon': ConfigValue('General', ConfigValueType.Bool, False, 'Use banner as icon', 'If there is a banner image but not an icon, use that as icon'),
	'sort_multiple_dev_names': ConfigValue('General', ConfigValueType.Bool, False, 'Sort multiple developer/publisher names', 'For games with multiple entities in developer/publisher field, sort alphabetically'),

	'skipped_source_files': ConfigValue('Arcade', ConfigValueType.StringList, [], 'Skipped source files', 'List of MAME source files to skip (not including extension)'),
	'memcard_path': ConfigValue('Arcade', ConfigValueType.FolderPath, None, 'Memory card path', 'Path to store memory cards for arcade systems which support that'),
	'exclude_non_arcade': ConfigValue('Arcade', ConfigValueType.Bool, False, 'Exclude non-arcade', 'Skip machines not categorized as arcade games or as any other particular category (various devices and gadgets, etc)'),
	'exclude_pinball': ConfigValue('Arcade', ConfigValueType.Bool, False, 'Exclude pinball', 'Whether or not to skip pinball games (physical pinball, not video pinball)'),
	'exclude_standalone_systems': ConfigValue('Arcade', ConfigValueType.Bool, False, 'Exclude standalone systems', 'Skip machines categorized as "standalone systems" (computers, game consoles, etc)'),
	'exclude_non_working': ConfigValue('Arcade', ConfigValueType.Bool, False, 'Exclude non-working', 'Skip any driver marked as not working'),
	'non_working_whitelist': ConfigValue('Arcade', ConfigValueType.StringList, [], 'Non-working whitelist', 'If exclude_non_working is True, allow these machines anyway even if they are marked as not working'),

	'mac_db_path': ConfigValue('Mac', ConfigValueType.FilePath, None, 'mac_db.json path', 'Path to mac_db.json from ComputerGameDB'),
	'launchers_for_unknown_mac_apps': ConfigValue('Mac', ConfigValueType.Bool, False, 'Launchers for unknown apps', 'Whether or not to create launchers for Mac programs that are found but not in the database'),

	'dos_db_path': ConfigValue('DOS', ConfigValueType.FilePath, None, 'dos_db.json path', 'Path to dos_db.json from ComputerGameDB'),
	'launchers_for_unknown_dos_apps': ConfigValue('DOS', ConfigValueType.Bool, False, 'Launchers for unknown apps', 'Whether or not to create launchers for DOS programs that are found but not in the database'),

	#TODO: Put this in a general section, use it in the other modules
	'normalize_name_case': ConfigValue('Steam', ConfigValueType.Integer, 0, 'Normalize name case', 'Apply title case to uppercase things (1: only if whole title is uppercase, 2: capitalize individual uppercase words, 3: title case the whole thing regardless)'),
	'force_create_launchers': ConfigValue('Steam', ConfigValueType.Bool, False, 'Force create launchers', 'Create launchers even for games which are\'nt launchable'),
	'warn_about_missing_icons': ConfigValue('Steam', ConfigValueType.Bool, False, 'Warn about missing icons', 'Spam console with debug messages about icons not existing or being missing'),

	'skip_mame_non_working_software': ConfigValue('Roms', ConfigValueType.Bool, False, 'Skip MAME non-working software', "Don't attempt to use MAME for ROMs marked as unsupported in software list"),
	'wii_common_key': ConfigValue('Roms', ConfigValueType.String, '', 'Wii common key', 'Wii common key used for decrypting Wii discs which some projects are brave enough to hardcode but I am not'),
	'skipped_subfolder_names': ConfigValue('Roms', ConfigValueType.StringList, [], 'Skipped subfolder names', 'Always skip these subfolders in every ROM dir'),
	'use_mame_system_icons': ConfigValue('Roms', ConfigValueType.Bool, False, 'Use MAME system icons', 'If a game does not have an icon, use the MAME icon for its system if available'),
	'find_equivalent_arcade_games': ConfigValue('Roms', ConfigValueType.Bool, False, 'Find equivalent arcade games by name', 'Get metadata from MAME machines of the same name'),
	#TODO This is evidence that I need to rewrite this whole mess with "specific configs" (what kind of name is that anyway, what the hell was I thinking and how tired was I)
	'find_software_by_name': ConfigValue('Roms', ConfigValueType.StringList, [], 'Systems to find software by name', 'For these platforms, use the filename to match something in the software list'),

	'use_original_platform': ConfigValue('ScummVM', ConfigValueType.Bool, False, 'Use original platform', 'Set the platform in metadata to the original platform instead of leaving blank'),

	#These shouldn't end up in config.ini as they're intended to be set per-run
	'debug': ConfigValue(runtime_option_section, ConfigValueType.Bool, False, 'Debug', 'Enable debug mode, which is really verbose mode, oh well'),
	'print_times': ConfigValue(runtime_option_section, ConfigValueType.Bool, False, 'Print times', 'Print how long it takes to do things'),
	'full_rescan': ConfigValue(runtime_option_section, ConfigValueType.Bool, False, 'Full rescan', 'Regenerate every launcher from scratch instead of just what\'s new and removing what\'s no longer there'),
	'organize_folders': ConfigValue(runtime_option_section, ConfigValueType.Bool, False, 'Organize folders', 'Use the organized folders frontend'),
}
#Hmm... debug could be called 'verbose' and combined with --super_debug used in disambiguate to become verbosity_level or just verbose for short, which could have an integer argument, and it _could_ be in config.ini I guess... ehh whatevs

def get_config_ini_options():
	opts = {}
	for k, v in _config_ini_values.items():
		if v.section == runtime_option_section:
			continue
		if v.section not in opts:
			opts[v.section] = {}
		opts[v.section][k] = v
	return opts

def get_runtime_options():
	return {name: opt for name, opt in _config_ini_values.items() if opt.section == runtime_option_section}

def get_command_line_arguments():
	d = {}
	for i, arg in enumerate(sys.argv):
		if not arg.startswith('--'):
			continue
		arg = arg[2:]

		for name, option in _config_ini_values.items():
			expected_arg = name.replace('_', '-')

			if option.type == ConfigValueType.Bool:
				if arg == '--no-' + expected_arg:
					d[name] = False
				elif arg == expected_arg:
					d[name] = True

			elif arg == expected_arg:
				value = sys.argv[i + 1]
				#TODO: If value = another argument starts with --, invalid?
				#if option.type == ConfigValueType.Bool: #or do I wanna do that
				#	d[name] = parse_command_line_bool(value)
				if option.type in (ConfigValueType.FilePath, ConfigValueType.FolderPath):
					d[name] = os.path.expanduser(value)
				elif option.type in (ConfigValueType.FilePathList, ConfigValueType.FolderPathList):
					d[name] = parse_path_list(value)
				elif option.type == ConfigValueType.StringList:
					d[name] = parse_string_list(value)
				else:
					d[name] = value
	return d

def load_ignored_directories():
	ignored_directories = []

	try:
		with open(_ignored_dirs_path, 'rt') as ignored_txt:
			ignored_directories += ignored_txt.read().splitlines()
	except FileNotFoundError:
		pass

	if '--ignored-directories' in sys.argv:
		#TODO Move to get_command_line_arguments or otherwise somewhere else
		index = sys.argv.index('--ignored-directories')
		arg = sys.argv[index + 1]
		for ignored_dir in parse_path_list(arg):
			ignored_directories.append(ignored_dir)

	ignored_directories = [dir if dir.endswith(os.sep) else dir + os.sep for dir in ignored_directories]

	return ignored_directories

def write_ignored_directories(ignored_dirs):
	try:
		with open(_ignored_dirs_path, 'wt') as ignored_txt:
			for ignored_dir in ignored_dirs:
				ignored_txt.write(ignored_dir)
				ignored_txt.write('\n')
	except OSError as oe:
		print('AAaaaa!!! Failed to write ignored directories file!!', oe)

def write_new_main_config(new_config):
	write_new_config(new_config, _main_config_path)

def write_new_config(new_config, config_file_path):
	parser = configparser.ConfigParser(interpolation=None)
	parser.optionxform = str
	ensure_exist(config_file_path)
	parser.read(config_file_path)
	for section, configs in new_config.items():
		if section not in parser:
			parser.add_section(section)
		for name, value in configs.items():
			parser[section][name] = convert_value_for_ini(value)

	try:
		with open(config_file_path, 'wt') as ini_file:
			parser.write(ini_file)
	except OSError as ex:
		print('Oh no!!! Failed to write', config_file_path, '!!!!11!!eleven!!', ex)

class Config():
	class __Config():
		def __init__(self):
			self.values = {}
			for name, config in _config_ini_values.items():
				self.values[name] = config.default_value

			self.runtime_overrides = get_command_line_arguments()
			self.reread_config()

		def reread_config(self):
			parser = configparser.ConfigParser(interpolation=None)
			parser.optionxform = str
			self.parser = parser
			ensure_exist(_main_config_path)
			self.parser.read(_main_config_path)

			self.ignored_directories = load_ignored_directories()

		def rewrite_config(self):
			with open(_main_config_path, 'wt') as f:
				self.parser.write(f)

		def __getattr__(self, name):
			if name in self.values:
				if name in self.runtime_overrides:
					return self.runtime_overrides[name]
				config = _config_ini_values[name]

				if config.section == runtime_option_section:
					return config.default_value

				if config.section not in self.parser:
					self.parser.add_section(config.section)
					self.rewrite_config()

				section = self.parser[config.section]
				if name not in section:
					section[name] = convert_value_for_ini(config.default_value)
					self.rewrite_config()
					return config.default_value

				return parse_value(section, name, config.type, config.default_value)

			raise AttributeError(name)

	__instance = None

	@staticmethod
	def getConfig():
		if Config.__instance is None:
			Config.__instance = Config.__Config()
		return Config.__instance

main_config = Config.getConfig()

class SystemConfig():
	def __init__(self, name):
		self.name = name
		self.paths = []
		self.chosen_emulators = []
		self.specific_config = {}

	@property
	def is_available(self):
		return bool(self.paths) and bool(self.chosen_emulators)

class SystemConfigs():
	class __SystemConfigs():
		def __init__(self):
			self.configs = {} #This will be an array of SystemConfig objects and that's fine and I don't think I need to refactor that right now
			self.read_configs_from_file()

		def read_configs_from_file(self):
			parser = configparser.ConfigParser(interpolation=None, delimiters=('='), allow_no_value=True)
			parser.optionxform = str

			ensure_exist(_system_config_path)
			parser.read(_system_config_path)

			for system_name in parser.sections():
				self.configs[system_name] = SystemConfig(system_name)

				section = parser[system_name]
				self.configs[system_name].paths = parse_path_list(section.get('paths', ''))
				chosen_emulators = []
				for s in parse_string_list(section.get('emulators', '')):
					if s in ('MAME', 'Mednafen', 'VICE'):
					#Allow for convenient shortcut
						s = '{0} ({1})'.format(s, system_name)
					chosen_emulators.append(s)
				self.configs[system_name].chosen_emulators = chosen_emulators
				if system_name in systems:
					#Hmm… having to import systems for this doesn't seem right
					specific_configs = systems[system_name].specific_configs
					for k, v in specific_configs.items():
						self.configs[system_name].specific_config[k] = parse_value(section, k, v.type, v.default_value)
				elif system_name in computer_systems:
					specific_configs = computer_systems[system_name].specific_configs
					for k, v in specific_configs.items():
						self.configs[system_name].specific_config[k] = parse_value(section, k, v.type, v.default_value)
						
	__instance = None

	@staticmethod
	def getConfigs():
		if SystemConfigs.__instance is None:
			SystemConfigs.__instance = SystemConfigs.__SystemConfigs()
		return SystemConfigs.__instance

system_configs = SystemConfigs.getConfigs()

#--regen-dos-config is used in emulator_command_lines... should I move it here?
