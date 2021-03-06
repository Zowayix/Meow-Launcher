from zlib import crc32

import input_metadata
from common import NotAlphanumericException, convert_alphanumeric
from common_types import SaveType
from data.nintendo_licensee_codes import nintendo_licensee_codes
from info.region_info import TVSystem
from software_list_info import get_software_list_entry

nintendo_gba_logo_crc32 = 0xD0BEB55E
def parse_gba_header(metadata, header):
	#Entry point: 0-4
	nintendo_logo = header[4:0xa0]
	nintendo_logo_valid = crc32(nintendo_logo) == nintendo_gba_logo_crc32
	metadata.specific_info['Nintendo-Logo-Valid'] = nintendo_logo_valid
	
	internal_title = header[0xa0:0xac].decode('ascii', errors='backslashreplace').rstrip('\0')
	metadata.specific_info['Internal-Title'] = internal_title
	if internal_title == 'mb2gba':
		return
	
	product_code = None
	try:
		product_code = convert_alphanumeric(header[0xac:0xb0])
		if len(product_code) == 4:
			game_type = product_code[0]
			if game_type in ('K', 'R'):
				metadata.input_info.input_options[0].inputs.append(input_metadata.MotionControls())
			metadata.specific_info['Force-Feedback'] = game_type in ('R', 'V')

			metadata.product_code = product_code
	except NotAlphanumericException:
		pass

	licensee_code = None
	try:
		licensee_code = convert_alphanumeric(header[0xb0:0xb2])

		if licensee_code in nintendo_licensee_codes:
			metadata.publisher = nintendo_licensee_codes[licensee_code]
	except NotAlphanumericException:
		pass

	#"Fixed value": 0xb2, apparently should be 0x96
	#Main unit code: 0xb3, apparently should be 0
	#Device type: 0xb4, apparently normally should be 0
	#Reserved: 0xb5 - 0xbc

	metadata.specific_info['Revision'] = header[0xbc]

	#Checksum (see ROMniscience for how to calculate it, because I don't feel like describing it all in a single line of comment): 0xbd
	#Reserved: 0xbe - 0xc0

def look_for_strings_in_cart(entire_cart, metadata):
	has_save = False
	save_strings = [b'EEPROM_V', b'SRAM_V', b'SRAM_F_V', b'FLASH_V', b'FLASH512_V', b'FLASH1M_V']
	for string in save_strings:
		if string in entire_cart:
			has_save = True
			break
	metadata.specific_info['Has-RTC'] = b'SIIRTC_V' in entire_cart
	metadata.specific_info['Uses-Wireless-Adapter'] = b'RFU_V10' in entire_cart
	metadata.save_type = SaveType.Cart if has_save else SaveType.Nothing

	if b'AUDIO ERROR, too many notes on channel 0.increase polyphony RAM' in entire_cart:
		#Look for Rare sound driver because I can
		metadata.developer = 'Rare'


def add_gba_metadata(game):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2 #A B
	builtin_gamepad.shoulder_buttons = 2 #L R
	game.metadata.input_info.add_option(builtin_gamepad)

	game.metadata.tv_type = TVSystem.Agnostic

	entire_cart = game.rom.read()
	if len(entire_cart) >= 0xc0:
		header = entire_cart[0:0xc0]
		parse_gba_header(game.metadata, header)

	look_for_strings_in_cart(entire_cart, game.metadata)

	software = get_software_list_entry(game)
	if software:
		software.add_standard_metadata(game.metadata)
