import configparser
import hashlib
import os

import input_metadata
from common import NotAlphanumericException, convert_alphanumeric, byteswap
from common_types import SaveType
from software_list_info import get_software_list_entry

_mupen64plus_database = None
def get_mupen64plus_database():
	global _mupen64plus_database
	if _mupen64plus_database:
		return _mupen64plus_database

	locations = ['/usr/share/mupen64plus/mupen64plus.ini', '/usr/local/share/mupen64plus/mupen64plus.ini']
	location = None
	for possible_location in locations:
		if os.path.isfile(possible_location):
			location = possible_location
			break

	if not location:
		return None

	parser = configparser.ConfigParser(interpolation=None)
	parser.optionxform = str
	parser.read(location)

	database = {section: dict(parser.items(section)) for section in parser.sections()}
	for game, keypairs in database.items():
		if 'RefMD5' in keypairs:
			parent_md5 = keypairs['RefMD5']
			if parent_md5 in database:
				parent = database[parent_md5]
				for parent_key, parent_value in parent.items():
					if parent_key in database[game]:
						continue
					database[game][parent_key] = parent_value

	_mupen64plus_database = database
	return database

def parse_n64_header(metadata, header):
	#Clock rate, apparently? 0:4
	#Program counter: 4-8
	#Release address: 8-12
	#Checksum: 12-16
	#Checksum 2: 16-20
	#Zero filled: 20-28
	internal_title = header[28:52].decode('shift_jis', errors='backslashreplace').rstrip('\0')
	if internal_title:
		metadata.specific_info['Internal-Title'] = internal_title
	#Unknown: 52-59
	try:
		product_code = convert_alphanumeric(header[59:63])
		metadata.product_code = product_code
	except NotAlphanumericException:
		pass
	metadata.specific_info['Revision'] = header[63]

def add_info_from_database_entry(metadata, database_entry):
	#Keys: {'SaveType', 'Biopak', 'GoodName', 'SiDmaDuration', 'Players', 'DisableExtraMem', 'Mempak', 'Cheat0', 'Transferpak', 'CRC', 'Status', 'Rumble', 'CountPerOp'}
	#CRC is just the N64 checksum from the ROM header so I dunno if that's any use
	#Stuff like SiDmaDuration and CountPerOp and DisableExtraMem should be applied automatically by Mupen64Plus I would think (and be irrelevant for other emulators)
	#Likewise Cheat0 is just a quick patch to workaround emulator issues, so it doesn't need to be worried about here
	#Status seems... out of date

	#This is just here for debugging etc
	metadata.add_alternate_name(database_entry.get('GoodName'), 'GoodName')

	if 'Players' in database_entry:
		metadata.specific_info['Number-of-Players'] = database_entry['Players']

	if database_entry.get('SaveType', 'None') != 'None':
		metadata.save_type = SaveType.Cart
	elif database_entry.get('Mempak', 'No') == 'Yes':
		#Apparently it is possible to have both cart and memory card saving, so that is strange
		#I would think though that if the cartridge could save everything it needed to, it wouldn't bother with a memory card, so if it does use the controller pak then that's probably the main form of saving
		metadata.specific_info['Uses-Controller-Pak'] = True
		metadata.save_type = SaveType.MemoryCard
	else:
		#TODO: iQue would be SaveType.Internal, could maybe detect that based on CIC but that might be silly (the saving wouldn't be emulated by anything at this point anyway)
		metadata.save_type = SaveType.Nothing

	if database_entry.get('Rumble', 'No') == 'Yes':
		metadata.specific_info['Force-Feedback'] = True
	if database_entry.get('Biopak', 'No') == 'Yes':
		metadata.input_info.input_options[0].inputs.append(input_metadata.Biological())
	if database_entry.get('Transferpak', 'No') == 'Yes':
		metadata.specific_info['Uses-Transfer-Pak'] = True
	#Unfortunately nothing in here which specifies to use VRU, or any other weird fancy controllers which may or may not exist

def add_n64_metadata(game):
	entire_rom = game.rom.read()

	magic = entire_rom[:4]

	is_byteswapped = False
	if magic == b'\x80\x37\x12\x40':
		game.metadata.specific_info['ROM-Format'] = 'Z64'
	elif magic == b'\x37\x80\x40\x12':
		is_byteswapped = True
		game.metadata.specific_info['ROM-Format'] = 'V64'
	else:
		#TODO: Detect other formats (there are a few homebrews that start with 0x80 0x37 but not 0x12 0x40 after that, which may be launchable on some emulators but not on others)
		game.metadata.specific_info['ROM-Format'] = 'Unknown'
		return

	header = entire_rom[:64]
	if is_byteswapped:
		header = byteswap(header)

	parse_n64_header(game.metadata, header)

	normal_controller = input_metadata.NormalController()
	normal_controller.face_buttons = 6 #A, B, 4 * C
	normal_controller.shoulder_buttons = 3 #L, R, and I guess Z will have to be counted as a shoulder button
	normal_controller.analog_sticks = 1
	normal_controller.dpads = 1
	game.metadata.input_info.add_option(normal_controller)

	database = get_mupen64plus_database()
	if database:
		rom_md5 = hashlib.md5(entire_rom).hexdigest().upper()
		database_entry = database.get(rom_md5)
		if database_entry:
			add_info_from_database_entry(game.metadata, database_entry)

	software = get_software_list_entry(game)
	if software:
		software.add_standard_metadata(game.metadata)
