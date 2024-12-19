from corePlugins.mcFunction.argumentTypes import *
from corePlugins.mcFunction.command import ArgumentSchema, KeywordSchema
from .argumentTypes import *
from base.model.parsing.bytesUtils import strToBytes
from corePlugins.mcFunction.filterArgs import FilterArgOptions, FALLBACK_FILTER_ARGUMENT_INFO, FilterArgumentInfo, \
	NegationStyle

itemComponentNames: list[str] = [
	'attribute_modifiers',
	'banner_patterns',
	'base_color',
	'bees',
	'block_entity_data',
	'block_state',
	'bucket_entity_data',
	'bundle_contents',
	'can_break',
	'can_place_on',
	'charged_projectiles',
	'consumable',
	'container',
	'container_loot',
	'custom_data',
	'custom_model_data',
	'custom_name',
	'damage',
	'damage_resistant',
	'debug_stick_state',
	'death_protection',
	'dyed_color',
	'enchantable',
	'enchantment_glint_override',
	'enchantments',
	'entity_data',
	'equippable',
	'firework_explosion',
	'fireworks',
	'food',
	'glider',
	'hide_additional_tooltip',
	'hide_tooltip',
	'instrument',
	'intangible_projectile',
	'item_model',
	'item_name',
	'jukebox_playable',
	'lock',
	'lodestone_tracker',
	'lore',
	'map_color',
	'map_decorations',
	'map_id',
	'max_damage',
	'max_stack_size',
	'note_block_sound',
	'ominous_bottle_amplifier',
	'pot_decorations',
	'potion_contents',
	'profile',
	'rarity',
	'recipes',
	'repairable',
	'repair_cost',
	'stored_enchantments',
	'suspicious_stew_effects',
	'tool',
	'tooltip_style',
	'trim',
	'unbreakable',
	'use_cooldown',
	'use_remainder',
	'writable_book_content',
	'written_book_content',

]


itemComponentArguments: list[FilterArgumentInfo] = [
	FilterArgumentInfo(
		keySchema=KeywordSchema(name),
		valueSchema=ArgumentSchema(
			name=name,
			type=MINECRAFT_NBT_TAG,
			args=dict(schema=f'minecraft:{name}')
		),
		multipleAllowed=False,
		isNegatable=True,
		canBeEmpty=True,
		description=""
	)
	for name in itemComponentNames
]

ITEM_COMPONENT_ARGUMENTS_DICT: dict[bytes, FilterArgumentInfo] = {
	strToBytes(tsa.keySchema.name): tsa
	for tsa in itemComponentArguments
}


ITEM_COMPONENT_ARG_OPTIONS: FilterArgOptions = FilterArgOptions(
	opening=b'[',
	closing=b']',
	allowTrailingComma=False,
	negationStyle=NegationStyle.KEY_NEGATION,
	keySchema=ArgumentSchema(
		name='key',
		type=makeLiteralsArgumentType(list(ITEM_COMPONENT_ARGUMENTS_DICT.keys())),
	),
	getArgsInfo=lambda key: ITEM_COMPONENT_ARGUMENTS_DICT.get(key.content, FALLBACK_FILTER_ARGUMENT_INFO),
	description=""
)


__all__ = [
	'ITEM_COMPONENT_ARGUMENTS_DICT',
	'ITEM_COMPONENT_ARG_OPTIONS',
]
