import sys

from metadata import SaveType, InputType, PlayerInput
from info.region_info import TVSystem
from software_list_info import get_software_list_entry

debug = '--debug' in sys.argv

input_types = {
	1: (InputType.Digital, 2),
	2: (InputType.LightGun, 1),
	3: (InputType.Paddle, 1),
	4: (InputType.Trackball, 1),
}

def _add_atari_7800_header_info(game, header):
	left_input_type = header[55]
	right_input_type = header[56]
	if left_input_type != 0:
		player = PlayerInput()
		if left_input_type in input_types:
			input_type, buttons = input_types[left_input_type]
			player.buttons = buttons
			player.inputs = [input_type]
		else:
			player.inputs = [InputType.Custom]
		game.metadata.input_info.players.append(player)
	if right_input_type != 0:
		#TODO: Refactor to avoid duplication
		player = PlayerInput()
		if right_input_type in input_types:
			input_type, buttons = input_types[right_input_type]
			player.buttons = buttons
			player.inputs = [input_type]
		else:
			player.inputs = [InputType.Custom]
		game.metadata.input_info.players.append(player)

	tv_type = header[57]

	if tv_type == 1:
		game.metadata.tv_type = TVSystem.PAL
	elif tv_type == 0:
		game.metadata.tv_type = TVSystem.NTSC
	else:
		if debug:
			print('Something is wrong with', game.rom.path, ', has TV type byte of', tv_type)
		game.metadata.specific_info['Invalid-TV-Type'] = True

	save_type = header[58]
	if save_type == 0:
		game.metadata.save_type = SaveType.Nothing
	elif save_type == 1:
		#High Score Cart, an unreleased device that ends up being supported by some games (apparently). Just saves high scores so don't get too excited. It doesn't seem to be supported by MAME which is the only 7800 emulator we use anyway.
		#You plug the High Score Cart into the 7800 and then the game into the High Score Cart, so I guess this is the easiest thing to call it.
		game.metadata.save_type = SaveType.Internal
	elif save_type == 2:
		#AtariVox/SaveKey. Both are third party products which plug into the controller port, so what else can you call them except memory cards?
		game.metadata.save_type = SaveType.MemoryCard
	elif debug:
		print(game.rom.path, 'has save type byte of ', save_type)

def add_atari_7800_metadata(game):
	game.metadata.input_info.console_buttons = 3 #Pause, select, reset

	header = game.rom.read(amount=128)
	if header[1:10] == b'ATARI7800':
		headered = True
		_add_atari_7800_header_info(game, header)
	else:
		headered = False

	game.metadata.specific_info['Headered'] = headered

	software = get_software_list_entry(game, skip_header = 128 if headered else 0)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')
		#Don't need sharedfeat > compatibility to get TV type or feature > peripheral, unheadered roms won't work anyway
