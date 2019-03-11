manufacturer_overrides = {
	#Stuff that appears in machines/software lists but it's the same company but formatted in different ways (suffixes/punctuation/spacing/whatnot), and maybe neither is more correct but it's no fun to have inconsistent naming

	#Anyway. Some of these are bit... contentious? Is that the right word? Like, some of these are definitely different ways of spelling the same company and that's definitely a valid thing to deal with, but then some of these might well just be different brands used by the same company, because companies are weird like that. So at some point I'll probably need to clean this up. Hmm...
	#Yeah let's make this a big TODO to verify what formatting companies actually use themselves

	#TODO: Are ATW > ATW USA Inc. the same or a regional branch?
	#Should NEC Avenue just be called NEC?
	#Should Sony Computer Entertainment Inc and Sony Imagesoft be just Sony?
	#Toshiba EMI > Toshiba?
	#Are CBS Electronics and CBS Software the same? Seems like they're both owned by CBS the American TV company, the former is for various Atari 2600/5200/7800 games they published and distributing the ColecoVision outside USA; and the latter is basically licensed Sesame Street games?
	#Are Fox Interactive, Fox Video Games, 20th Century Fox all the same?
	#Human == Human Amusement?
	#Ultra, Ultra Games, Konami (Ultra Games)?
	#Universal == Universal Video Games?
	#BBC Worldwide == BBC Multimedia? I mean they're obviously both the BBC
	#Empire Entertainment == Empire Interactive?
	#New Image Technologies == New Image?
	#Naxat == Naxat Soft?
	#The SNES game Super Godzilla (USA) has a publisher of literally "Super Godzilla". Wait what? That can't be right. Should be Toho right? Same with Tetris (Japan) for Megadrive. Unless they meant The Tetris Company there.
	#Leave Atari Games > Atari and Midway Games > Midway alone, because if I try to comperehend the timeline of which is what and who owned the rights to which brand name and who owned who at any given time, I would die of confusion
	#Marvelous Entertainment and Marvelous Interactive also are different (due to mergers) and I gotta remember that

	'20th Century Fox Video Games': '20th Century Fox',
	'Absolute': 'Absolute Entertainment', #Hmm, not sure if it'd be better to do this the other way around
	'Acclaim Entertainment': 'Acclaim',
	'American Softworks Company': 'American Softworks',
	'ASCII Entertainment': 'ASCII',
	'Bally Gaming': 'Bally',
	'BPS': 'Bullet-Proof Software', #I hope nobody else uses that acronym
	'Broderbund Software': 'Brøderbund',
	'Brøderbund Software': 'Brøderbund',
	'California Pacific Computer': 'California Pacific',
	'Coconuts Japan Entertainment': 'Coconuts Japan',
	'Creative Software': 'Creative',
	'Cryo': 'Cryo Interactive',
	'Data East Corporation': 'Data East',
	'Dempa Shinbunsha': 'Dempa',
	'Eidos Interactive': 'Eidos',
	'Elite': 'Elite Systems',
	'Entex Industries': 'Entex',
	'First Star': 'First Star Software',
	'Grandslam Entertainments': 'Grandslam',
	'Gremlin Interactive': 'Gremlin Graphics',
	'HAL Kenkyuujo': 'HAL', #Literally "HAL Laboratory"
	'HAL Laboratory': 'HAL',
	'Hasbro Interactive': 'Hasbro',
	'HiCom': 'Hi-Com',
	'Hudson': 'Hudson Soft',
	'Human Entertainment': 'Human',
	'International Business Machines': 'IBM',
	'JoWooD Entertainment AG': 'JoWooD Entertainment',
	'Kaneko Elc.': 'Kaneko',
	'K-Tel Vision': 'K-Tel',
	'Laser Beam': 'Laser Beam Entertainment',
	'MicroCabin': 'Micro Cabin', #Annoying alternate spelling because they officially use both just to be annoying
	'Microlab': 'Micro Lab',
	'Microprose Games': 'MicroProse',
	'NEC Home Electronics': 'NEC',
	'Nihon Telenet': 'Telenet', #I guess
	'Ocean Software': 'Ocean',
	'Omage Micott': 'Omega Micott', #I have a feeling I'm the one who's wrong here. Never did quality check the Wonderswan licensees
	'Omori Electric': 'Omori',
	'Palm Inc': 'Palm',
	'Playmates Interactive': 'Playmates',
	'PonyCa': 'Pony Canyon',
	'ProSoft': 'Prosoft',
	'Sammy Entertainment': 'Sammy',
	'Seta Corporation': 'Seta',
	'Sierra Entertainment': 'Sierra',
	'Sierra On-Line': 'Sierra',
	'Sigma Enterprises': 'Sigma', #Every time I see this line I keep thinking "sigma balls", just thought you should know
	'Software Toolworks': 'The Software Toolworks', #It doesn't seem right that the "correct" one is the latter, but it's used more often, so I guess it is
	'Spinnaker Software': 'Spinnaker',
	'Sunrise Software': 'Sunrise',
	'Taito Corporation': 'Taito',
	'Taito Corporation Japan': 'Taito',
	'Taito America Corporation': 'Taito America',
	'Team 17': 'Team17',
	'TecMagik Entertainment': 'TecMagik',
	'T*HQ': 'THQ', #Why.
	'Titus Software': 'Titus',
	'V.Fame': 'Vast Fame',
	'Viacom New Media': 'Viacom',
	'Visco Corporation': 'Visco',
	'Virgin Games': 'Virgin',
	'Virgin Interactive': 'Virgin',
	'Vivendi Universal': 'Vivendi', #Probably kinda wrong, but ehhh
	'Williams Entertainment': 'Williams',

	#Sometimes companies go by two different names and like... maybe I should leave those alone, bleh I hate decision making
	'DSI Games': 'Destination Software',
	'dtp Entertainment': 'Digital Tainment Pool',
	'Square': 'Squaresoft', #Which is the frickin' right one?
	'Ultra Games': 'Konami (Ultra Games)', #This is questionable to format it like this, but... I'll contemplate which one is better some other time

	#This isn't a case of a company formatting its name in different ways, but it's where a company's renamed itself, and maybe I shouldn't do this...
	'Alpha Denshi Co.': 'ADK', #Renamed in 1993
	'Ubi Soft': 'Ubisoft', #I hate that they used to spell their name with a space so this is valid. But then, don't we all hate Ubisoft for one reason or another?
	#Video Technology > VTech

	#Brand names that are definitely the same company but insist on using some other name... maybe I shouldn't change these either
	'Atarisoft': 'Atari', #Atarisoft is just a brand name and not an actual company, so I guess I'll do this
	'Disney Interactive': 'Disney',
	'Disney Interactive Studios': 'Disney',
	'Disney Software': 'Disney',
	'Dreamworks Games': 'DreamWorks',
	'LEGO Media': 'Lego',
	'Mattel Electronics': 'Mattel',
	'Mattel Interactive': 'Mattel',
	'Mattel Media': 'Mattel',
	'Nihon Bussan': 'Nichibutsu',
	'Nihonbussan': 'Nichibutsu', #In the event that we figure out we shouldn't change the above, we should at least consistentify this formatting

	#For some reason, some Japanese computer software lists have the Japanese name and then the English one in brackets. Everywhere else the English name is used even when the whole thing is Japanese. Anyway I guess we just want the English name then, because otherwise for consistency, I'd have to convert every single English name into Japanese
	'B·P·S (Bullet-Proof Software)': 'Bullet-Proof Software',
	'HOT・B': 'Hot-B',
	'アートディンク (Artdink)': 'Artdink',
	'アイレム (Irem)': 'Irem',
	'アスキー (ASCII)': 'ASCII',
	'イマジニア (Imagineer)': 'Imagineer',
	'エニックス (Enix)': 'Enix',
	'カプコン (Capcom)': 'Capcom',
	'コナミ (Konami)': 'Konami',
	'コンプティーク (Comptiq)': 'Comptiq',
	'システムサコム (System Sacom)': 'System Sacom',
	'システムソフト (System Soft)': 'System Soft',
	'シャープ (Sharp)': 'Sharp',
	'シンキングラビット (Thinking Rabbit)': 'Thinking Rabbit',
	'スタークラフト (Starcraft)': 'Starcraft',
	'ソフトプロ (Soft Pro)': 'Soft Pro',
	'デービーソフト (dB-Soft)': 'dB-Soft',
	'ニデコム (Nidecom)': 'Nidecom',
	'パックスエレクトロニカ (Pax Electronica)': 'Pax Electronica',
	'ハドソン (Hudson Soft)': 'Hudson Soft',
	'ブラザー工業 (Brother Kougyou)': 'Brother Kougyou',
	'ブローダーバンドジャパン (Brøderbund Japan)': 'Brøderbund Japan',
	'ホームデータ (Home Data)': 'Home Data',
	'ポニカ (Pony Canyon)': 'Pony Canyon',
	'ポニカ (PonyCa)': 'Pony Canyon',
	'マイクロネット (Micronet)': 'Micronet',
	'マカダミアソフト (Macadamia Soft)': 'Macadamia Soft',
	'工画堂スタジオ (Kogado Studio)': 'Kogado Studio',
	'日本ソフトバンク (Nihon SoftBank)': 'Nihon SoftBank',
	'日本テレネット (Nihon Telenet)': 'Telenet',
	'日本ファルコム (Nihon Falcom)': 'Nihon Falcom',
	'電波新聞社 (Dempa Shinbunsha)': 'Dempa',

	#YELLING CASE / other capitalisation stuff
	'BEC': 'Bec',
	'Dreamworks': 'DreamWorks',
	'enix': 'Enix',
	'EPYX': 'Epyx',
	'Microprose': 'MicroProse',
	'SONY': 'Sony',
	'SpectraVideo': 'Spectravideo',
	'Spectrum HoloByte': 'Spectrum Holobyte',
	'VAP': 'Vap',

	#Maybe typos?
	'Commonweaalth': 'Commonwealth',
	'Connonwealth': 'Commonwealth',
	'Elite System': 'Elite Systems',
	'Hi Tech Expressions': 'Hi-Tech Expressions',
	'Jungle\'s Soft / Ultimate Products (HK)': 'Jungle Soft / Ultimate Products (HK)',
	'Mindscapce': 'Mindscape', #Yeah okay, that _definitely_ is a typo
	'Pack-In-Video': 'Pack-In Video',
	'Sydney Developmeent': 'Sydney Development',
	'Take Two Interactive': 'Take-Two Interactive',
	'Watera': 'Watara',

	'unknown': '<unknown>', #This shows up in sv8000 software list, so it might actually just be Bandai, but when you presume you make a pres out of u and me, so we'll just lump it in with the other unknowns
}