from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class DefaultFileInfo:
	name: str
	namespace: Optional[str]
	contents: str


@dataclass(frozen=True)
class FolderInfo:
	folder: str
	extensions: tuple[str, ...]
	initialFiles: list[DefaultFileInfo] = field(default_factory=list)


NAME_SPACE_VAR = '${namespace}'


LOAD_JSON_CONTENTS = f"""{{
	"values": [
		"{NAME_SPACE_VAR}:load"
	]
}}"""

TICK_JSON_CONTENTS = f"""{{
	"values": [
		"{NAME_SPACE_VAR}:tick"
	]
}}"""

LOAD_MCFUNCTION_CONTENTS = f"say loading {NAME_SPACE_VAR} ..."

TICK_MCFUNCTION_CONTENTS = f"# add commands here..."

#######################################################################
# DATAPACK_FOLDERS: ###################################################
#######################################################################

DATAPACK_FOLDERS = [
	# TagInfos:
	FolderInfo(
		'tags/blocks/',
		('.json',),
	),
	FolderInfo(
		'tags/entity_types/',
		('.json',),
	),
	FolderInfo(
		'tags/fluids/',
		('.json',),
	),
	FolderInfo(
		'tags/functions/',
		('.json',),
		initialFiles=[
			DefaultFileInfo(
				'load.json',
				'minecraft',
				LOAD_JSON_CONTENTS
			),
			DefaultFileInfo(
				'tick.json',
				'minecraft',
				TICK_JSON_CONTENTS
			)
		],
	),
	FolderInfo(
		'tags/game_events/',
		('.json',),
	),
	FolderInfo(
		'tags/items/',
		('.json',),
	),

	# WorldGenInfos:
	FolderInfo(
		'worldgen/biome/',
		('.json',),
	),
	FolderInfo(
		'worldgen/configured_carver/',
		('.json',),
	),
	FolderInfo(
		'worldgen/configured_feature/',
		('.json',),
	),
	FolderInfo(
		'worldgen/configured_structure_feature/',
		('.json',),
	),
	FolderInfo(
		'worldgen/configured_surface_builder/',
		('.json',),
	),
	FolderInfo(
		'worldgen/noise_settings/',
		('.json',),
	),
	FolderInfo(
		'worldgen/processor_list/',
		('.json',),
	),
	FolderInfo(
		'worldgen/template_pool/',
		('.json',),
	),

	# DatapackContents:
	FolderInfo(
		'advancements/',
		('.json',),
	),
	FolderInfo(
		'functions/',
		('.mcfunction',),
		initialFiles=[
			DefaultFileInfo(
				'load.mcfunction',
				NAME_SPACE_VAR,
				LOAD_MCFUNCTION_CONTENTS
			),
			DefaultFileInfo(
				'tick.mcfunction',
				NAME_SPACE_VAR,
				TICK_MCFUNCTION_CONTENTS
			)
		],
	),
	FolderInfo(
		'item_modifiers/',
		('.json',),
	),
	FolderInfo(
		'loot_tables/',
		('.json',),
	),
	FolderInfo(
		'predicates/',
		('.json',),
	),
	FolderInfo(
		'recipes/',
		('.json',),
	),
	FolderInfo(
		'structures/',
		('.nbt',),
	),
	FolderInfo(
		'dimension/',
		('.json',),
	),
	FolderInfo(
		'dimension_type/',
		('.json',),
	),
]
