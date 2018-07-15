import sys
import shlex

import common
from region_info import TVSystem

debug = '--debug' in sys.argv

class Emulator():
	def __init__(self, command_line, supported_extensions, supported_compression):
		self.command_line = command_line
		self.supported_extensions = supported_extensions
		self.supported_compression = supported_compression

	def get_command_line(self, game, other_config):
		#You might think sinc I have game.rom here, I should just insert the path into the command line here too. I don't though, in case the final path that gets passed to the emulator needs to be different than the ROM's path (in case of temporary extracted files for emulators not supporting compression, for example)
		if callable(self.command_line):
			return self.command_line(game, other_config)
		
		return self.command_line

class MednafenModule(Emulator):
	def __init__(self, module, supported_extensions):
		Emulator.__init__(self, 'mednafen -video.fs 1 -force_module %s $<path>' % module, supported_extensions, ['zip', 'gz'])

def make_mame_command_line(driver, slot=None, slot_options=None, has_keyboard=False):
	command_line = 'mame -skip_gameinfo'
	if has_keyboard:
		command_line += ' -ui_active'

	command_line += ' ' + driver

	if slot_options:
		for name, value in slot_options.items():
			command_line += ' -' + name + ' ' + value

	if slot:
		command_line += ' -' + slot + ' $<path>'

	return command_line

class MameSystem(Emulator):
	def __init__(self, command_line, supported_extensions):
		Emulator.__init__(self, command_line, supported_extensions, ['7z', 'zip'])

MAME_CDROM_FORMATS = ['iso', 'chd', 'cue', 'toc', 'nrg', 'cdr', 'gdi']
#Some drivers have custom floppy formats, but these seem to be available for all
MAME_FLOPPY_FORMATS = ['d77', 'd88', '1dd', 'dfi', 'hfe', 'imd', 'ipf', 'mfi', 'mfm', 'td0', 'cqm', 'cqi', 'dsk']
		
def build_atari7800_command_line(game, _):
	#TODO: Move the region byte reading into roms.py under somewhere in get_metadata
	rom_data = game.rom.read()
	if rom_data[1:10] != b'ATARI7800':
		if debug:
			print(game.rom.path, 'has no header and is therefore unsupported')
		return None
	
	region_byte = rom_data[57]
		
	if region_byte == 1:
		system = 'a7800p'
	elif region_byte == 0:
		system = 'a7800'
	else:
		if debug:
			print('Something is wrong with', game.rom.path, ', has region byte of', region_byte)
		return None

	return make_mame_command_line(system, 'cart')

def build_vic20_command_line(game, _):
	size = game.rom.get_size()
	if size > ((8 * 1024) + 2):
		#It too damn big (only likes 8KB with 2 byte header at most)
		if debug:
			print('Bugger!', game.rom.path, 'is too big for MAME at the moment, it is', size)
		return None
	
	if game.tv_type == TVSystem.PAL:
		system = 'vic20p'
	else:
		system = 'vic20'

	return make_mame_command_line(system, 'cart', has_keyboard=True)
		
def build_a800_command_line(game, _):
	is_left = True
	rom_data = game.rom.read()
	if rom_data[:4] == b'CART':
		cart_type = int.from_bytes(rom_data[4:8], 'big')
		#See also: https://github.com/dmlloyd/atari800/blob/master/DOC/cart.txt,
		#https://github.com/mamedev/mame/blob/master/src/devices/bus/a800/a800_slot.cpp
		if cart_type in (13, 14, 23, 24, 25) or (cart_type >= 33 and cart_type <= 38):
			if debug:
				print(game.rom.path, 'is actually a XEGS ROM which is not supported by MAME yet, cart type is', cart_type)
			return None
			
		#You probably think this is a bad way to do this...  I guess it is, but hopefully I can take some out as they become
		#supported (even if I have to use some other emulator or something to do it)
		if cart_type in (5, 17, 22, 41, 42, 43, 45, 46, 47, 48, 49, 53, 57, 58, 59, 60, 61) or (cart_type >= 26 and cart_type <= 32) or (cart_type >= 54 and cart_type <= 56):
			if debug:
				print(game.rom.path, "won't work as cart type is", cart_type)
			return None

		if cart_type in (4, 6, 7, 16, 19, 20):
			if debug:
				print(game.rom.path, "is an Atari 5200 ROM ya goose!! It won't work as an Atari 800 ROM as the type is", cart_type)
			return None
			
		if cart_type == 21: #59 goes in the right slot as well, but that's not supported
			if debug:
				print(game.rom.path, 'goes in right slot')
			is_left = False
	else:
		size = game.rom.get_size()
		#Treat 8KB files as type 1, 16KB as type 2, everything else is unsupported for now
		if size > ((16 * 1024) + 16):
			if debug:
				print(game.rom.path, 'may actually be a XL/XE/XEGS cartridge, please check it as it has no header and a size of', size)
			return None
	
	slot = 'cart1' if is_left else 'cart2'

	if game.tv_type == TVSystem.PAL:
		#Atari 800 should be fine for everything, and I don't feel like the XL/XE series to see in which ways they don't work
		system = 'a800p'
	else:
		system = 'a800'

	return make_mame_command_line(system, slot, has_keyboard=True)

def find_c64_system(game):
	rom_data = game.rom.read()
	if rom_data[:16] == b'C64 CARTRIDGE   ':
		#Just gonna make sure we're actually dealing with the CCS64 header format thingy first (see:
		#http://unusedino.de/ec64/technical/formats/crt.html)
		#It's okay if it doesn't, though; just means we won't be able to know if it's C64GS
		#TODO: Can we detect other cart types that might be completely unsupported?
		cart_type = int.from_bytes(rom_data[22:24], 'big')
		
		if cart_type == 15: #Commodore C64GS System 3 cart
			#For some reason, these carts don't work on a regular C64 in MAME, and we have to use...  the thing specifically designed for playing games (but we normally wouldn't use this, since some cartridge games still need the keyboard, even if just for the menus, and that's why it actually sucks titty balls IRL.  But if it weren't for that, we totes heckin would)
			#Note that C64GS doesn't really work properly in MAME anyway, but the carts... not work... less than in the regular C64 driver
			return 'c64gs'
	
	#Don't think we really need c64c unless we really want the different SID chip
	
	if game.tv_type == TVSystem.PAL:
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
	
	system = find_c64_system(game)
	return make_mame_command_line(system, 'cart', {'joy1': 'joybstr', 'joy2': 'joybstr'}, True)
	

def make_snes_addon_cart_command_line(game, other_config):
	#Just because this confused my eyes for a bit: game being unused other than in the error message is correct. The command line stays the same regardless of the content or region or whatever of the game, which is all we're preparing at the moment
	if 'bios_path' not in other_config:
		if debug:
			#TODO Only print this once!
			print("You can't do", game.rom.path, "because you haven't set up the BIOS for it yet, check config.py")
		return None
	return make_mame_command_line('snes', 'cart2', {'cart': shlex.quote(other_config['bios_path'])}, False)

def make_prboom_plus_command_line(_, other_config):
	if 'save_dir' in other_config:
		return 'prboom-plus -save %s -iwad $<path>' % shlex.quote(other_config['save_dir'])

	#Fine don't save then, nerd
	return 'prboom-plus -iwad $<path>'

emulators = {
	'Gambatte': Emulator('gambatte_qt --full-screen $<path>', ['gb', 'gbc'], ['zip']),
	#--gba-cgb-mode[=0] and --force-dmg-mode[=0] may be useful in obscure situations
	'mGBA': Emulator('mgba-qt -f $<path>', ['gb', 'gbc', 'gba', 'srl', 'bin', 'mb'], ['7z', 'zip']),
	#Use -C useBios=0 for homebrew with bad checksum/logo that won't boot on real hardware.  Some intensive games (e.g.
	#Doom) will not run at full speed on toaster, but generally it's fine
	'Snes9x': Emulator('snes9x-gtk $<path>', ['sfc', 'smc', 'swc'], ['zip', 'gz']),
	#Slows down on toaster for a lot of intensive games e.g.  SuperFX.  Can't set fullscreen mode from the command line so you have
	#to set up that yourself; GTK port can't do Sufami Turbo due to lacking multi-cart support that Windows has, MAME can
	#emulate this but it's too slow on toasters so we do that later; GTK port can do Satellaview but not directly from the
	#command line
	'Mupen64Plus': Emulator('env MESA_GL_VERSION_OVERRIDE=3.3COMPAT mupen64plus --nosaveoptions --fullscreen $<path>', ['z64', 'v64', 'n64'], []),
	#Often pretty slow on toaster but okay for turn-based games; environment variable is needed for GLideN64 which sometimes is
	#preferred over Rice and sometimes not (the latter wins at speed and not much else).  Do I still need that environment
	#variable?  I think I might
	'Kega Fusion': Emulator('kega-fusion -fullscreen $<path>', ['bin', 'gen', 'md', 'smd', 'sgd', 'gg', 'sms', 'iso', 'cue', 'sg', '32x'], ['zip']),
	#May support other CD formats for Mega CD other than iso, cue?
	'PPSSPP': Emulator('ppsspp-qt $<path>', ['iso', 'pbp', 'cso'], []),
	'Mednafen (Neo Geo Pocket)': MednafenModule('ngp', ['ngp', 'npc', 'ngc']),
	'Mednafen (PC Engine)': MednafenModule('pce', ['pce', 'sgx', 'iso', 'cue', 'ccd', 'toc', 'm3u']),
	#Mednafen assumes that there is only 1 gamepad and it's the 6 button kind, so button mapping is kind of weird when I
	#was perfectly fine just using 2 buttons
	'Mednafen (PC Engine Fast)': MednafenModule('pce_fast', ['pce', 'sgx', 'iso', 'cue', 'ccd', 'toc', 'm3u']),
	'Mednafen (NES)': MednafenModule('nes', ['nes', 'fds', 'unf']),
	'Mednafen (Virtual Boy)': MednafenModule('vb', ['bin', 'vb']),
	'Stella': Emulator('stella -fullscreen 1 $<path>', ['a26', 'bin', 'rom'], ['gz', 'zip']),
	'PokeMini': Emulator('PokeMini -fullscreen $<path>', ['min'], ['zip']),
	'PokeMini (wrapper)': Emulator('PokeMini.sh -fullscreen $<path>', ['min'], ['zip']),
	'Mednafen (Lynx)': MednafenModule('lynx', ['lnx', 'lyx', 'o']),
	#Sorta has like...  2 sets of A and B buttons, and 3 buttons on one side and 2 on the other?  It's supposed to be
	#ambidextrous or something which is cool in real life but not so great here, I might need to look more into it and
	#then maybe move it into the normal-but-less-cool platforms
	'Mednafen (WonderSwan)': MednafenModule('wswan', ['ws', 'wsc', 'bin']),
	#Oof this is just super mega weird because you can turn the thing sideways and it still does a thing.  I'll need some
	#point of reference to figure out how to set this up for a normal-ish gamepad...
	#, 'command_line': 'mednafen -video.fs 1 {0}', 'supported_extensions': , 'supported_compression': ['gz', 'zip']
	'Mednafen (PS1)': MednafenModule('psx', ['iso', 'cue', 'exe', 'toc', 'ccd', 'm3u']),
	#Seems like some PAL games don't run at the resolution Mednafen thinks they should, so they need per-game configs
	#that override the scanline start/end settings
	'Dolphin': Emulator('dolphin-emu -b -e $<path>', ['iso', 'gcz', 'elf', 'dol', 'wad'], []),
	#, 'command_line': 'citra-qt {0}', 'supported_extensions': , 'supported_compression': []
	'Citra': Emulator('citra-qt $<path>', ['3ds', 'cxi', '3dsx'], []),
	#Will not run full screen from the command line and you always have to set it manually whether you like it or not (I
	#do not)
	'Medusa': Emulator('medusa-emu-qt -f $<path>', ['nds'], ['7z', 'zip']),
	'PCSX2': Emulator('pcsx2 --nogui --fullscreen --fullboot $<path>', ['iso', 'cso', 'bin'], ['gz']),
	#Has a few problems.  Takes some time to load the interface so at first it might look like it's not working; take out --fullboot if it forbids any homebrew stuff (but it should be fine, and Katamari Damacy needs it).  ELF still doesn't work, though it'd need a different command line anyway
	'Mednafen (Saturn)': MednafenModule('ss', ['cue', 'toc', 'ccd', 'm3u']),
	#Doesn't do .iso for whatever strange reason, which is a bit unfortunate. Might do .bin executables? Probably not
	'Mednafen (Game Boy)': MednafenModule('gb', ['gb', 'gbc']),
	#Would not recommend due to this being based on VisualBoyAdvance, it's just here for completeness
	'Mednafen (GBA)': MednafenModule('gba', ['gba']),
	#Would not recommend due to this being based on VisualBoyAdvance, it's just here for completeness
	'Mednafen (Game Gear)': MednafenModule('gg', ['gg']),
	#Apparently "a low-priority system in terms of proactive maintenance and bugfixes"
	'Mednafen (Master System)': MednafenModule('gg', ['gg']),
	#Apparently "a low-priority system in terms of proactive maintenance and bugfixes"
	'Mednafen (Mega Drive)': MednafenModule('md', ['md', 'bin', 'gen', 'smd', 'sgd']),
	#Apparently "should still be considered experimental; there are still likely timing bugs in the 68K emulation code, the YM2612 emulation code is not particularly accurate, and the VDP code has timing-related issues."
	'Mednafen (SNES)': MednafenModule('snes', ['sfc', 'smc', 'swc']),
	#Based on bsnes v0.059, probably not so great on toasters. Not sure how well it works necessarily, probably doesn't do Sufami Turbo or Satellaview
	'Mednafen (SNES-Faust)': MednafenModule('snes_faust', ['sfc', 'smc', 'swc']),
	#Experimental and doesn't support expansion chips
	'PrBoom+': Emulator(make_prboom_plus_command_line, ['wad'], []),
	#Joystick support not so great, otherwise it plays perfectly well with keyboard + mouse; except the other issue where it doesn't really like running in fullscreen when more than one monitor is around (to be precise, it stops that second monitor updating). Can I maybe utilize some kind of wrapper?  I guess it's okay because it's not like I don't have a mouse and keyboard though the multi-monitor thing really is not okay

	'MAME (Atari 5200)': MameSystem(make_mame_command_line('a5200', 'cart'), ['bin', 'rom', 'car', 'a52']),
	#Analog stuff like Gorf doesn't really work that well, but it doesn't in real life either; could use -sio casette
	#-cass *.wav if there was ever a game that came as a .wav which apparently could be a thing in theory
	'MAME (Watara Supervision)': MameSystem(make_mame_command_line('svision', 'cart'), ['bin', 'ws', 'sv']),
	#I've been told the sound is that horrible on a real system; there are "TV Link" variant systems but that just makes
	#the colours look even worse (they're all inverted and shit)
	'MAME (PV-1000)': MameSystem(make_mame_command_line('pv1000', 'cart'), ['bin']),
	'MAME (Arcadia 2001)': MameSystem(make_mame_command_line('arcadia', 'cart'), ['bin']),
	#Can also use bndarc for Bandai version but that doesn't seem to make any difference at all?  Some games seem to be
	#weird with the input so that sucks
	'MAME (Entex Adventure Vision)': MameSystem(make_mame_command_line('advision', 'cart'), ['bin']),
	#Doesn't work with the "Code Red" demo last time I tried
	'MAME (Vectrex)': MameSystem(make_mame_command_line('vectrex', 'cart'), ['bin', 'gam', 'vec']),
	#I wonder if there's a way to set the overlay programmatically...  doesn't look like there's a command line option to
	#do that.  Also the buttons are kinda wack I must admit, as they're actually a horizontal row of 4
	#, 'command_line': 'mame megaduck -skip_gameinfo -cart {0}', 'supported_extensions': ['bin'], 'supported_compression': ['7z', 'zip']
	'MAME (Mega Duck)': MameSystem(make_mame_command_line('megaduck', 'cart'), ['bin']),
	'MAME (Amstrad GX4000)': MameSystem(make_mame_command_line('gx4000', 'cart'), ['bin', 'cpr']),
	#"But why not just use Amstrad CPC+?" you ask, well, there's no games that are on CPC+ cartridges that aren't on
	#GX4000, and I don't feel like fondling around with disks and tapes
	'MAME (Amstrad CPC+)': MameSystem(make_mame_command_line('cpc6128p', 'cart'), ['bin', 'cpr']),
	#Just in case I change my mind on that. cpc464p is a different CPC+ model but I'm not sure that would be useful?
	'MAME (Gamate)': MameSystem(make_mame_command_line('gamate', 'cart'), ['bin']),
	'MAME (Game Pocket Computer)': MameSystem(make_mame_command_line('gamepock', 'cart'), ['bin']),
	'MAME (Neo Geo CD)': MameSystem(make_mame_command_line('neocdz', 'cdrom'), MAME_CDROM_FORMATS),
	#This is interesting, because this runs alright on toasters, but Neo Geo-based arcade games do not (both being
	#emulated in MAME); meaning I am probably doing something wrong.  Don't think it has region lock so I should never
	#need to use neocdzj? (neocd doesn't work, apparently because it thinks it has the drive tray open constantly)
	'MAME (ColecoVision)': MameSystem(make_mame_command_line('coleco', 'cart'), ['bin', 'col', 'rom']),
	#Controls are actually fine in-game, just requires a keypad to select levels/start games and that's not consistent at
	#all so good luck with that (but mapping 1 to Start seems to work well).  All carts are either USA or combination USA/Europe and are required by Coleco to run on both regions, so why play in 50Hz when we don't have to
	'MAME (Intellivision)': MameSystem(make_mame_command_line('intv', 'cart'), ['bin', 'int', 'rom', 'itv']),
	#Well this sure is a shit console.  There's no consistency to how any game uses any buttons or keypad keys (is it the
	#dial?  Is it keys 2 4 6 8?, so good luck with that; also 2 player mode isn't practical because some games use the
	#left controller and some use the right, so you have to set both controllers to the same inputs; and Pole Position has
	#glitchy graphics.  Why did Mattel make consoles fuck you Mattel I hope you burn
	'MAME (Intellivoice)': MameSystem(make_mame_command_line('intvoice', 'cart'), ['bin', 'int', 'rom', 'itv']),
	#Anyway, might as well use the voice module here since it shouldn't break any existing games 
	'MAME (Intellivision ECS)': MameSystem(make_mame_command_line('intvecs', 'cart'), ['bin', 'int', 'rom', 'itv']),
	#The ECS module does, in fact, break some existing games (I've heard so anyway, don't know which ones), but it is here for usage anyway
	'MAME (Intellivision Keyboard)': MameSystem(make_mame_command_line('intvkbd', 'cart'), ['bin', 'int', 'rom', 'itv']),
	#This was unreleased, but there are dumps of the keyboard-using games out there
	'MAME (APF-MP1000)': MameSystem(make_mame_command_line('apfm1000', 'cart'), ['bin']),
	'MAME (Astrocade)': MameSystem(make_mame_command_line('astrocde', 'cart', {'exp': 'rl64_ram'}), ['bin']),
	#There's a keypad there which is used for game selection/setup, otherwise it just uses a paddle with a button (the
	#actual controllers IRL were wacky, but for emulation purposes are otherwise pretty normal).  Hopefully adding that
	#RAM expansion won't hurt?  Some games (Chicken) seem to be broken anyway with expansion or without whoops
	'MAME (Channel F)': MameSystem(make_mame_command_line('channelf', 'cart'), ['bin', 'chf']),
	#How the fuck do these controls work?  Am I just too much of a millenial?
	'MAME (MSX1)': MameSystem(make_mame_command_line('svi738', 'cart1', has_keyboard=True), ['bin', 'rom']),
	#Note that MSX2 is backwards compatible anyway, so there's not much reason to use this, unless you do have some reason. This model in particular is used because it should be completely in English and if anything goes wrong I'd be able to understand it. I still don't know how disks work (they don't autoboot), or if there's even a consistent command to use to boot them.
	'MAME (MSX2)': MameSystem(make_mame_command_line('fsa1wsx', 'cart1', has_keyboard=True), ['bin', 'rom']),
	#This includes MSX2+ because do you really want me to make those two separate things? Turbo-R doesn't work in MAME though, so that'd have to be its own thing. This model is used just because I looked it up and it seems like the best one, the MSX2/MSX2+ systems in MAME are all in Japanese (the systems were only really released in Japan, after all) so you can't avoid that part. Still don't understand disks.
	'MAME (PV-2000)': MameSystem(make_mame_command_line('pv2000', 'cart', has_keyboard=True), ['bin']),
	#Not the same as the PV-1000!  Although it might as well be, except it's a computer, and they aren't compatible with each other.  MAME says it
	#doesn't work but it seems alright, other than it's supposed to have joysticks and doesn't (so you just set up a
	#gamepad to map to emulated cursor keys) which maybe is why they say it's preliminary
	'MAME (Sord M5)': MameSystem(make_mame_command_line('m5', 'cart', {'ramsize': '64K'}, True), ['bin']),
	#Apparently has joysticks with no fire button?  Usually space seems to be fire but sometimes 1 is, which is usually
	#for starting games.  I hate everything.
	'MAME (CD-i)': MameSystem(make_mame_command_line('cdimono1', 'cdrom'), MAME_CDROM_FORMATS),
	#This is the only CD-i model that works, and it says it's not working, but it seems fine
	'MAME (Game.com)': MameSystem(make_mame_command_line('gamecom', 'cart1'), ['bin', 'tgc']),
	#I don't know what the other cart slot does, or if you can use two at once, or how that would work if you could. Hopefully I don't need it for anything
	'MAME (Tomy Tutor)': MameSystem(make_mame_command_line('tutor', 'cart', has_keyboard=True), ['bin']),
	#Well, at least there's no region crap, though there is pyuuta if you want to read Japanese instead.  The controls in
	#the menus are a bit wack but I think I've set them up so it should work relatively smoothly, also there's not really
	#a way to skip the "Graphics/BASIC/Cartridge" screen that I know of so you'll always have to select that
	'MAME (VIC-10)': MameSystem(make_mame_command_line('vic10', 'cart', {'joy1': 'joy', 'joy2': 'joy'}, has_keyboard=True), ['crt', '80', 'e0']),
	#More similar to the C64 than the VIC-20, need to plug a joystick into both ports because once again games can use
	#either port and thanks I hate it.  At least there's only one TV type
	'MAME (Sharp X1)': MameSystem(make_mame_command_line('x1turbo40', 'flop1', has_keyboard=True), MAME_FLOPPY_FORMATS + ['2d']),
	#Hey!!  We finally have floppies working!!  Because they boot automatically!  Assumes that they will all work fine
	#though without any other disks, and this will need to be updated if we see any cartridges (MAME says it has a cart
	#slot)...
	'MAME (Sharp X68000)': MameSystem(make_mame_command_line('x68000', 'flop1', has_keyboard=True), MAME_FLOPPY_FORMATS + ['xdf', 'hdm', '2hd', 'dim']),	
	'MAME (Atari 8-bit)': MameSystem(build_a800_command_line, ['bin', 'rom', 'car']),
	#Might get a bit of slowdown on toaster if you open the MAME menu, but usually you'd want to do that when paused
	#anyway, and the games themselves run fine	
	'MAME (VIC-20)': MameSystem(build_vic20_command_line, ['20', '40', '60', '70', 'a0', 'b0', 'crt']),
	#Need to figure out which region to use and we can only really do that by filename, also it doesn't like 16KB carts;
	#disks and tapes are a pain in the ass IRL so MAME emulates the ass-pain of course; and I dunno about .prg files,
	#those are just weird (but it'd be great if I could get those working though); with this and C64 there are some games
	#where you'll have to manually change to the paddle which kinda sucks but I guess it can't be helped and also turn on
	#"Paddle Reverse" in "Analog Controls" for some reason
	'MAME (C64)': MameSystem(build_c64_command_line, ['80', 'a0', 'e0', 'crt']),
	#Same kerfluffle with regions and different media formats here.  Could use c64c/c64cp for the newer model with the
	#new SID chip, but that might break compatibility I dunno; could also use sx64 for some portable version, there's a
	#whole bunch of models; c64gs doesn't really have much advantages (just like in real life) except for those few
	#cartridges that were made for it specifically.
	'MAME (Atari 7800)': MameSystem(build_atari7800_command_line, ['bin', 'a78']),
	'MAME (Game Boy)': MameSystem(make_mame_command_line('gbpocket', 'cart'), ['bin', 'gb', 'gbc']),
	'MAME (Super Game Boy)': MameSystem(make_mame_command_line('supergb2', 'cart'), ['bin', 'gb', 'gbc']),
	'MAME (Game Boy Color)': MameSystem(make_mame_command_line('gbcolor', 'cart'), ['bin', 'gb', 'gbc']),
	'MAME (GBA)': MameSystem(make_mame_command_line('gba', 'cart'), ['bin', 'gba']),
	'MAME (Game Gear)': MameSystem(make_mame_command_line('gamegear', 'cart'), ['bin', 'gg']),
	'MAME (Neo Geo Pocket)': MameSystem(make_mame_command_line('ngpc', 'cart'), ['bin', 'ngp', 'npc', 'ngc']),
	'MAME (Pokemon Mini)': MameSystem(make_mame_command_line('pokemini', 'cart'), ['bin', 'min']),
	#Wouldn't recommend yet as it has no sound, even if most people would probably turn the sound off in real life
	'MAME (SG-1000)': MameSystem(make_mame_command_line('sg1000', 'cart'), ['bin', 'sg']),
	'MAME (Virtual Boy)': MameSystem(make_mame_command_line('vboy', 'cart'), ['bin', 'vb']),
	#Doesn't do red/blue stereo 3D, instead just outputing two screens side by side (you can go cross-eyed to see the 3D effect, but that'll hurt your eyes after a while (just like in real life)). Also has a bit of graphical glitches here and there; no ROMs required though so that's neat
	'MAME (WonderSwan)': MameSystem(make_mame_command_line('wscolor', 'cart'), ['ws', 'wsc', 'bin']),
	'MAME (Sufami Turbo)': MameSystem(make_snes_addon_cart_command_line, ['st']),
	#Snes9x's GTK+ port doesn't let us load carts with slots for other carts from the command line yet, so this will have
		#to do, but unfortunately it's a tad slower
	'MAME (Satellaview)': MameSystem(make_snes_addon_cart_command_line, ['bs']),
	#Also you still have to go through all the menus and stuff for BS-X/Satellaview/whatsitcalled

	#Other systems that MAME can do but I'm too lazy to do them yet because they'd need a command line generator function:
	#Lynx: Need to select -quick for .o files and -cart otherwise
	#SC-3000: Need to select -cart for carts and -cass for cassettes (.wav .bit); I'm not sure Kega Fusion can do .sc or cassettes yet
	#SF-7000: Need to select -flop for disk images (sf7 + normal MAME disk formats) and -cass for cassettes (.wav .bit); very sure Kega Fusion can't do this
	#NES, SMS, Megadrive, SNES, Atari 2600: Need to detect region 
	#	(Notable that Megadrive and SNES support lock-on carts, i.e. Sonic & Knuckles, Sufami Turbo respectively)
	#N64: Does not do PAL at all. The game might even tell you off if it's a PAL release
	#PC Engine: Need to select between pce and tg16 depending on region, -cdrom and -cart slots, and sgx accordingly

}
