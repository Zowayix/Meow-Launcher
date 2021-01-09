import configparser
import os
import pathlib
import re
import shlex
from enum import Enum

import common
from config.main_config import main_config
from io_utils import ensure_exist

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

metadata_section_name = 'X-Meow Launcher Metadata'
id_section_name = 'X-Meow Launcher ID'
junk_section_name = 'X-Meow Launcher Junk'
image_section_name = 'X-Meow Launcher Images'
name_section_name = 'X-Meow Launcher Names'

def get_desktop(path):
	parser = configparser.ConfigParser(interpolation=None)
	parser.optionxform = str #Can you actually fuck off?
	parser.read(path)
	return parser

def get_field(desktop, name, section=metadata_section_name):
	if section not in desktop:
		return None

	entry = desktop[section]
	if name in entry:
		return entry[name]

	return None

def get_array(desktop, name, section=metadata_section_name):
	field = get_field(desktop, name, section)
	if field is None:
		return []

	return field.split(';')

remove_brackety_things_for_filename = re.compile(r'[]([)]')
clean_for_filename = re.compile(r'[^A-Za-z0-9_]')
def make_filename(name):
	name = name.lower()
	name = remove_brackety_things_for_filename.sub('', name)
	name = clean_for_filename.sub('-', name)
	while name.startswith('-'):
		name = name[1:]
	if not name:
		name = 'blank'
	return name

class LaunchParams():
	def __init__(self, exe_name, exe_args, env_vars=None, working_directory=None):
		self.exe_name = exe_name
		self.exe_args = exe_args
		self.env_vars = {} if env_vars is None else env_vars
		self.working_directory = working_directory

	def make_linux_command_string(self):
		exe_args_quoted = ' '.join(shlex.quote(arg) for arg in self.exe_args)
		exe_name_quoted = shlex.quote(self.exe_name)
		if self.env_vars:
			environment_vars = ' '.join([shlex.quote(k + '=' + v) for k, v in self.env_vars.items()])
			return 'env {0} {1} {2}'.format(environment_vars, exe_name_quoted, exe_args_quoted)
		if not self.exe_name: #Wait, when does this ever happen? Why is this here?
			return exe_args_quoted
		return exe_name_quoted + ' ' + exe_args_quoted

	def prepend_command(self, launch_params):
		multi_command = MultiCommandLaunchParams([self])
		return multi_command.prepend_command(launch_params)

	def append_command(self, launch_params):
		multi_command = MultiCommandLaunchParams([self])
		return multi_command.append_command(launch_params)

	def replace_path_argument(self, path):
		return LaunchParams(self.exe_name, [arg.replace('$<path>', path) for arg in self.exe_args], self.env_vars)

class MultiCommandLaunchParams():
	#I think this shouldn't inherit from LaunchParams because duck typing (but doesn't actually reuse anything from LaunchParams). I _think_ I know what I'm doing. Might not.
	def __init__(self, commands):
		self.commands = commands

	def make_linux_command_string(self):
		#Purrhaps I should add an additional field for this object to use ; instead of &&
		return 'sh -c ' + shlex.quote(' && '.join([command.make_linux_command_string() for command in self.commands]))

	def prepend_command(self, launch_params):
		commands = self.commands
		commands.insert(0, launch_params)
		return MultiCommandLaunchParams(commands)

	def append_command(self, launch_params):
		commands = self.commands
		commands.append(launch_params)
		return MultiCommandLaunchParams(commands)

	def replace_path_argument(self, path):
		new_commands = [command.replace_path_argument(path) for command in self.commands]
		return MultiCommandLaunchParams(new_commands)

def pick_new_filename(folder, display_name, extension):
	base_filename = make_filename(display_name)
	filename = base_filename + os.extsep + extension

	i = 2
	while os.path.isfile(os.path.join(folder, filename)):
		filename = base_filename + str(i) + os.extsep + extension
		i += 1
	return filename

def make_linux_desktop(launch_params, display_name, fields=None):
	filename = pick_new_filename(main_config.output_folder, display_name, 'desktop')
	
	path = os.path.join(main_config.output_folder, filename)

	configwriter = configparser.ConfigParser(interpolation=None)
	configwriter.optionxform = str

	configwriter.add_section('Desktop Entry')
	desktop_entry = configwriter['Desktop Entry']

	#Necessary for this thing to even be recognized
	desktop_entry['Type'] = 'Application'
	desktop_entry['Encoding'] = 'UTF-8'

	desktop_entry['Name'] = display_name
	desktop_entry['Exec'] = launch_params.make_linux_command_string()
	if launch_params.working_directory:
		desktop_entry['Path'] = launch_params.working_directory

	if fields:
		for section_name, section in fields.items():
			if not section:
				continue
			configwriter.add_section(section_name)
			section_writer = configwriter[section_name]

			for k, v in section.items():
				if v is None:
					continue

				use_image_object = False
				value_as_string = None
				if have_pillow:
					if isinstance(v, Image.Image):
						use_image_object = True
						this_image_folder = os.path.join(main_config.image_folder, k)
						pathlib.Path(this_image_folder).mkdir(exist_ok=True, parents=True)
						image_path = os.path.join(this_image_folder, filename + '.png')
						v.save(image_path, 'png')
						value_as_string = image_path

				if isinstance(v, list):
					if not v:
						continue
					value_as_string = ';'.join(['None' if item is None else item.name if isinstance(item, Enum) else str(item) for item in v])
				elif isinstance(v, Enum):
					value_as_string = v.name
				#else:
				elif not use_image_object:
					value_as_string = str(v)

				value_as_string = common.clean_string(value_as_string)
				section_writer[k.replace('_', '-')] = value_as_string

	if image_section_name in configwriter:
		keys_to_try = ['Icon'] + main_config.use_other_images_as_icons
		for k in keys_to_try:
			if k in configwriter[image_section_name]:
				desktop_entry['Icon'] = configwriter[image_section_name][k]
				break

	ensure_exist(path)
	with open(path, 'wt') as f:
		configwriter.write(f)

	#Set executable, but also set everything else because whatever
	os.chmod(path, 0o7777)

split_brackets = re.compile(r' (?=\()')
def make_launcher(launch_params, name, metadata, id_type, unique_id):
	display_name = common.remove_filename_tags(name)
	filename_tags = common.find_filename_tags_at_end(name)

	fields = metadata.to_launcher_fields()

	if filename_tags:
		fields[junk_section_name]['Filename-Tags'] = filename_tags
	fields[junk_section_name]['Original-Name'] = name

	fields[id_section_name] = {}
	fields[id_section_name]['Type'] = id_type
	fields[id_section_name]['Unique-ID'] = unique_id

	#For very future use, this is where the underlying host platform is abstracted away. Right now we only run on Linux though so zzzzz
	make_linux_desktop(launch_params, display_name, fields)

def _get_existing_launchers():
	a = []

	output_folder = main_config.output_folder
	if not os.path.isdir(output_folder):
		return []
	for name in os.listdir(output_folder):
		path = os.path.join(output_folder, name)

		existing_launcher = get_desktop(path)
		existing_type = get_field(existing_launcher, 'Type', id_section_name)
		existing_id = get_field(existing_launcher, 'Unique-ID', id_section_name)
		a.append((existing_type, existing_id))

	return a
_existing_launchers = None

def has_been_done(game_type, game_id):
	global _existing_launchers #Of course it's global you dicktwat. I swear to fuck this fucking language sometimes, I just wanted to lazy initialize a variable why do you have to make this difficult by making me put spooky keywords in there or forcing me to write some boilerplate shit involving classes and decorators instead, if I wanted to write verbose bullshit I'd program in fucking Java, fuck off
	if _existing_launchers is None:
		_existing_launchers = _get_existing_launchers()

	for existing_type, existing_id in _existing_launchers:
		if existing_type == game_type and existing_id == game_id:
			return True

	return False
