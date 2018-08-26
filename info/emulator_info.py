import sys
import shlex
import os
import configparser

import config
from .region_info import TVSystem

debug = '--debug' in sys.argv

class Emulator():
	def __init__(self, command_line, supported_extensions, supported_compression, wrap_in_shell=False):
		self.command_line = command_line
		self.supported_extensions = supported_extensions
		self.supported_compression = supported_compression
		self.wrap_in_shell = wrap_in_shell

	def get_command_line(self, game, other_config):
		#You might think sinc I have game.rom here, I should just insert the path into the command line here too. I don't though, in case the final path that gets passed to the emulator needs to be different than the ROM's path (in case of temporary extracted files for emulators not supporting compression, for example)
		if callable(self.command_line):
			return self.command_line(game, other_config)
		
		return self.command_line

def make_mednafen_command_line(module):
	return 'mednafen -video.fs 1 -force_module %s $<path>' % module

class MednafenModule(Emulator):
	def __init__(self, module, supported_extensions, command_line=None):
		if not command_line:
			command_line = make_mednafen_command_line(module)
		Emulator.__init__(self, command_line, supported_extensions, ['zip', 'gz'])

def get_autoboot_script_by_name(name):
	this_package = os.path.dirname(__file__)
	root_package = os.path.dirname(this_package)
	return os.path.join(root_package, 'mame_autoboot', name + '.lua')

def make_mame_command_line(driver, slot=None, slot_options=None, has_keyboard=False, autoboot_script=None):
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
		command_line += ' -autoboot_script ' + shlex.quote(get_autoboot_script_by_name(autoboot_script))

	return command_line

class MameSystem(Emulator):
	def __init__(self, command_line, supported_extensions):
		Emulator.__init__(self, command_line, supported_extensions, ['7z', 'zip'])

mame_cdrom_formats = ['iso', 'chd', 'cue', 'toc', 'nrg', 'cdr', 'gdi']
#Some drivers have custom floppy formats, but these seem to be available for all
mame_floppy_formats = ['d77', 'd88', '1dd', 'dfi', 'hfe', 'imd', 'ipf', 'mfi', 'mfm', 'td0', 'cqm', 'cqi', 'dsk']
		
def build_atari7800_command_line(game, _):
	if not game.metadata.specific_info.get('Headered', False):
		if debug:
			print(game.rom.path, 'has no header and is therefore unsupported')
		return None

	if game.metadata.tv_type == TVSystem.PAL:
		system = 'a7800p'
	else:
		system = 'a7800'

	return make_mame_command_line(system, 'cart')

def build_vic20_command_line(game, _):
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

	return make_mame_command_line(system, 'cart', {'iec8': '""'}, has_keyboard=True)
		
def build_a800_command_line(game, _):
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

	return make_mame_command_line(system, slot, has_keyboard=True)

def find_c64_system(game):
	if game.metadata.platform == 'C64GS':	
		#For some reason, C64GS carts don't work on a regular C64 in MAME, and we have to use...  the thing specifically designed for playing games (but we normally wouldn't use this, since some cartridge games still need the keyboard, even if just for the menus, and that's why it actually sucks titty balls IRL.  But if it weren't for that, we totes heckin would)
		#Note that C64GS doesn't really work properly in MAME anyway, but the carts... not work... less than in the regular C64 driver
		return 'c64gs'
	
	#Don't think we really need c64c unless we really want the different SID chip
	
	if game.metadata.tv_type == TVSystem.PAL:
		return 'c64p'
	
	return 'c64'
	
def build_c64_command_line(game, _):
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

	system = find_c64_system(game)
	return make_mame_command_line(system, 'cart', {'joy1': 'joybstr', 'joy2': 'joybstr', 'iec8': '""'}, True)

def make_mgba_command_line(game, _):
	command_line = 'mgba-qt -f'
	if not game.metadata.specific_info.get('Nintendo-Logo-Valid', True):
		command_line += ' -C useBios=0'
	return command_line + ' $<path>'

def make_gambatte_command_line(game, _):
	mapper = game.metadata.specific_info.get('Mapper', None)
	if not mapper:
		#If there was a problem detecting the mapper, or it's something invalid, it probably won't run
		if debug:
			print('Skipping', game.rom.path, '(by Gambatte) because mapper is unrecognized')
		return None
	if mapper.name in ['Bandai TAMA5', 'HuC3', 'MBC6', 'MBC7', 'Pocket Camera']:
		return None		

	return 'gambatte_qt --full-screen $<path>'

def make_mame_snes_command_line(game, other_config):
	#Snes9x's GTK+ port doesn't let us load carts with slots for other carts from the command line yet, so this will have
	#to do, but unfortunately it's a tad slower
	if game.rom.extension == 'st':
		if 'sufami_turbo_bios_path' not in other_config:
			if debug:
				#TODO Only print this once!
				print("You can't do", game.rom.path, "because you haven't set up the BIOS for it yet, check emulators.ini")
			return None

		#We don't need to detect TV type because the Sufami Turbo (and also BS-X) was only released in Japan and so the Super Famicom can be used for everything
		return make_mame_command_line('snes', 'cart2', {'cart': shlex.quote(other_config['sufami_turbo_bios_path'])}, False)
	
	if game.rom.extension == 'bs':
		if 'bsx_bios_path' not in other_config:
			if debug:
				#TODO Only print this once!
				print("You can't do", game.rom.path, "because you haven't set up the BIOS for it yet, check emulators.ini")
			return None

		return make_mame_command_line('snes', 'cart2', {'cart': shlex.quote(other_config['bsx_bios_path'])}, False)
	
	if game.metadata.tv_type == TVSystem.PAL:
		system = 'snespal'
	else:
		#American SNES and Super Famicom are considered to be the same system, so that works out nicely
		system = 'snes'

	return make_mame_command_line(system, 'cart')

def make_mame_nes_command_line(game, _):
	if game.rom.extension == 'fds':
		#We don't need to detect TV type because the FDS was only released in Japan and so the Famicom can be used for everything
		return make_mame_command_line('fds', 'flop')
	
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

	return make_mame_command_line(system, 'cart', has_keyboard=uses_sb486)

def make_mame_atari_2600_command_line(game, _):
	if game.rom.get_size() > (512 * 1024):
		if debug:
			print(game.rom.path, "can't be run by MAME a2600 as it's too big")
		return None
	#TODO: Switch based on input type
	if game.metadata.tv_type == TVSystem.PAL:
		system = 'a2600p'
	else:
		system = 'a2600'

	return make_mame_command_line(system, 'cart')

def make_mame_speccy_command_line(game, _):
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

	return make_mame_command_line(system, slot, options, True)

def get_dolphin_command_line(game, _):
	if game.metadata.specific_info.get('No-Disc-Magic', False):
		if debug:
			print(game.rom.path, 'has no disc magic')
		return None

	return 'dolphin-emu -b -e $<path>'

def get_citra_command_line(game, _):
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

def get_kega_fusion_command_line(game, _):
	if game.rom.extension == 'md' and game.metadata.platform != 'Mega Drive':
		#Probably just a readme file or similar
		return None
	if game.rom.extension == 'bin' and game.metadata.platform == 'Mega CD':
		#Prefer the .cue of .bin/.cue images
		return None
	return 'kega-fusion -fullscreen $<path>'

def get_mednafen_nes_command_line(game, _):
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

def get_reicast_command_line(game, _):
	if game.metadata.specific_info.get('Uses-Windows-CE', False):
		if debug:
			print(game.rom.path, 'is not supported because it uses Windows CE')
		return None
	return 'reicast -config x11:fullscreen=1 $<path>'

def make_mame_sg1000_command_line(game, _):
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


	return make_mame_command_line(system, slot, slot_options, has_keyboard)
	
emulators = {
	'Citra': Emulator(get_citra_command_line, ['3ds', 'cxi', '3dsx'], []),
	#Will not run full screen from the command line and you always have to set it manually whether you like it or not (I
	#do not, but eh, it works and that's really cool)
	'Dolphin': Emulator(get_dolphin_command_line, ['iso', 'gcz', 'elf', 'dol', 'wad'], []),
	'Gambatte': Emulator(make_gambatte_command_line, ['gb', 'gbc'], ['zip']),
	#--gba-cgb-mode[=0] and --force-dmg-mode[=0] may be useful in obscure situations
	'Kega Fusion': Emulator(get_kega_fusion_command_line, ['bin', 'gen', 'md', 'smd', 'sgd', 'gg', 'sms', 'iso', 'cue', 'sg', 'sc', '32x'], ['zip']),
	#May support other CD formats for Mega CD other than iso, cue?
	'Medusa': Emulator('medusa-emu-qt -f $<path>', ['nds'], ['7z', 'zip']),
	'mGBA': Emulator(make_mgba_command_line, ['gb', 'gbc', 'gba', 'srl', 'bin', 'mb'], ['7z', 'zip']),
	#Use -C useBios=0 for homebrew with bad checksum/logo that won't boot on real hardware.  Some intensive games (e.g.
	#Doom) will not run at full speed on toaster, but generally it's fine
	'Mupen64Plus': Emulator('env MESA_GL_VERSION_OVERRIDE=3.3COMPAT mupen64plus --nosaveoptions --fullscreen $<path>', ['z64', 'v64', 'n64'], []),
	#Often pretty slow on toaster but okay for turn-based games; environment variable is needed for GLideN64 which sometimes is
	#preferred over Rice and sometimes not (the latter wins at speed and not much else).  Do I still need that environment
	#variable?  I think I might
	'PCSX2': Emulator('pcsx2 --nogui --fullscreen --fullboot $<path>', ['iso', 'cso', 'bin'], ['gz']),
	#Has a few problems.  Takes some time to load the interface so at first it might look like it's not working; take out --fullboot if it forbids any homebrew stuff (but it should be fine, and Katamari Damacy needs it).  ELF still doesn't work, though it'd need a different command line anyway
	'PokeMini': Emulator('PokeMini -fullscreen $<path>', ['min'], ['zip']),
	#Puts all the config files in the current directory, which is why there's a wrapper below which you probably want to use instead of this
	'PokeMini (wrapper)': Emulator('mkdir -p ~/.config/PokeMini && cd ~/.config/PokeMini && PokeMini -fullscreen $<path>', ['min'], ['zip'], True),
	'PPSSPP': Emulator('ppsspp-qt $<path>', ['iso', 'pbp', 'cso'], []),
	'Reicast': Emulator(get_reicast_command_line, ['gdi', 'cdi', 'chd'], []),
	'Snes9x': Emulator('snes9x-gtk $<path>', ['sfc', 'smc', 'swc'], ['zip', 'gz']),
	#Slows down on toaster for a lot of intensive games e.g.  SuperFX.  Can't set fullscreen mode from the command line so you have
	#to set up that yourself; GTK port can't do Sufami Turbo due to lacking multi-cart support that Windows has, MAME can
	#emulate this but it's too slow on toasters so we do that later; GTK port can do Satellaview but not directly from the
	#command line
	'Stella': Emulator('stella -fullscreen 1 $<path>', ['a26', 'bin', 'rom'], ['gz', 'zip']),

	'Mednafen (Game Boy)': MednafenModule('gb', ['gb', 'gbc']),
	#Would not recommend due to this being based on VisualBoyAdvance, it's just here for completeness
	'Mednafen (Game Gear)': MednafenModule('gg', ['gg']),
	#Apparently "a low-priority system in terms of proactive maintenance and bugfixes"
	'Mednafen (GBA)': MednafenModule('gba', ['gba']),
	#Would not recommend due to this being based on VisualBoyAdvance, it's just here for completeness
	'Mednafen (Lynx)': MednafenModule('lynx', ['lnx', 'lyx', 'o']),
	#Sorta has like...  2 sets of A and B buttons, and 3 buttons on one side and 2 on the other?  It's supposed to be
	#ambidextrous or something which is cool in real life but not so great here, I might need to look more into it and
	#then maybe move it into the normal-but-less-cool platforms
	'Mednafen (Master System)': MednafenModule('gg', ['gg']),
	#Apparently "a low-priority system in terms of proactive maintenance and bugfixes"
	'Mednafen (Mega Drive)': MednafenModule('md', ['md', 'bin', 'gen', 'smd', 'sgd']),
	#Apparently "should still be considered experimental; there are still likely timing bugs in the 68K emulation code, the YM2612 emulation code is not particularly accurate, and the VDP code has timing-related issues."
	'Mednafen (Neo Geo Pocket)': MednafenModule('ngp', ['ngp', 'npc', 'ngc']),
	'Mednafen (NES)': MednafenModule('nes', ['nes', 'fds', 'unf'], get_mednafen_nes_command_line),
	'Mednafen (PC Engine)': MednafenModule('pce', ['pce', 'sgx', 'iso', 'cue', 'ccd', 'toc', 'm3u']),
	#Mednafen assumes that there is only 1 gamepad and it's the 6 button kind, so button mapping is kind of weird when I
	#was perfectly fine just using 2 buttons
	'Mednafen (PC Engine Fast)': MednafenModule('pce_fast', ['pce', 'sgx', 'iso', 'cue', 'ccd', 'toc', 'm3u']),
	'Mednafen (PC-FX)': MednafenModule('pcfx', ['iso', 'cue', 'toc', 'ccd', 'm3u']), #Do NOT specify a FX-SCSI BIOS
	'Mednafen (PS1)': MednafenModule('psx', ['iso', 'cue', 'exe', 'toc', 'ccd', 'm3u']),
	#Seems like some PAL games don't run at the resolution Mednafen thinks they should, so they need per-game configs
	#that override the scanline start/end settings
	'Mednafen (Saturn)': MednafenModule('ss', ['cue', 'toc', 'ccd', 'm3u']),
	#Doesn't do .iso for whatever strange reason, which is a bit unfortunate. Might do .bin executables? Probably not
	'Mednafen (SNES)': MednafenModule('snes', ['sfc', 'smc', 'swc']),
	#Based on bsnes v0.059, probably not so great on toasters. Not sure how well it works necessarily, probably doesn't do Sufami Turbo or Satellaview
	'Mednafen (SNES-Faust)': MednafenModule('snes_faust', ['sfc', 'smc', 'swc']),
	#Experimental and doesn't support expansion chips
	'Mednafen (Virtual Boy)': MednafenModule('vb', ['bin', 'vb']),
	'Mednafen (WonderSwan)': MednafenModule('wswan', ['ws', 'wsc', 'bin', 'pc2']),
	#Oof this is just super mega weird because you can turn the thing sideways and it still does a thing.  I'll need some
	#point of reference to figure out how to set this up for a normal-ish gamepad...

	'MAME (Amstrad CPC+)': MameSystem(make_mame_command_line('cpc6128p', 'cart'), ['bin', 'cpr']),
	#Just in case I change my mind on using GX4000. cpc464p is a different CPC+ model but I'm not sure that would be useful?
	'MAME (Amstrad GX4000)': MameSystem(make_mame_command_line('gx4000', 'cart'), ['bin', 'cpr']),
	#"But why not just use Amstrad CPC+?" you ask, well, there's no games that are on CPC+ cartridges that aren't on
	#GX4000, and I don't feel like fondling around with disks and tapes if I can avoid it
	'MAME (APF-MP1000)': MameSystem(make_mame_command_line('apfm1000', 'cart'), ['bin']),
	'MAME (Arcadia 2001)': MameSystem(make_mame_command_line('arcadia', 'cart'), ['bin']),
	#Can also use bndarc for Bandai version but that doesn't seem to make any difference at all?  Some games seem to be
	#weird with the input so that sucks
	#TOOD: What kind of weird? Perhaps I don't actually know what I'm doing
	'MAME (Astrocade)': MameSystem(make_mame_command_line('astrocde', 'cart', {'exp': 'rl64_ram'}), ['bin']),
	#There's a keypad there which is used for game selection/setup, otherwise it just uses a paddle with a button (the
	#actual controllers IRL were wacky, but for emulation purposes are otherwise pretty normal).  Hopefully adding that
	#RAM expansion won't hurt?  Some games (Chicken) seem to be broken anyway with expansion or without whoops
	'MAME (Atari 2600)': MameSystem(make_mame_atari_2600_command_line, ['bin', 'a26']),
	'MAME (Atari 5200)': MameSystem(make_mame_command_line('a5200', 'cart'), ['bin', 'rom', 'car', 'a52']),
	#Analog stuff like Gorf doesn't really work that well, but it doesn't in real life either; could use -sio casette
	#-cass *.wav if there was ever a game that came as a .wav which apparently could be a thing in theory
	'MAME (Atari 7800)': MameSystem(build_atari7800_command_line, ['bin', 'a78']),
	'MAME (Atari 8-bit)': MameSystem(build_a800_command_line, ['bin', 'rom', 'car']),
	#Might get a bit of slowdown on toaster if you open the MAME menu, but usually you'd want to do that when paused
	#anyway, and the games themselves run fine	
	'MAME (C64)': MameSystem(build_c64_command_line, ['80', 'a0', 'e0', 'crt']),
	#Same kerfluffle with regions and different media formats here.  Could use c64c/c64cp for the newer model with the
	#new SID chip, but that might break compatibility I dunno; could also use sx64 for some portable version, there's a
	#whole bunch of models; c64gs doesn't really have much advantages (just like in real life) except for those few
	#cartridges that were made for it specifically.
	'MAME (CD-i)': MameSystem(make_mame_command_line('cdimono1', 'cdrom'), mame_cdrom_formats),
	#This is the only CD-i model that works, and it says it's not working, but it seems fine
	'MAME (Channel F)': MameSystem(make_mame_command_line('channelf', 'cart'), ['bin', 'chf']),
	#How the fuck do these controls work?  Am I just too much of a millenial?
	'MAME (ColecoVision)': MameSystem(make_mame_command_line('coleco', 'cart'), ['bin', 'col', 'rom']),
	#Controls are actually fine in-game, just requires a keypad to select levels/start games and that's not consistent at
	#all so good luck with that (but mapping 1 to Start seems to work well).  All carts are either USA or combination USA/Europe and are required by Coleco to run on both regions, so why play in 50Hz when we don't have to
	'MAME (Coleco Adam)': MameSystem(make_mame_command_line('adam', 'cass1', {'net4': '""', 'net5': '""'}, has_keyboard=True), ['wav', 'ddp']),
	#Uses tapes, but they just boot automatically, so it's fine I guess.
	#TODO: Do disks as well, if I had any. Also Adam-specific carts I guess? Not sure how those work, or if the cartridge port is just there for Colecovision compatibility and I'm a doofus
	'MAME (Entex Adventure Vision)': MameSystem(make_mame_command_line('advision', 'cart'), ['bin']),
	#Doesn't work with the "Code Red" demo last time I tried
	'MAME (Gamate)': MameSystem(make_mame_command_line('gamate', 'cart'), ['bin']),
	'MAME (Game.com)': MameSystem(make_mame_command_line('gamecom', 'cart1'), ['bin', 'tgc']),
	#I don't know what the other cart slot does, or if you can use two at once, or how that would work if you could. Hopefully I don't need it for anything
	'MAME (Game Boy)': MameSystem(make_mame_command_line('gbpocket', 'cart'), ['bin', 'gb', 'gbc']),
	'MAME (Game Boy Color)': MameSystem(make_mame_command_line('gbcolor', 'cart'), ['bin', 'gb', 'gbc']),
	'MAME (Game Gear)': MameSystem(make_mame_command_line('gamegear', 'cart'), ['bin', 'gg']),
	'MAME (Game Pocket Computer)': MameSystem(make_mame_command_line('gamepock', 'cart'), ['bin']),
	'MAME (GBA)': MameSystem(make_mame_command_line('gba', 'cart'), ['bin', 'gba']),
	'MAME (Intellivision)': MameSystem(make_mame_command_line('intv', 'cart'), ['bin', 'int', 'rom', 'itv']),
	#Well this sure is a shit console.  There's no consistency to how any game uses any buttons or keypad keys (is it the
	#dial?  Is it keys 2 4 6 8?, so good luck with that; also 2 player mode isn't practical because some games use the
	#left controller and some use the right, so you have to set both controllers to the same inputs; and Pole Position has
	#glitchy graphics.  Why did Mattel make consoles fuck you Mattel I hope you burn
	'MAME (Intellivoice)': MameSystem(make_mame_command_line('intvoice', 'cart'), ['bin', 'int', 'rom', 'itv']),
	#Anyway, might as well use the voice module here since it shouldn't break any existing games 
	#TODO: Merge these four Intellivision consoles into one, and automatically detect if voice, ECS, or keyboard needs to be used. The tricky part will be to detect that.
	'MAME (Intellivision ECS)': MameSystem(make_mame_command_line('intvecs', 'cart'), ['bin', 'int', 'rom', 'itv']),
	#The ECS module does, in fact, break some existing games (I've heard so anyway, don't know which ones), but it is here for usage anyway
	'MAME (Intellivision Keyboard)': MameSystem(make_mame_command_line('intvkbd', 'cart'), ['bin', 'int', 'rom', 'itv']),
	#This was unreleased, but there are dumps of the keyboard-using games out there
	'MAME (Mega Duck)': MameSystem(make_mame_command_line('megaduck', 'cart'), ['bin']),
	'MAME (MSX1)': MameSystem(make_mame_command_line('svi738', 'cart1', {'fdc:0': '""'}, has_keyboard=True), ['bin', 'rom']),
	#Note that MSX2 is backwards compatible anyway, so there's not much reason to use this, unless you do have some reason. This model in particular is used because it should be completely in English and if anything goes wrong I'd be able to understand it. I still don't know how disks work (they don't autoboot), or if there's even a consistent command to use to boot them.
	'MAME (MSX2)': MameSystem(make_mame_command_line('fsa1wsx', 'cart1', {'fdc:0': '""'}, has_keyboard=True), ['bin', 'rom']),
	#This includes MSX2+ because do you really want me to make those two separate things? Turbo-R doesn't work in MAME though, so that'd have to be its own thing. This model is used just because I looked it up and it seems like the best one, the MSX2/MSX2+ systems in MAME are all in Japanese (the systems were only really released in Japan, after all) so you can't avoid that part. Still don't understand disks.
	'MAME (Neo Geo CD)': MameSystem(make_mame_command_line('neocdz', 'cdrom'), mame_cdrom_formats),
	#This is interesting, because this runs alright on toasters, but Neo Geo-based arcade games do not (both being
	#emulated in MAME); meaning I am probably doing something wrong.  Don't think it has region lock so I should never
	#need to use neocdzj? (neocd doesn't work, apparently because it thinks it has the drive tray open constantly)
	'MAME (Neo Geo Pocket)': MameSystem(make_mame_command_line('ngpc', 'cart'), ['bin', 'ngp', 'npc', 'ngc']),
	'MAME (NES)': MameSystem(make_mame_nes_command_line, ['nes', 'unf', 'unif', 'fds']),
	'MAME (Pokemon Mini)': MameSystem(make_mame_command_line('pokemini', 'cart'), ['bin', 'min']),
	#Wouldn't recommend yet as it has no sound, even if most people would probably turn the sound off in real life
	'MAME (PC-88)': MameSystem(make_mame_command_line('pc8801', 'flop1', has_keyboard=True), mame_floppy_formats),
	#TODO: Tapes, and potentially look into other models. All the PC-88 models claim to be broken, but the base one plays the games, so that's good enough in my book. Some might use BASIC though so I'd have to specially handle that?
	'MAME (PV-1000)': MameSystem(make_mame_command_line('pv1000', 'cart'), ['bin']),
	'MAME (PV-2000)': MameSystem(make_mame_command_line('pv2000', 'cart', has_keyboard=True), ['bin']),
	#Not the same as the PV-1000!  Although it might as well be, except it's a computer, and they aren't compatible with each other.  MAME says it
	#doesn't work but it seems alright, other than it's supposed to have joysticks and doesn't (so you just set up a
	#gamepad to map to emulated cursor keys) which maybe is why they say it's preliminary
	'MAME (SG-1000)': MameSystem(make_mame_sg1000_command_line, ['bin', 'sg', 'sc', 'sf7'] + mame_floppy_formats),
	'MAME (Sharp X1)': MameSystem(make_mame_command_line('x1turbo40', 'flop1', has_keyboard=True), mame_floppy_formats + ['2d']),
	#Hey!!  We finally have floppies working!!  Because they boot automatically!  Assumes that they will all work fine
	#though without any other disks, and this will need to be updated if we see any cartridges (MAME says it has a cart
	#slot)...
	'MAME (Sharp X68000)': MameSystem(make_mame_command_line('x68000', 'flop1', has_keyboard=True), mame_floppy_formats + ['xdf', 'hdm', '2hd', 'dim']),	
	'MAME (SNES)': MameSystem(make_mame_snes_command_line, ['sfc', 'bs', 'st']),
	'MAME (Sord M5)': MameSystem(make_mame_command_line('m5', 'cart1', {'ramsize': '64K', 'upd765:0': '""'}, True), ['bin']),
	#Apparently has joysticks with no fire button?  Usually space seems to be fire but sometimes 1 is, which is usually
	#for starting games.  I hate everything.
	'MAME (Super Game Boy)': MameSystem(make_mame_command_line('supergb2', 'cart'), ['bin', 'gb', 'gbc']),
	'MAME (Tomy Tutor)': MameSystem(make_mame_command_line('tutor', 'cart', has_keyboard=True, autoboot_script='tomy_tutor'), ['bin']),
	#Well, at least there's no region crap, though there is pyuuta if you want to read Japanese instead
	'MAME (Uzebox)': MameSystem(make_mame_command_line('uzebox', 'cart'), ['bin', 'uze']),
	#Runs really slowly, but it works, also heck it
	'MAME (VC 4000)': MameSystem(make_mame_command_line('vc4000', 'cart'), ['bin', 'rom']),
	#There's like 30 different clones of this, and most of them aren't even clones in the MAME sense, they're literally hardware clones. But they're apparently all software-compatible, although the cartridges aren't hardware-compatible, they just contain the same software... so this all gets confusing. Anyway, the software list with all these is named "vc4000" so I guess that's the "main" one, so we'll use that. I'm not sure if there are any PAL/NTSC differences to worry about.
	#TODO: Quickload slot (.pgm, .tvc)
	'MAME (Vectrex)': MameSystem(make_mame_command_line('vectrex', 'cart'), ['bin', 'gam', 'vec']),
	#I wonder if there's a way to set the overlay programmatically...  doesn't look like there's a command line option to
	#do that.  Also the buttons are kinda wack I must admit, as they're actually a horizontal row of 4
	'MAME (VIC-10)': MameSystem(make_mame_command_line('vic10', 'cart', {'joy1': 'joy', 'joy2': 'joy'}, has_keyboard=True), ['crt', '80', 'e0']),
	#More similar to the C64 than the VIC-20, need to plug a joystick into both ports because once again games can use
	#either port and thanks I hate it.  At least there's only one TV type
	'MAME (VIC-20)': MameSystem(build_vic20_command_line, ['20', '40', '60', '70', 'a0', 'b0', 'crt']),
	#Need to figure out which region to use and we can only really do that by filename, also it doesn't like 16KB carts;
	#disks and tapes are a pain in the ass IRL so MAME emulates the ass-pain of course; and I dunno about .prg files,
	#those are just weird (but it'd be great if I could get those working though); with this and C64 there are some games
	#where you'll have to manually change to the paddle which kinda sucks but I guess it can't be helped and also turn on
	#"Paddle Reverse" in "Analog Controls" for some reason
	'MAME (Virtual Boy)': MameSystem(make_mame_command_line('vboy', 'cart'), ['bin', 'vb']),
	#Doesn't do red/blue stereo 3D, instead just outputing two screens side by side (you can go cross-eyed to see the 3D effect, but that'll hurt your eyes after a while (just like in real life)). Also has a bit of graphical glitches here and there; no ROMs required though so that's neat
	'MAME (VZ-200)': MameSystem(make_mame_command_line('vz200', 'dump', {'io': 'joystick', 'mem': 'laser_64k'}, True),  ['vz']),
	#In the Laser 200/Laser 210 family, but Dick Smith variant should do.
	#TODO see if casettes (wav cas) or disks (mame_floppy_formats, mem slot = floppy) work nicely
	#Joystick interface doesn't seem to be used by any games, but I guess it does more than leaving the IO slot unfilled. That sucks, because otherwise no game ever uses the keyboard consistently, because of course not. Even modern homebrew games. Why y'all gotta be like that?
	#Some games will need you to type RUN to run them, not sure how to detect that.
	'MAME (Watara Supervision)': MameSystem(make_mame_command_line('svision', 'cart'), ['bin', 'ws', 'sv']),
	#I've been told the sound is that horrible on a real system; there are "TV Link" variant systems but that just makes
	#the colours look even worse (they're all inverted and shit)
	'MAME (WonderSwan)': MameSystem(make_mame_command_line('wscolor', 'cart'), ['ws', 'wsc', 'bin', 'pc2']),
	'MAME (ZX Spectrum)': MameSystem(make_mame_speccy_command_line, ['ach', 'frz', 'plusd', 'prg', 'sem', 'sit', 'sna', 'snp', 'snx', 'sp', 'z80', 'zx'] + mame_floppy_formats),

	#Other systems that MAME can do but I'm too lazy to do them yet because they'd need a command line generator function or other:
	#Dreamcast: Region, and also runs slow on my computer so I don't feel like it
	#Lynx: Need to select -quick for .o files and -cart otherwise
	#SMS, Megadrive: Need to detect region (beyond TV type)
	#	(Notable that Megadrive can do Sonic & Knuckles)
	#N64: Does not do PAL at all. The game might even tell you off if it's a PAL release
	#PC Engine: Need to select between pce and tg16 depending on region, -cdrom and -cart slots, and sgx accordingly
}

def make_prboom_plus_command_line(_, other_config):
	if 'save_dir' in other_config:
		return 'prboom-plus -save %s -iwad $<path>' % shlex.quote(other_config['save_dir'])

	#Fine don't save then, nerd
	return 'prboom-plus -iwad $<path>'

class GameEngine():
	#Not really emulators, but files come in and games come out. 
	def __init__(self, command_line, is_game_data):
		self.command_line = command_line
		self.is_game_data = is_game_data #This is supposed to be a lambda but I can't figure out how to word it so that's apparent at first glance

	def get_command_line(self, game, other_config):
		if callable(self.command_line):
			return self.command_line(game, other_config)
		
		return self.command_line

engines = {
	'PrBoom+': GameEngine(make_prboom_plus_command_line, lambda file: file.extension == 'wad'),
	#Joystick support not so great, otherwise it plays perfectly well with keyboard + mouse; except the other issue where it doesn't really like running in fullscreen when more than one monitor is around (to be precise, it stops that second monitor updating). Can I maybe utilize some kind of wrapper?  I guess it's okay because it's not like I don't have a mouse and keyboard though the multi-monitor thing really is not okay
	'Darkplaces': GameEngine('darkplaces-glx -nostdout -fullscreen -basedir $<path>', lambda folder: folder.contains_subfolder('id1'))
	#TODO: Make this work with expansion packs and stuff (this will most definitely only work with base Quake), I haven't bought them yet
}

def make_basilisk_ii_command_line(app, other_config):
	if 'arch' in app.config:
		if app.config['arch'] == 'ppc':
			return None

	#This requires a script inside the Mac OS environment's startup items folder that reads "Unix:autoboot.txt" and launches whatever path is referred to by the contents of that file. That's ugly, but there's not really any other way to do it. Like, at all. Other than having separate bootable disk images. You don't want that. Okay, so I don't want that.
	#Ideally, HFS manipulation would be powerful enough that we could just slip an alias into the Startup Items folder ourselves and delete it afterward. That doesn't fix the problem of automatically shutting down (still need a script for that), unless we don't create an alias at all and we create a script or something on the fly that launches that path and then shuts down, but yeah. Stuff and things.
	autoboot_txt_path = os.path.join(other_config['shared_folder'], 'autoboot.txt')
	width = other_config.get('default_width', 1920)
	height = other_config.get('default_height', 1080)
	if 'max_resolution' in app.config:
		width, height = app.config['max_resolution']
	#Can't do anything about colour depth at the moment (displaycolordepth is functional on some SDL1 builds, but not SDL2)
	#Or controls... but I swear I will find a way!!!!
	
	#If you're not using an SDL2 build of BasiliskII, you probably want to change dga to window! Well you really want to get an SDL2 build of BasiliskII, honestly
	actual_emulator_command = 'BasiliskII --screen dga/{0}/{1}'.format(width, height)
	inner_command = 'echo {0} > {1} && {2} && rm {1}'.format(shlex.quote(app.path), shlex.quote(autoboot_txt_path), actual_emulator_command)
	return 'sh -c {0}'.format(shlex.quote(inner_command))

class MacEmulator():
	def __init__(self, command_line):
		self.command_line = command_line

	def get_command_line(self, app, other_config):
		if callable(self.command_line):
			return self.command_line(app, other_config)
		
		return self.command_line

mac_emulators = {
	'BasiliskII': MacEmulator(make_basilisk_ii_command_line),
	#TODO: Add SheepShaver here, even if we would have to do the vm.mmap thingy
}

class DOSEmulator():
	def __init__(self, command_line):
		self.command_line = command_line

	def get_command_line(self, app, other_config):
		if callable(self.command_line):
			return self.command_line(app, other_config)
		
		return self.command_line

def get_dos_config(app):
	if not os.path.isdir(config.dos_configs_path):
		return None	

	for conf in os.listdir(config.dos_configs_path):
		path = os.path.join(config.dos_configs_path, conf)
		name, _ = os.path.splitext(conf)
		if app.name in (name, name.replace(' - ', ': ')):
			return path

	return None

def make_dos_config(app, other_config):
	configwriter = configparser.ConfigParser()
	configwriter.optionxform = str

	configwriter['sdl'] = {}
	configwriter['sdl']['fullscreen'] = 'true'
	configwriter['sdl']['fullresolution'] = 'desktop'
	#TODO: Set mapper file, which will of course require another separate directory
	#TODO: Might have to set autoexec instead of just pointing to the file as a command line argument for some versions of DOSBox

	if 'required_hardware' in app.config:
		if 'for_xt' in app.config['required_hardware']:
			if app.config['required_hardware']['for_xt']:
				configwriter['cpu'] = {}
				configwriter['cpu']['cycles'] = other_config.get('slow_cpu_cycles', 400)

		if 'max_graphics' in app.config['required_hardware']:
			configwriter['dosbox'] = {}
			graphics = app.config['required_hardware']['max_graphics']
			configwriter['dosbox']['machine'] = 'svga_s3' if graphics == 'svga' else graphics

	#TODO: Perform other sanity checks on name
	name = app.name.replace(': ', ' - ') + '.ini'
	path = os.path.join(config.dos_configs_path, name)

	os.makedirs(config.dos_configs_path, exist_ok=True)
	with open(path, 'wt') as config_file:
		configwriter.write(config_file)

	return path

def get_dosbox_command_line(app, other_config):
	conf = get_dos_config(app)
	if ('--regen-dos-config' in sys.argv) or not conf:
		conf = make_dos_config(app, other_config)
	actual_command = "dosbox -exit -noautoexec -userconf -conf {1} {0}".format(shlex.quote(app.path), shlex.quote(conf))
	return actual_command

dos_emulators = {
	'DOSBox/SDL2': DOSEmulator(get_dosbox_command_line)
}
