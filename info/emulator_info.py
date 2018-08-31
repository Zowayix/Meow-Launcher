import sys
import shlex
import os
import configparser

import config

import info.emulator_command_lines as command_lines

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

class MednafenModule(Emulator):
	def __init__(self, module, supported_extensions, command_line=None):
		if not command_line:
			command_line = command_lines.make_mednafen_command_line(module)
		Emulator.__init__(self, command_line, supported_extensions, ['zip', 'gz'])

class MameSystem(Emulator):
	def __init__(self, command_line, supported_extensions):
		Emulator.__init__(self, command_line, supported_extensions, ['7z', 'zip'])

mame_cdrom_formats = ['iso', 'chd', 'cue', 'toc', 'nrg', 'cdr', 'gdi']
#Some drivers have custom floppy formats, but these seem to be available for all
mame_floppy_formats = ['d77', 'd88', '1dd', 'dfi', 'hfe', 'imd', 'ipf', 'mfi', 'mfm', 'td0', 'cqm', 'cqi', 'dsk']
	
emulators = {
	'Citra': Emulator(command_lines.citra, ['3ds', 'cxi', '3dsx'], []),
	#Will not run full screen from the command line and you always have to set it manually whether you like it or not (I
	#do not, but eh, it works and that's really cool)
	'Dolphin': Emulator(command_lines.dolphin, ['iso', 'gcz', 'elf', 'dol', 'wad'], []),
	'Gambatte': Emulator(command_lines.gambatte, ['gb', 'gbc'], ['zip']),
	#--gba-cgb-mode[=0] and --force-dmg-mode[=0] may be useful in obscure situations
	'Kega Fusion': Emulator(command_lines.kega_fusion, ['bin', 'gen', 'md', 'smd', 'sgd', 'gg', 'sms', 'iso', 'cue', 'sg', 'sc', '32x'], ['zip']),
	#May support other CD formats for Mega CD other than iso, cue?
	'Medusa': Emulator(command_lines.medusa, ['nds'], ['7z', 'zip']),
	'mGBA': Emulator(command_lines.mgba, ['gb', 'gbc', 'gba', 'srl', 'bin', 'mb'], ['7z', 'zip']),
	#Use -C useBios=0 for homebrew with bad checksum/logo that won't boot on real hardware.  Some intensive games (e.g.
	#Doom) will not run at full speed on toaster, but generally it's fine
	'Mupen64Plus': Emulator(command_lines.mupen64plus, ['z64', 'v64', 'n64'], []),
	#Often pretty slow on toaster but okay for turn-based games; environment variable is needed for GLideN64 which sometimes is
	#preferred over Rice and sometimes not (the latter wins at speed and not much else).  Do I still need that environment
	#variable?  I think I might
	'PCSX2': Emulator('pcsx2 --nogui --fullscreen --fullboot $<path>', ['iso', 'cso', 'bin'], ['gz']),
	#Has a few problems.  Takes some time to load the interface so at first it might look like it's not working; take out --fullboot if it forbids any homebrew stuff (but it should be fine, and Katamari Damacy needs it).  ELF still doesn't work, though it'd need a different command line anyway
	'PokeMini': Emulator('PokeMini -fullscreen $<path>', ['min'], ['zip']),
	#Puts all the config files in the current directory, which is why there's a wrapper below which you probably want to use instead of this
	'PokeMini (wrapper)': Emulator('mkdir -p ~/.config/PokeMini && cd ~/.config/PokeMini && PokeMini -fullscreen $<path>', ['min'], ['zip'], True),
	'PPSSPP': Emulator('ppsspp-qt $<path>', ['iso', 'pbp', 'cso'], []),
	'Reicast': Emulator(command_lines.reicast, ['gdi', 'cdi', 'chd'], []),
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
	'Mednafen (NES)': MednafenModule('nes', ['nes', 'fds', 'unf'], command_lines.mednafen_nes),
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

	'MAME (Amstrad CPC+)': MameSystem(command_lines.mame_command_line('cpc6128p', 'cart'), ['bin', 'cpr']),
	#Just in case I change my mind on using GX4000. cpc464p is a different CPC+ model but I'm not sure that would be useful?
	'MAME (Amstrad GX4000)': MameSystem(command_lines.mame_command_line('gx4000', 'cart'), ['bin', 'cpr']),
	#"But why not just use Amstrad CPC+?" you ask, well, there's no games that are on CPC+ cartridges that aren't on
	#GX4000, and I don't feel like fondling around with disks and tapes if I can avoid it
	'MAME (APF-MP1000)': MameSystem(command_lines.mame_command_line('apfm1000', 'cart'), ['bin']),
	'MAME (Arcadia 2001)': MameSystem(command_lines.mame_command_line('arcadia', 'cart'), ['bin']),
	#Can also use bndarc for Bandai version but that doesn't seem to make any difference at all?  Some games seem to be
	#weird with the input so that sucks
	#TOOD: What kind of weird? Perhaps I don't actually know what I'm doing
	'MAME (Astrocade)': MameSystem(command_lines.mame_command_line('astrocde', 'cart', {'exp': 'rl64_ram'}), ['bin']),
	#There's a keypad there which is used for game selection/setup, otherwise it just uses a paddle with a button (the
	#actual controllers IRL were wacky, but for emulation purposes are otherwise pretty normal).  Hopefully adding that
	#RAM expansion won't hurt?  Some games (Chicken) seem to be broken anyway with expansion or without whoops
	'MAME (Atari 2600)': MameSystem(command_lines.mame_atari_2600, ['bin', 'a26']),
	'MAME (Atari 5200)': MameSystem(command_lines.mame_command_line('a5200', 'cart'), ['bin', 'rom', 'car', 'a52']),
	#Analog stuff like Gorf doesn't really work that well, but it doesn't in real life either; could use -sio casette
	#-cass *.wav if there was ever a game that came as a .wav which apparently could be a thing in theory
	'MAME (Atari 7800)': MameSystem(command_lines.mame_atari_7800, ['bin', 'a78']),
	'MAME (Atari 8-bit)': MameSystem(command_lines.mame_atari_8bit, ['bin', 'rom', 'car']),
	#Might get a bit of slowdown on toaster if you open the MAME menu, but usually you'd want to do that when paused
	#anyway, and the games themselves run fine	
	'MAME (C64)': MameSystem(command_lines.mame_c64, ['80', 'a0', 'e0', 'crt']),
	#Same kerfluffle with regions and different media formats here.  Could use c64c/c64cp for the newer model with the
	#new SID chip, but that might break compatibility I dunno; could also use sx64 for some portable version, there's a
	#whole bunch of models; c64gs doesn't really have much advantages (just like in real life) except for those few
	#cartridges that were made for it specifically.
	'MAME (CD-i)': MameSystem(command_lines.mame_command_line('cdimono1', 'cdrom'), mame_cdrom_formats),
	#This is the only CD-i model that works, and it says it's not working, but it seems fine
	'MAME (Channel F)': MameSystem(command_lines.mame_command_line('channelf', 'cart'), ['bin', 'chf']),
	#How the fuck do these controls work?  Am I just too much of a millenial?
	'MAME (ColecoVision)': MameSystem(command_lines.mame_command_line('coleco', 'cart'), ['bin', 'col', 'rom']),
	#Controls are actually fine in-game, just requires a keypad to select levels/start games and that's not consistent at
	#all so good luck with that (but mapping 1 to Start seems to work well).  All carts are either USA or combination USA/Europe and are required by Coleco to run on both regions, so why play in 50Hz when we don't have to
	'MAME (Coleco Adam)': MameSystem(command_lines.mame_command_line('adam', 'cass1', {'net4': '""', 'net5': '""'}, has_keyboard=True), ['wav', 'ddp']),
	#Uses tapes, but they just boot automatically, so it's fine I guess.
	#TODO: Do disks as well, if I had any. Also Adam-specific carts I guess? Not sure how those work, or if the cartridge port is just there for Colecovision compatibility and I'm a doofus
	'MAME (Entex Adventure Vision)': MameSystem(command_lines.mame_command_line('advision', 'cart'), ['bin']),
	#Doesn't work with the "Code Red" demo last time I tried
	'MAME (Gamate)': MameSystem(command_lines.mame_command_line('gamate', 'cart'), ['bin']),
	'MAME (Game.com)': MameSystem(command_lines.mame_command_line('gamecom', 'cart1'), ['bin', 'tgc']),
	#I don't know what the other cart slot does, or if you can use two at once, or how that would work if you could. Hopefully I don't need it for anything
	'MAME (Game Boy)': MameSystem(command_lines.mame_command_line('gbpocket', 'cart'), ['bin', 'gb', 'gbc']),
	'MAME (Game Boy Color)': MameSystem(command_lines.mame_command_line('gbcolor', 'cart'), ['bin', 'gb', 'gbc']),
	'MAME (Game Gear)': MameSystem(command_lines.mame_command_line('gamegear', 'cart'), ['bin', 'gg']),
	'MAME (Game Pocket Computer)': MameSystem(command_lines.mame_command_line('gamepock', 'cart'), ['bin']),
	'MAME (GBA)': MameSystem(command_lines.mame_command_line('gba', 'cart'), ['bin', 'gba']),
	'MAME (Intellivision)': MameSystem(command_lines.mame_command_line('intv', 'cart'), ['bin', 'int', 'rom', 'itv']),
	#Well this sure is a shit console.  There's no consistency to how any game uses any buttons or keypad keys (is it the
	#dial?  Is it keys 2 4 6 8?, so good luck with that; also 2 player mode isn't practical because some games use the
	#left controller and some use the right, so you have to set both controllers to the same inputs; and Pole Position has
	#glitchy graphics.  Why did Mattel make consoles fuck you Mattel I hope you burn
	'MAME (Intellivoice)': MameSystem(command_lines.mame_command_line('intvoice', 'cart'), ['bin', 'int', 'rom', 'itv']),
	#Anyway, might as well use the voice module here since it shouldn't break any existing games 
	#TODO: Merge these four Intellivision consoles into one, and automatically detect if voice, ECS, or keyboard needs to be used. The tricky part will be to detect that.
	'MAME (Intellivision ECS)': MameSystem(command_lines.mame_command_line('intvecs', 'cart'), ['bin', 'int', 'rom', 'itv']),
	#The ECS module does, in fact, break some existing games (I've heard so anyway, don't know which ones), but it is here for usage anyway
	'MAME (Intellivision Keyboard)': MameSystem(command_lines.mame_command_line('intvkbd', 'cart'), ['bin', 'int', 'rom', 'itv']),
	#This was unreleased, but there are dumps of the keyboard-using games out there
	'MAME (Juice Box)': MameSystem(command_lines.mame_command_line('juicebox', 'memcard'), ['smc']),
	#Oh also this is slow by the way, should warn y'all
	'MAME (Mega Duck)': MameSystem(command_lines.mame_command_line('megaduck', 'cart'), ['bin']),
	'MAME (MSX1)': MameSystem(command_lines.mame_command_line('svi738', 'cart1', {'fdc:0': '""'}, has_keyboard=True), ['bin', 'rom']),
	#Note that MSX2 is backwards compatible anyway, so there's not much reason to use this, unless you do have some reason. This model in particular is used because it should be completely in English and if anything goes wrong I'd be able to understand it. I still don't know how disks work (they don't autoboot), or if there's even a consistent command to use to boot them.
	'MAME (MSX2)': MameSystem(command_lines.mame_command_line('fsa1wsx', 'cart1', {'fdc:0': '""'}, has_keyboard=True), ['bin', 'rom']),
	#This includes MSX2+ because do you really want me to make those two separate things? Turbo-R doesn't work in MAME though, so that'd have to be its own thing. This model is used just because I looked it up and it seems like the best one, the MSX2/MSX2+ systems in MAME are all in Japanese (the systems were only really released in Japan, after all) so you can't avoid that part. Still don't understand disks.
	'MAME (Neo Geo CD)': MameSystem(command_lines.mame_command_line('neocdz', 'cdrom'), mame_cdrom_formats),
	#This is interesting, because this runs alright on toasters, but Neo Geo-based arcade games do not (both being
	#emulated in MAME); meaning I am probably doing something wrong.  Don't think it has region lock so I should never
	#need to use neocdzj? (neocd doesn't work, apparently because it thinks it has the drive tray open constantly)
	'MAME (Neo Geo Pocket)': MameSystem(command_lines.mame_command_line('ngpc', 'cart'), ['bin', 'ngp', 'npc', 'ngc']),
	'MAME (NES)': MameSystem(command_lines.mame_nes, ['nes', 'unf', 'unif', 'fds']),
	'MAME (Pokemon Mini)': MameSystem(command_lines.mame_command_line('pokemini', 'cart'), ['bin', 'min']),
	#Wouldn't recommend yet as it has no sound, even if most people would probably turn the sound off in real life
	'MAME (PC-88)': MameSystem(command_lines.mame_command_line('pc8801', 'flop1', has_keyboard=True), mame_floppy_formats),
	#TODO: Tapes, and potentially look into other models. All the PC-88 models claim to be broken, but the base one plays the games, so that's good enough in my book. Some might use BASIC though so I'd have to specially handle that?
	'MAME (PV-1000)': MameSystem(command_lines.mame_command_line('pv1000', 'cart'), ['bin']),
	'MAME (PV-2000)': MameSystem(command_lines.mame_command_line('pv2000', 'cart', has_keyboard=True), ['bin']),
	#Not the same as the PV-1000!  Although it might as well be, except it's a computer, and they aren't compatible with each other.  MAME says it
	#doesn't work but it seems alright, other than it's supposed to have joysticks and doesn't (so you just set up a
	#gamepad to map to emulated cursor keys) which maybe is why they say it's preliminary
	'MAME (SG-1000)': MameSystem(command_lines.mame_sg1000, ['bin', 'sg', 'sc', 'sf7'] + mame_floppy_formats),
	'MAME (Sharp X1)': MameSystem(command_lines.mame_command_line('x1turbo40', 'flop1', has_keyboard=True), mame_floppy_formats + ['2d']),
	#Hey!!  We finally have floppies working!!  Because they boot automatically!  Assumes that they will all work fine
	#though without any other disks, and this will need to be updated if we see any cartridges (MAME says it has a cart
	#slot)...
	'MAME (Sharp X68000)': MameSystem(command_lines.mame_sharp_x68000, mame_floppy_formats + ['xdf', 'hdm', '2hd', 'dim', 'm3u']),
	#It doesn't	really support m3u, but I'm going to make it so it does
	'MAME (SNES)': MameSystem(command_lines.mame_snes, ['sfc', 'bs', 'st']),
	'MAME (Sord M5)': MameSystem(command_lines.mame_command_line('m5', 'cart1', {'ramsize': '64K', 'upd765:0': '""'}, True), ['bin']),
	#Apparently has joysticks with no fire button?  Usually space seems to be fire but sometimes 1 is, which is usually
	#for starting games.  I hate everything.
	'MAME (Super Game Boy)': MameSystem(command_lines.mame_command_line('supergb2', 'cart'), ['bin', 'gb', 'gbc']),
	'MAME (Tomy Tutor)': MameSystem(command_lines.mame_command_line('tutor', 'cart', has_keyboard=True, autoboot_script='tomy_tutor'), ['bin']),
	#Well, at least there's no region crap, though there is pyuuta if you want to read Japanese instead
	'MAME (Uzebox)': MameSystem(command_lines.mame_command_line('uzebox', 'cart'), ['bin', 'uze']),
	#Runs really slowly, but it works, also heck it
	'MAME (VC 4000)': MameSystem(command_lines.mame_command_line('vc4000', 'cart'), ['bin', 'rom']),
	#There's like 30 different clones of this, and most of them aren't even clones in the MAME sense, they're literally hardware clones. But they're apparently all software-compatible, although the cartridges aren't hardware-compatible, they just contain the same software... so this all gets confusing. Anyway, the software list with all these is named "vc4000" so I guess that's the "main" one, so we'll use that. I'm not sure if there are any PAL/NTSC differences to worry about.
	#TODO: Quickload slot (.pgm, .tvc)
	'MAME (Vectrex)': MameSystem(command_lines.mame_command_line('vectrex', 'cart'), ['bin', 'gam', 'vec']),
	#I wonder if there's a way to set the overlay programmatically...  doesn't look like there's a command line option to
	#do that.  Also the buttons are kinda wack I must admit, as they're actually a horizontal row of 4
	'MAME (VIC-10)': MameSystem(command_lines.mame_command_line('vic10', 'cart', {'joy1': 'joy', 'joy2': 'joy'}, has_keyboard=True), ['crt', '80', 'e0']),
	#More similar to the C64 than the VIC-20, need to plug a joystick into both ports because once again games can use
	#either port and thanks I hate it.  At least there's only one TV type
	'MAME (VIC-20)': MameSystem(command_lines.mame_vic_20, ['20', '40', '60', '70', 'a0', 'b0', 'crt']),
	#Need to figure out which region to use and we can only really do that by filename, also it doesn't like 16KB carts;
	#disks and tapes are a pain in the ass IRL so MAME emulates the ass-pain of course; and I dunno about .prg files,
	#those are just weird (but it'd be great if I could get those working though); with this and C64 there are some games
	#where you'll have to manually change to the paddle which kinda sucks but I guess it can't be helped and also turn on
	#"Paddle Reverse" in "Analog Controls" for some reason
	'MAME (Virtual Boy)': MameSystem(command_lines.mame_command_line('vboy', 'cart'), ['bin', 'vb']),
	#Doesn't do red/blue stereo 3D, instead just outputing two screens side by side (you can go cross-eyed to see the 3D effect, but that'll hurt your eyes after a while (just like in real life)). Also has a bit of graphical glitches here and there; no ROMs required though so that's neat
	'MAME (VZ-200)': MameSystem(command_lines.mame_command_line('vz200', 'dump', {'io': 'joystick', 'mem': 'laser_64k'}, True), ['vz']),
	#In the Laser 200/Laser 210 family, but Dick Smith variant should do.
	#TODO see if casettes (wav cas) or disks (mame_floppy_formats, mem slot = floppy) work nicely
	#Joystick interface doesn't seem to be used by any games, but I guess it does more than leaving the IO slot unfilled. That sucks, because otherwise no game ever uses the keyboard consistently, because of course not. Even modern homebrew games. Why y'all gotta be like that?
	#Some games will need you to type RUN to run them, not sure how to detect that.
	'MAME (Watara Supervision)': MameSystem(command_lines.mame_command_line('svision', 'cart'), ['bin', 'ws', 'sv']),
	#I've been told the sound is that horrible on a real system; there are "TV Link" variant systems but that just makes
	#the colours look even worse (they're all inverted and shit)
	'MAME (WonderSwan)': MameSystem(command_lines.mame_command_line('wscolor', 'cart'), ['ws', 'wsc', 'bin', 'pc2']),
	'MAME (ZX Spectrum)': MameSystem(command_lines.mame_zx_spectrum, ['ach', 'frz', 'plusd', 'prg', 'sem', 'sit', 'sna', 'snp', 'snx', 'sp', 'z80', 'zx'] + mame_floppy_formats),

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

def is_doom_file(file):
	if file.extension != 'wad':
		return False

	return file.read(amount=4) == b'IWAD'

engines = {
	'PrBoom+': GameEngine(make_prboom_plus_command_line, is_doom_file),
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
