#!/usr/bin/env python3

import os

import launchers
import pc
from common_types import EmulationNotSupportedException, NotARomException
from config.main_config import main_config
from config.system_config import system_configs
from info.emulator_info import dos_emulators
from pc_common_metadata import look_for_icon_next_to_file

dos_config = system_configs.get('DOS')

class DOSApp(pc.App):
	@property
	def is_valid(self):
		return os.path.isfile(self.path)

	def additional_metadata(self):
		self.metadata.platform = 'DOS'
		_, extension = os.path.splitext(self.path)
		self.metadata.extension = extension[1:].lower()
		icon = look_for_icon_next_to_file(self.path)
		if icon:
			self.metadata.images['Icon'] = icon

	def make_launcher(self):
		emulator_name = None
		params = None
		exception_reason = None
		for emulator in dos_config.chosen_emulators:
			emulator_name = emulator
			try:
				params = dos_emulators[emulator].get_launch_params(self, dos_config.options)
				if params:
					break
			except (EmulationNotSupportedException, NotARomException) as ex:
				exception_reason = ex

		if not params:
			if main_config.debug:
				print(self.path, 'could not be launched by', dos_config.chosen_emulators, 'because', exception_reason)
			return

		self.metadata.emulator_name = emulator_name
		launchers.make_launcher(params, self.name, self.metadata, 'DOS', self.path)

def make_dos_launchers():
	if dos_config:
		if not dos_config.chosen_emulators:
			return
		pc.make_launchers('DOS', DOSApp)

# def scan_app(path, exe_name, game_list, unknown_games, found_games, ambiguous_games):
# 	possible_games = [(game_name, game_config) for game_name, game_config in game_list.items() if game_config['app_name'].lower() == exe_name]
# 	if not possible_games:
# 		unknown_games.append(path)
# 	elif len(possible_games) == 1:
# 		found_games[path] = possible_games[0][0]
# 	else:
# 		ambiguous_games[path] = [game_name for game_name, game_config in possible_games]

# def scan_dos_folder(path, game_list, unknown_games, found_games, ambiguous_games):
# 	for root, _, files in os.walk(path):
# 		if common.starts_with_any(root + os.sep, main_config.ignored_directories):
# 			continue
# 		for name in files:
# 			ext = os.path.splitext(name)[1][1:].lower()
# 			if ext not in ('exe', 'com', 'bat'):
# 				continue

# 			path = os.path.join(root, name)
# 			scan_app(path, name.lower(), game_list, unknown_games, found_games, ambiguous_games)

if __name__ == '__main__':
	make_dos_launchers()
