from __future__ import annotations

from corePlugins.mcFunction.argumentTypes import ArgumentType, LiteralsArgumentType

CHAT_COLORS: set[bytes] = {
	b'black',
	b'dark_blue',
	b'dark_green',
	b'dark_aqua',
	b'dark_red',
	b'dark_purple',
	b'gold',
	b'gray',
	b'dark_gray',
	b'blue',
	b'green',
	b'aqua',
	b'red',
	b'light_purple',
	b'yellow',
	b'white',
}

TEAM_COLORS: set[bytes] = {
	b'reset',
	*CHAT_COLORS,
}

ENTITY_ANCHORS: set[bytes] = {b'eyes', b'feet'}

GAME_MODES: list[bytes] = [b'adventure', b'creative', b'spectator', b'survival']


MINECRAFT_ANGLE = ArgumentType(
	name='minecraft:angle',
	description="{{Arg desc|je=angle}}",
	description2="""""",
	examples="""
	* {{cd|0}}
	* {{cd|~}}
	* {{cd|~-0.5}}""",
)

# args:
#   -'type': (int|float), default = int
MINECRAFT_BLOCK_POS = ArgumentType(
	name='minecraft:block_pos',
	description="{{Arg desc|je=block_pos}}",
	description2="""""",
	examples="""
	* {{cd|0 0 0}}
	* {{cd|~ ~ ~}}
	* {{cd|^ ^ ^}}
	* {{cd|^1 ^ ^-5}}
	* {{cd|~0.5 ~1 ~-5}}""",
)

MINECRAFT_BLOCK_PREDICATE = ArgumentType(
	name='minecraft:block_predicate',
	description="<!--{{Arg desc|je=block_predicate}}-->",
	description2="""
	The format of block_predicate parameters is <code>''block_id''[''block_states'']{''data_tags''}</code>, in which block states and data tags can be omitted when they are not needed.
	* <code>block_id</code> is required, and it should be in the format of [[resourse location]](if namespace isn't set it defaults to <code>minecraft:</code>).
	** It can also be the resource location of a [[Tags|block tag]] prefixed with <code>#</code>, such as <code>#minecraft:planks</code>.
	* [[Block state]]s are inside <code>[]</code>, comma-separated and must be properties/values supported by the blocks. They are optional.
	** <code>minecraft:stone[doesntexist=purpleberry]</code> is unparseable, because <code>stone</code> doesn't have <code>doesntexist</code>.
	** <code>minecraft:redstone_wire[power=tuesday]</code> is unparseable, because <code>redstone_wire</code>'s <code>power</code> is a number between 0 and 15.
	* [[NBT format|Data tags]] are inside <code>{}</code>. It's optional.
	* When test for block, only the states provided are tested.
	** If command tests <code>redstone_wire[power=15]</code>, it checks only power, but ignores other states such as <code>north</code>.""",
	examples="""
	* {{cd|stone}}
	* {{cd|minecraft:stone}}
	* <code>stone[foo=bar]</code>
	* {{cd|#stone}}
	* <code>#stone[foo=bar]{baz:nbt}</code>""",
)

MINECRAFT_BLOCK_STATE = ArgumentType(
	name='minecraft:block_state',
	description="<!--{{Arg desc|je=block_state}}-->",
	description2="""
	The format of block_state parameters is <code>''block_id''[''block_states'']{''data_tags''}</code>, in which block states and data tags can be omitted when they are not needed.
	* <code>block_id</code> is required, and it should be in the format of [[resourse location]] (if namespace isn't set it defaults to <code>minecraft:</code>).
	* [[Block state]]s are inside <code>[]</code>, comma-separated and must be properties/values supported by the blocks. They are optional.
	** <code>minecraft:stone[doesntexist=purpleberry]</code> is unparseable, because <code>stone</code> doesn't have <code>doesntexist</code>.
	** <code>minecraft:redstone_wire[power=tuesday]</code> is unparseable, because <code>redstone_wire</code>'s <code>power</code> is a number between 0 and 15.
	* [[NBT format|Data tags]] are inside <code>{}</code>. It's optional.
	* When placing blocks, any states provided are set, but anything omitted retain their default values, depending on the block type.
	** If command sets <code>redstone_wire[power=15]</code>, it is set <code>power</code> to 15, but <code>north</code> is a default value (in this case, set to <code>none</code>).""",
	examples="""
	* {{cd|stone}}
	* {{cd|minecraft:stone}}
	* <code>stone[foo=bar]</code>
	* <code>foo{bar:baz}</code>""",
)

MINECRAFT_COLOR = LiteralsArgumentType(
	name='minecraft:color',
	options=sorted(TEAM_COLORS),
	description="Must be a team color (= `reset` or one of the 16 chat colors.)",
	description2="""""",
	examples="""
	* {{cd|red}}
	* {{cd|green}}""",
)

MINECRAFT_COLUMN_POS = ArgumentType(
	name='minecraft:column_pos',
	description="Must be a column coordinates composed of `<x>` and `<z>`, each of which must be an integer or tilde notation.",
	description2="""""",
	examples="""
	* {{cd|0 0}}
	* {{cd|~ ~}}
	* {{cd|~1 ~-2}}""",
)

MINECRAFT_COMPONENT = ArgumentType(
	name='minecraft:component',
	description="Must be a raw JSON text.",
	description2="""""",
	examples="""
	* {{cd|"hello world"}}
	* {{cd|""}}
	* {{cd|{"text":"hello world"} }}
	* {{cd|[""]}}""",
)

MINECRAFT_DIMENSION = ArgumentType(
	name='minecraft:dimension',
	description="Must be the resource location of a dimension. ",
	description2="""""",
	examples="""
	* {{cd|minecraft:overworld}}
	* {{cd|minecraft:the_nether}}""",
)

MINECRAFT_ENTITY = ArgumentType(
	name='minecraft:entity',
	description="Must be a player name, a target selector or a UUID.",
	description2="""
	Each entity argument may place limits on the number of entities (single/multiple) selected or the type of entities (player/any entity) selected.
	""",
	examples="""
	* {{cd|Player}}
	* {{cd|0123}}
	* {{cd|@e}}
	* <code>@e[type=foo]</code>
	* {{cd|dd12be42-52a9-4a91-a8a1-11c01849e498}}""",
	jsonProperties="""
	* {{nbt|compound|properties}}: The root properties object.
	** {{nbt|string|amount}}: The amount of entities that can be selected. Can be {{cd|single}} or {{cd|multiple}}.
	** {{nbt|string|type}}: The target entity type. Can be {{cd|players}} or {{cd|entities}}. """,
)

MINECRAFT_ENTITY_ANCHOR = LiteralsArgumentType(
	name='minecraft:entity_anchor',
	options=sorted(ENTITY_ANCHORS),
	description="Must be either `eyes` or `feet`.",
	description2="""""",
	examples="""
	* {{cd|eyes}}
	* {{cd|feet}}""",
)

MINECRAFT_ENTITY_SUMMON = ArgumentType(
	name='minecraft:entity_summon',
	description="Must be an entity type in the format of resource location of a summonable entity type.",
	description2="""""",
	examples="""
	* {{cd|minecraft:pig}}
	* {{cd|cow}}""",
)

MINECRAFT_ENTITY_TYPE = ArgumentType(
	name='dpe:entity_type',
	description="Must be an entity type in the format of resource location of a entity type or entity type tag.",
	description2="""""",
	examples="""
	* {{cd|minecraft:pig}}
	* {{cd|cow}}
	* {{cd|#du:undead}}""",
)

MINECRAFT_FLOAT_RANGE = ArgumentType(
	name='minecraft:float_range',
	description="Must be a range acceptable for float values. (e.g. `0.1` - exact match of `0.1`. `..0.1` - less than or equal to `0.1`. `0.1..` - more than or equal to `0.1`. `0.1..1` - between `0.1` and `1`, inclusive.)",
	description2="""""",
	examples="""
	* {{cd|0..5.2}}
	* {{cd|0}}
	* {{cd|-5.4}}
	* {{cd|-100.76..}}
	* {{cd|..100}}""",
)

MINECRAFT_FUNCTION = ArgumentType(
	name='minecraft:function',
	description="It must be a resource location, which refers to a single function, or one prefixed with a `#`, which refers to a function tag. ",
	description2="""""",
	examples="""
	* {{cd|foo}}
	* {{cd|foo:bar}}
	* {{cd|#foo}}""",
)

MINECRAFT_GAME_MODE = LiteralsArgumentType(
	name='game_mode',
	options=GAME_MODES,
	description="Must be a valid game mode",
	description2="""""",
	examples="""
	* {{cd|survival}}
	* {{cd|creative}}""",
)

MINECRAFT_GAME_PROFILE = ArgumentType(
	name='minecraft:game_profile',
	description="Must be a collection of game profiles (player profiles), which can be a player name (must be a real one if the server is in online mode), or a player-type target selector.",
	description2="""""",
	examples="""
	* {{cd|Player}}
	* {{cd|0123}}
	* {{cd|dd12be42-52a9-4a91-a8a1-11c01849e498}}
	* {{cd|@e}}""",
)

MINECRAFT_INT_RANGE = ArgumentType(
	name='minecraft:int_range',
	description="Must be a range acceptable for integer values. (e.g. `0` - exact match of `0`. `..0` - less than or equal to `0`. `0..` - more than or equal to `0`. `0..1` - between `0` and `1`, inclusive.)",
	description2="""""",
	examples="""
	* {{cd|0..5}}
	* {{cd|0}}
	* {{cd|-5}}
	* {{cd|-100..}}
	* {{cd|..100}}""",
)

MINECRAFT_ITEM_ENCHANTMENT = ArgumentType(
	name='minecraft:item_enchantment',
	description="Must be an ID of an enchantment.",
	description2="""""",
	examples="""
	* {{cd|unbreaking}}
	* {{cd|silk_touch}}""",
)

MINECRAFT_ITEM_PREDICATE = ArgumentType(
	name='minecraft:item_predicate',
	description="",
	description2="""
	The format of item_predicate parameters is <code>''item_id''{''data_tags''}</code>, in which data tags can be omitted when not needed.
	* <code>item_id</code> is required, and it should be in the format of [[resourse location]] (if namespace isn't set it defaults to <code>minecraft:</code>).
	** It can also be the resource location of a [[Tags|block tag or item tag]] with the prefix of <code>#</code>, such as <code>#minecraft:planks</code>.
	* [[#Data tags|Data tags]] are inside <code>{}</code>. It's optional.
	** When clear or test for item, only the states provided are tested.""",
	examples="""
	* {{cd|stick}}
	* {{cd|minecraft:stick}}
	* {{cd|#stick}}
	* <code>#stick{foo:bar}</code>""",
)

MINECRAFT_ITEM_SLOT = ArgumentType(
	name='minecraft:item_slot',
	description="Must be a string notation that refer to certain slots in the inventory.",
	description2="""
	{{see also|Commands/replaceitem}}
	The slot reference is mapped to an integer.
	
	:::{| class="wikitable sortable" data-description="Slot mapping"
	!Slot
	!Valid ''slot_number''
	!Mapped index
	|-
	|<code>armor.chest</code>
	|
	|align="center"|102
	|-
	|<code>armor.feet</code>
	|
	|align="center"|100
	|-
	|<code>armor.head</code>
	|
	|align="center"|103
	|-
	|<code>armor.legs</code>
	|
	|align="center"|101
	|-
	|<code>weapon</code>
	|
	|align="center"|98
	|-
	|<code>weapon.mainhand</code>
	|
	|align="center"|98
	|-
	|<code>weapon.offhand</code>
	|
	|align="center"|99
	|-
	|<code>container.''slot_number''</code>
	|align="center"|0-53
	|align="center"|0-53
	|-
	|<code>enderchest.''slot_number''</code>
	|align="center"|0-26
	|align="center"|200-226
	|-
	|<code>hotbar.''slot_number''</code>
	|align="center"|0-8
	|align="center"|0-8
	|-
	|<code>inventory.''slot_number''</code>
	|align="center"|0-26
	|align="center"|9-35
	|-
	|<code>horse.saddle</code><br/>
	|
	|align="center"|400
	|-
	|<code>horse.chest</code>
	|
	|align="center"|499
	|-
	|<code>horse.armor</code>
	|
	|align="center"|401
	|-
	|<code>horse.''slot_number''</code>
	|align="center"|0-14
	|align="center"|500-514
	|-
	|<code>villager.''slot_number''</code>
	|align="center"|0-7
	|align="center"|300-307
	|}
	
	Then, restrictions are applied to mapped indexes.
	
	:::{| class="wikitable sortable" data-description="Restrictions"
	!Mapped index
	!Restrictions
	|-
	|0-53
	|General inventories
	|-
	|98-103
	|[[Mobs]], [[player]]s, and [[armor stand]]s
	|-
	|200-226
	|[[Player]]s
	|-
	|300-307
	|[[Villager]]s, [[pillager]]s
	|-
	|400-401
	|[[Horse]]s, [[donkey]]s
	|-
	|499-514
	|[[Donkey]]s with chest
	|}""",
	examples="""
	* {{cd|container.5}}
	* {{cd|12}}
	* {{cd|weapon}}""",
)

MINECRAFT_ITEM_STACK = ArgumentType(
	name='minecraft:item_stack',
	description="",
	description2="""
	The format of item_stack parameters is <code>''item_id''{''data_tags''}</code>, in which data tags can be omitted when not needed.
	* <code>item_id</code> is required, and it should be in the format of [[resourse location]] (if namespace isn't set it defaults to <code>minecraft:</code>).
	* [[#Data tags|Data tags]] are inside <code>{}</code>. It's optional.
	* When giving items, any states provided are set, but anything omitted retain their default values, depending on the item type.""",
	examples="""
	* {{cd|stick}}
	* {{cd|minecraft:stick}}
	* <code>stick{foo:bar}</code>""",
)

MINECRAFT_LOOT_TABLE = ArgumentType(
	name='minecraft:loot_table',
	description="{{Arg desc|je=resource_location}}",
	description2="""resource location of a loot table.""",
	examples="""""",
)

MINECRAFT_MESSAGE = ArgumentType(
	name='minecraft:message',
	description="Must be a plain text. Can include spaces as well as target selectors. The game replaces entity selectors in the message with the list of selected entities' names, which is formatted as \"name1 and name2\" for two entities, or \"name1, name2, ... and namen\" for n entities.",
	description2="""""",
	examples="""
	* {{cd|Hello world!}}
	* {{cd|foo}}
	* {{cd|@e}}
	* {{cd|Hello @p :)}}""",
)

MINECRAFT_MOB_EFFECT = ArgumentType(
	name='minecraft:mob_effect',
	description="Must be an ID of a status effect.",
	description2="""""",
	examples="""
	* {{cd|spooky}}
	* {{cd|effect}}""",
)

MINECRAFT_NBT_COMPOUND_TAG = ArgumentType(
	name='minecraft:nbt_compound_tag',
	description="Must be a compound NBT in SNBT format.",
	description2="""""",
	examples="""
	* <code>{}</code>
	* <code>{foo:bar}</code>""",
)

MINECRAFT_NBT_PATH = ArgumentType(
	name='minecraft:nbt_path',
	description="Must be an NBT path.",
	description2="""""",
	example="""
	{{cd|foo.bar[0]."A [crazy name]".baz.}}
	<div class="treeview">
	* {{cd|foo}}
	** {{cd|bar}}
	*** ''<the first list element>''
	**** {{cd|A [crazy name]}}
	***** '''{{cd|baz}}'''
	*** ''<the second list element>''
	</div>""",
	examples="""
	* {{cd|foo}}
	* {{cd|foo.bar}}
	* {{cd|foo[0]}}
	* {{cd|[0]}}
	* <code>[]</code>
	* <code>{foo:bar}</code>""",
)

MINECRAFT_NBT_TAG = ArgumentType(
	name='minecraft:nbt_tag',
	description="Must be an NBT tag of any type in SNBT format.",
	description2="""""",
	examples="""
	* {{cd|0}}
	* {{cd|0b}}
	* {{cd|0l}}
	* {{cd|0.0}}
	* {{cd|"foo"}}
	* <code>{foo:bar}</code>""",
)

MINECRAFT_OBJECTIVE = ArgumentType(
	name='minecraft:objective',
	description="It must be an valid scoreboard objective name.",
	description2="""""",
	examples="""
	* {{cd|foo}}
	* {{cd|*}}
	* {{cd|012}}""",
)

MINECRAFT_OBJECTIVE_CRITERIA = ArgumentType(
	name='minecraft:objective_criteria',
	description="Must be a scoreboard objective criterion.",
	description2="""""",
	examples="""
	* {{cd|foo}}
	* {{cd|foo.bar.baz}}
	* {{cd|minecraft:foo}}""",
)

MINECRAFT_OPERATION = LiteralsArgumentType(
	name='minecraft:operation',
	options=[b'=', b'+=', b'-=', b'*=', b'/=', b'%=', b'><', b'<', b'>'],
	description="Must be an arithmetic operator for `/scoreboard`.\n"
				"Valid values include = (assignment), += (addition), -= (subtraction), *= (multiplication), /= (floor division), %= (modulus), >< (swapping), < (choosing minimum) and > (choosing maximum).",
	description2="""""",
	examples="""
	* <code>=</code>
	* {{cd|>}}
	* {{cd|<}}""",
)

MINECRAFT_PARTICLE = ArgumentType(
	name='minecraft:particle',
	description="{{Arg desc|je=particle}}",
	description2="""""",
	examples="""
	* {{cd|foo}}
	* {{cd|foo:bar}}
	* {{cd|particle with options}}""",
)

MINECRAFT_PREDICATE = ArgumentType(
	name='minecraft:predicate',
	description="{{Arg desc|je=resource_location}}",
	description2="""resource location of a predicate.""",
	examples="""""",
)

MINECRAFT_RESOURCE_LOCATION = ArgumentType(
	name='minecraft:resource_location',
	description="{{Arg desc|je=resource_location}}",
	description2="""""",
	examples="""
	* {{cd|foo}}
	* {{cd|foo:bar}}""",
)

MINECRAFT_ROTATION = ArgumentType(
	name='minecraft:rotation',
	description="{{Arg desc|je=rotation}}",
	description2="""""",
	examples="""
	* {{cd|0 0}}
	* {{cd|~ ~}}
	* {{cd|~-5 ~5}}""",
)

MINECRAFT_SCORE_HOLDER = ArgumentType(
	name='minecraft:score_holder',
	description="Must be a selection of score holders. It may be either a target selector, a player name, a UUID, or * for all score holders tracked by the scoreboard. Named player needn't be online, and it even needn't be a real player's name.",
	description2="""Each score holder argument may specify if it can select only one score holder or multiple score holders.""",
	examples="""
	* {{cd|Player}}
	* {{cd|0123}}
	* {{cd|*}}
	* {{cd|@e}}""",
	jsonProperties="""
	* {{nbt|compound|properties}}: The root properties object.
	** {{nbt|string|amount}}: The amount of score holders that can be selected. Can be {{cd|single}} or {{cd|multiple}}.""",
)

MINECRAFT_SCOREBOARD_SLOT = ArgumentType(
	name='minecraft:scoreboard_slot',
	description="{{Arg desc|je=scoreboard_slot}}",
	description2="""""",
	examples="""
	* {{cd|sidebar}}
	* {{cd|foo.bar}}""",
)

MINECRAFT_SWIZZLE = ArgumentType(
	name='minecraft:swizzle',
	description="{{Arg desc|je=swizzle}}",
	description2="""""",
	examples="""
	* {{cd|xyz}}
	* {{cd|x}}""",
)

MINECRAFT_TEAM = ArgumentType(
	name='minecraft:team',
	description="{{Arg desc|je=team}}",
	description2="""""",
	examples="""
	* {{cd|foo}}
	* {{cd|123}}""",
)

MINECRAFT_TIME = ArgumentType(
	name='minecraft:time',
	description="{{Arg desc|je=time}}",
	description2="""""",
	examples="""
	* {{cd|0d}}
	* {{cd|0s}}
	* {{cd|0t}}
	* {{cd|0}}""",
)

MINECRAFT_UUID = ArgumentType(
	name='minecraft:uuid',
	description="{{Arg desc|je=uuid}}",
	description2="""""",
	examples="""
	* {{cd|dd12be42-52a9-4a91-a8a1-11c01849e498}}""",
)

MINECRAFT_VEC2 = ArgumentType(
	name='minecraft:vec2',
	description="{{Arg desc|je=vec2}}",
	description2="""""",
	examples="""
	* {{cd|0 0}}
	* {{cd|~ ~}}
	* {{cd|0.1 -0.5}}
	* {{cd|~1 ~-2}}""",
)

MINECRAFT_VEC3 = ArgumentType(
	name='minecraft:vec3',
	description="{{Arg desc|je=vec3}}",
	description2="""""",
	examples="""
	* {{cd|0 0 0}}
	* {{cd|~ ~ ~}}
	* {{cd|^ ^ ^}}
	* {{cd|^1 ^ ^-5}}
	* {{cd|0.1 -0.5 .9}}
	* {{cd|~0.5 ~1 ~-5}}""",
)

DPE_ADVANCEMENT = ArgumentType(
	name='dpe:advancement',
	description="{{Arg desc|je=resource_location}}",
	description2="""""",
	examples="""
	* {{cd|foo}}
	* {{cd|foo:bar}}
	* {{cd|012}}""",
)


DPE_COMPARE_OPERATION = LiteralsArgumentType(
	name='dpe:compare_operation',
	options=[b'<=', b'<', b'=', b'>=', b'>'],
	description="(<|<=|=|>=|>)",
	description2="""""",
	examples="""""",
	jsonProperties="""""",
)


DPE_BIOME_ID = ArgumentType(
	name='dpe:biome_id',
	description="resource location of a biome",
	description2="""""",
	examples="""""",
	jsonProperties="""""",
)


###################################################
# SubTypes:
###################################################


ST_DPE_DATAPACK = ArgumentType(
	name='dpe:datapack',
	description="{{Arg desc|je=string}}",
	description2="""Each string argument type can accept either a single word (no spaces), a quotable phrase (either single word or quoted string), or a greedy phrase (taking the rest of the command as the string argument).""",
	examples="""""",
	jsonProperties="""""",
)

__all__ = [
	'CHAT_COLORS',
	'TEAM_COLORS',
	'ENTITY_ANCHORS',
	'GAME_MODES',

	'MINECRAFT_ANGLE',
	'MINECRAFT_BLOCK_POS',
	'MINECRAFT_BLOCK_PREDICATE',
	'MINECRAFT_BLOCK_STATE',
	'MINECRAFT_COLOR',
	'MINECRAFT_COLUMN_POS',
	'MINECRAFT_COMPONENT',
	'MINECRAFT_DIMENSION',
	'MINECRAFT_ENTITY',
	'MINECRAFT_ENTITY_ANCHOR',
	'MINECRAFT_ENTITY_SUMMON',
	'MINECRAFT_ENTITY_TYPE',
	'MINECRAFT_FLOAT_RANGE',
	'MINECRAFT_FUNCTION',
	'MINECRAFT_GAME_MODE',
	'MINECRAFT_GAME_PROFILE',
	'MINECRAFT_INT_RANGE',
	'MINECRAFT_ITEM_ENCHANTMENT',
	'MINECRAFT_ITEM_PREDICATE',
	'MINECRAFT_ITEM_SLOT',
	'MINECRAFT_ITEM_STACK',
	'MINECRAFT_LOOT_TABLE',
	'MINECRAFT_MESSAGE',
	'MINECRAFT_MOB_EFFECT',
	'MINECRAFT_NBT_COMPOUND_TAG',
	'MINECRAFT_NBT_PATH',
	'MINECRAFT_NBT_TAG',
	'MINECRAFT_OBJECTIVE',
	'MINECRAFT_OBJECTIVE_CRITERIA',
	'MINECRAFT_OPERATION',
	'MINECRAFT_PARTICLE',
	'MINECRAFT_PREDICATE',
	'MINECRAFT_RESOURCE_LOCATION',
	'MINECRAFT_ROTATION',
	'MINECRAFT_SCORE_HOLDER',
	'MINECRAFT_SCOREBOARD_SLOT',
	'MINECRAFT_SWIZZLE',
	'MINECRAFT_TEAM',
	'MINECRAFT_TIME',
	'MINECRAFT_UUID',
	'MINECRAFT_VEC2',
	'MINECRAFT_VEC3',
	'DPE_ADVANCEMENT',
	'DPE_COMPARE_OPERATION',
	'DPE_BIOME_ID',
	'ST_DPE_DATAPACK',
]