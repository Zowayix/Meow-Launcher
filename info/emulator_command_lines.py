import shlex
import os
import sys

from .region_info import TVSystem

debug = '--debug' in sys.argv

#Guess we just have to duplicate this info here to avoid circular references
mame_floppy_formats = ['d77', 'd88', '1dd', 'dfi', 'hfe', 'imd', 'ipf', 'mfi', 'mfm', 'td0', 'cqm', 'cqi', 'dsk']

def _get_autoboot_script_by_name(name):
	this_package = os.path.dirname(__file__)
	root_package = os.path.dirname(this_package)
	return os.path.join(root_package, 'mame_autoboot', name + '.lua')

def make_mednafen_command_line(module):
	return 'mednafen -video.fs 1 -force_module %s $<path>' % module

def mame_command_line(driver, slot=None, slot_options=None, has_keyboard=False, autoboot_script=None):
	command_line = 'mame -skip_gameinfo'
	if has_keyboard:
		command_line += ' -ui_active'

	command_line += ' ' + driver

	if slot_options:
		for name, value in slot_options.items():
			command_line += ' -' + name + ' ' + value

	if slot:
		command_line += ' -' + slot + ' $<path>'

	if autoboot_script:
		command_line += ' -autoboot_script ' + shlex.quote(_get_autoboot_script_by_name(autoboot_script))

	return command_line

def mame_atari_7800(game, _):
	if not game.metadata.specific_info.get('Headered', False):
		if debug:
			print(game.rom.path, 'has no header and is therefore unsupported')
		return None

	if game.metadata.tv_type == TVSystem.PAL:
		system = 'a7800p'
	else:
		system = 'a7800'

	return mame_command_line(system, 'cart')

def mame_vic_20(game, _):
	size = game.rom.get_size()
	if size > ((8 * 1024) + 2):
		#It too damn big (only likes 8KB with 2 byte header at most)
		if debug:
			print('Bugger!', game.rom.path, 'is too big for MAME at the moment, it is', size)
		return None
	
	if game.metadata.tv_type == TVSystem.PAL:
		system = 'vic20p'
	else:
		system = 'vic20'

	return mame_command_line(system, 'cart', {'iec8': '""'}, has_keyboard=True)
		
def mame_atari_8bit(game, _):
	if game.metadata.specific_info.get('Headered', False):
		cart_type = game.metadata.specific_info['Cart-Type']
		if cart_type in (13, 14, 23, 24, 25) or (cart_type >= 33 and cart_type <= 38):
			if debug:
				print(game.rom.path, 'is actually a XEGS ROM which is not supported by MAME yet, cart type is', cart_type)
			return None
			
		#You probably think this is a bad way to do this...  I guess it is, but hopefully I can take some out as they become supported
		if cart_type in (5, 17, 22, 41, 42, 43, 45, 46, 47, 48, 49, 53, 57, 58, 59, 60, 61) or (cart_type >= 26 and cart_type <= 32) or (cart_type >= 54 and cart_type <= 56):
			if debug:
				print(game.rom.path, "won't work as cart type is", cart_type)
			return None

		if cart_type in (4, 6, 7, 16, 19, 20):
			if debug:
				print(game.rom.path, "is an Atari 5200 ROM ya goose!! It won't work as an Atari 800 ROM as the type is", cart_type)
			return None		
	else:
		size = game.rom.get_size()
		#Treat 8KB files as type 1, 16KB as type 2, everything else is unsupported for now
		if size > ((16 * 1024) + 16):
			if debug:
				print(game.rom.path, 'may actually be a XL/XE/XEGS cartridge, please check it as it has no header and a size of', size)
			return None
	
	slot = 'cart1' if game.metadata.specific_info.get('Slot', 'Left') == 'Left' else 'cart2'

	if game.metadata.tv_type == TVSystem.PAL:
		#Atari 800 should be fine for everything, and I don't feel like the XL/XE series to see in which ways they don't work
		system = 'a800p'
	else:
		system = 'a800'

	return mame_command_line(system, slot, has_keyboard=True)

def _find_c64_system(game):
	if game.metadata.platform == 'C64GS':	
		#For some reason, C64GS carts don't work on a regular C64 in MAME, and we have to use...  the thing specifically designed for playing games (but we normally wouldn't use this, since some cartridge games still need the keyboard, even if just for the menus, and that's why it actually sucks titty balls IRL.  But if it weren't for that, we totes heckin would)
		#Note that C64GS doesn't really work properly in MAME anyway, but the carts... not work... less than in the regular C64 driver
		return 'c64gs'
	
	#Don't think we really need c64c unless we really want the different SID chip
	
	if game.metadata.tv_type == TVSystem.PAL:
		return 'c64p'
	
	return 'c64'
	
def mame_c64(game, _):
	#While we're here building a command line, should mention that you have to manually put a joystick in the first
	#joystick port, because by default there's only a joystick in the second port.  Why the fuck is that the default?
	#Most games use the first port (although, just to be annoying, some do indeed use the second...  why????)
	#Anyway, might as well use this "Boostergrip" thingy, or really it's like using the C64GS joystick, because it just
	#gives us two extra buttons for any software that uses it (probably nothing), and the normal fire button works as
	#normal.  _Should_ be fine
	#(Super cool pro tip: Bind F1 to Start)

	#For supported cart types, see: https://github.com/mamedev/mame/blob/master/src/lib/formats/cbm_crt.cpp
	#15 (System 3/C64GS) does seem to be a bit weird too, oh well
	#Maybe check the software list for compatibility
	if game.metadata.specific_info.get('Cart-Type', None) == 18:
		#Sega (Zaxxon/Super Zaxxon), nothing in the source there that says it's unsupported, but it consistently segfaults every time I try to launch it, so I guess it doesn't actually work
		return None
	if game.metadata.specific_info.get('Cart-Type', None) == 32:
		#EasyFlash. Well, at least it doesn't segfault. Just doesn't boot, even if I play with the dip switch that says "Boot". Maybe I'm missing something here?
		#There's a Prince of Persia cart in c64_cart.xml that uses easyflash type and is listed as being perfectly supported, but maybe it's one of those things where it'll work from the software list but not as a normal ROM (it's broken up into multiple ROMs)
		return None	

	system = _find_c64_system(game)
	return mame_command_line(system, 'cart', {'joy1': 'joybstr', 'joy2': 'joybstr', 'iec8': '""'}, True)

def mgba(game, _):
	command_line = 'mgba-qt -f'
	if not game.metadata.specific_info.get('Nintendo-Logo-Valid', True):
		command_line += ' -C useBios=0'
	return command_line + ' $<path>'

def medusa(game, _):
	if game.metadata.platform == 'DSi' or game.metadata.specific_info.get('Is-iQue', False):
		return None
	return 'medusa-emu-qt -f $<path>'

def gambatte(game, _):
	mapper = game.metadata.specific_info.get('Mapper', None)
	if not mapper:
		#If there was a problem detecting the mapper, or it's something invalid, it probably won't run
		if debug:
			print('Skipping', game.rom.path, '(by Gambatte) because mapper is unrecognized')
		return None
	if mapper.name in ['Bandai TAMA5', 'HuC3', 'MBC6', 'MBC7', 'Pocket Camera']:
		return None		

	return 'gambatte_qt --full-screen $<path>'

def mame_snes(game, other_config):
	#Snes9x's GTK+ port doesn't let us load carts with slots for other carts from the command line yet, so this will have
	#to do, but unfortunately it's a tad slower
	if game.rom.extension == 'st':
		if 'sufami_turbo_bios_path' not in other_config:
			if debug:
				#TODO Only print this once!
				print("You can't do", game.rom.path, "because you haven't set up the BIOS for it yet, check emulators.ini")
			return None

		#We don't need to detect TV type because the Sufami Turbo (and also BS-X) was only released in Japan and so the Super Famicom can be used for everything
		return mame_command_line('snes', 'cart2', {'cart': shlex.quote(other_config['sufami_turbo_bios_path'])}, False)
	
	if game.rom.extension == 'bs':
		if 'bsx_bios_path' not in other_config:
			if debug:
				#TODO Only print this once!
				print("You can't do", game.rom.path, "because you haven't set up the BIOS for it yet, check emulators.ini")
			return None

		return mame_command_line('snes', 'cart2', {'cart': shlex.quote(other_config['bsx_bios_path'])}, False)
	
	if game.metadata.tv_type == TVSystem.PAL:
		system = 'snespal'
	else:
		#American SNES and Super Famicom are considered to be the same system, so that works out nicely
		system = 'snes'

	return mame_command_line(system, 'cart')

def mame_nes(game, _):
	if game.rom.extension == 'fds':
		#We don't need to detect TV type because the FDS was only released in Japan and so the Famicom can be used for everything
		return mame_command_line('fds', 'flop')
	
	uses_sb486 = False

	#27 and 103 might be unsupported too?
	unsupported_ines_mappers = (29, 30, 55, 59, 60, 81, 84, 98,
	99, 100, 101, 102, 109, 110, 111, 122, 124, 125, 127, 128, 
	129, 130, 131, 135, 151, 161, 169, 170, 174, 181, 219, 220, 
	236, 237, 239, 247, 248, 251, 253)
	if game.metadata.specific_info.get('Header-Format', None) == 'iNES':
		mapper = game.metadata.specific_info['Mapper-Number']
		if mapper in unsupported_ines_mappers:
			#if debug:
			#	print(game.rom.path, 'contains unsupported mapper', game.metadata.specific_info['Mapper'], '(%s)' % mapper)
			return None
		if mapper == 167:
			#This might not be true for all games with this mapper, I dunno, hopefully it's about right.
			#At any rate, Subor - English Word Blaster needs to be used with the keyboard thing it's designed for
			uses_sb486 = True
		
	#TODO: Use dendy if we can know the game uses it	
	#TODO: Set up controller ports if game uses Zapper, etc
	if uses_sb486:
		system = 'sb486'
	elif game.metadata.tv_type == TVSystem.PAL:
		system = 'nespal'
	else:
		#There's both a "famicom" driver and also a "nes" driver which does include the Famicom (as well as NTSC NES), so that's weird
		#Gonna presume this works, though
		system = 'nes'

	return mame_command_line(system, 'cart', has_keyboard=uses_sb486)

def mame_atari_2600(game, _):
	if game.rom.get_size() > (512 * 1024):
		if debug:
			print(game.rom.path, "can't be run by MAME a2600 as it's too big")
		return None
	#TODO: Switch based on input type
	if game.metadata.tv_type == TVSystem.PAL:
		system = 'a2600p'
	else:
		system = 'a2600'

	return mame_command_line(system, 'cart')

def mame_zx_spectrum(game, _):
	#TODO: Add casettes and ROMs; former will require autoboot_script, I don't know enough about the latter but it seems to use exp = intf2
	#Maybe quickload things? Do those do anything useful?
	options = {}
	if game.rom.extension in mame_floppy_formats:
		system = 'specpls3'
		slot = 'flop1'
		#If only one floppy is needed, you can add -upd765:1 "" to the commmand line and use just "flop" instead of "flop1".
		#Seemingly the "exp" port doesn't do anything, so we can't attach a Kempston interface. Otherwise, we could use this for snapshots and tape games too.
	else:
		#No harm in using this for 48K games, it works fine, and saves us from having to detect which model a game is designed for. Seems to be completely backwards compatible, which is a relief.
		#We do need to plug in the Kempston interface ourselves, though; that's fine. Apparently how the ZX Interface 2 works is that it just maps joystick input to keyboard input, so we don't really need it, but I could be wrong and thinking of something else entirely.
		system = 'spec128'
		slot = 'dump'
		options['exp'] = 'kempjoy'

	return mame_command_line(system, slot, options, True)

def dolphin(game, _):
	if game.metadata.specific_info.get('No-Disc-Magic', False):
		if debug:
			print(game.rom.path, 'has no disc magic')
		return None

	return 'dolphin-emu -b -e $<path>'

def citra(game, _):
	if game.rom.extension != '3dsx':
		if not game.metadata.specific_info.get('Has-SMDH', False):
			if debug:
				print('Skipping', game.rom.path, 'because no SMDH')
			return None
		if not game.metadata.specific_info.get('Decrypted', True):
			if debug:
				print('Skipping', game.rom.path, 'because encrypted')
			return None
		if not game.metadata.specific_info.get('Is-CXI', True):
			if debug:
				print('Skipping', game.rom.path, 'because not CXI')
			return None
	return 'citra-qt $<path>'

def kega_fusion(game, _):
	if game.rom.extension == 'md' and game.metadata.platform != 'Mega Drive':
		#Probably just a readme file or similar
		return None
	if game.rom.extension == 'bin' and game.metadata.platform == 'Mega CD':
		#Prefer the .cue of .bin/.cue images
		return None
	return 'kega-fusion -fullscreen $<path>'

def mednafen_nes(game, _):
	#Yeah okay, I need a cleaner way of doing this
	unsupported_ines_mappers = (14, 20, 27, 28, 29, 30, 31, 35, 36, 39, 43, 50, 
		53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 81, 83, 84, 91, 98, 100, 
		102, 103, 104, 106, 108, 109, 110, 111, 116, 136, 137, 138, 139, 141, 
		142, 143, 181, 183, 186, 187, 188, 191, 192, 211, 212, 213, 214, 216,
		218, 219, 220, 221, 223, 224, 225, 226, 227, 229, 230, 231, 233, 235,
		236, 237, 238, 239, 243, 245)
	unsupported_ines_mappers += tuple(range(120, 133))
	unsupported_ines_mappers += tuple(range(145, 150))
	unsupported_ines_mappers += tuple(range(161, 180))
	unsupported_ines_mappers += tuple(range(194, 206))
	
	if game.metadata.specific_info.get('Header-Format', None) == 'iNES':
		mapper = game.metadata.specific_info['Mapper-Number']
		if mapper in unsupported_ines_mappers:
			#if debug:
			#	print(game.rom.path, 'contains unsupported mapper', game.metadata.specific_info['Mapper'], '(%s)' % mapper)
			return None

	return make_mednafen_command_line('nes')

def reicast(game, _):
	if game.metadata.specific_info.get('Uses-Windows-CE', False):
		if debug:
			print(game.rom.path, 'is not supported because it uses Windows CE')
		return None
	return 'reicast -config x11:fullscreen=1 $<path>'

def mame_sg1000(game, _):
	#TODO: SC-3000 casettes (wav bit)
	slot_options = {}
	has_keyboard = False

	ext = game.rom.extension
	if ext in mame_floppy_formats or ext == 'sf7':
		system = 'sf7000'
		slot = 'flop'
		has_keyboard = True
		#There are standard Centronics and RS-232 ports/devices available with this, but would I really need them?
	elif ext == 'sc':
		#SC-3000H is supposedly identical except it has a mechanical keyboard. Not sure why sc3000h is a separate driver, but oh well
		system = 'sc3000' 
		slot = 'cart'
		has_keyboard = True
	elif ext in ('bin', 'sg'):
		#Use original system here. Mark II seems to have no expansion and it should just run Othello Multivision stuff?
		system = 'sg1000'
		slot = 'cart'
		slot_options['sgexp'] = 'fm' #Can also put sk1100 in here. Can't detect yet what uses which though
	else:
		return None #This shouldn't happen


	return mame_command_line(system, slot, slot_options, has_keyboard)

def mame_sharp_x68000(game, _):
	if game.subroms:
		#FIXME: This won't work if the referenced m3u files have weird compression formats supported by 7z but not by MAME; but maybe that's your own fault
		floppy_slots = {}
		for i, individual_floppy in enumerate(game.subroms):
			floppy_slots['flop%d' % (i + 1)] = shlex.quote(individual_floppy.path)

		return mame_command_line('x68000', slot=None, slot_options=floppy_slots, has_keyboard=True)
	return mame_command_line('x68000', 'flop1', has_keyboard=True)

def mupen64plus(game, _):
	#TODO: Do I reaaaaaaally need that
	environment_variables = {'MESA_GL_VERSION_OVERRIDE': '3.3COMPAT'}

	if game.metadata.specific_info.get('ROM-Format', None) == 'Unknown':
		print('shoop da woop', game.rom.path)
		return None
	
	command_line = 'mupen64plus --nosaveoptions --fullscreen $<path>'
	if environment_variables:
		command_line = 'env {0} {1}'.format(' '.join(['{0}={1}'.format(k, v) for k, v in environment_variables.items()]), command_line)
	return command_line
