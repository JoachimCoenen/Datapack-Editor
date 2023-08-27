from dataclasses import replace

from corePlugins.mcFunction.command import KeywordSchema, MCFunctionSchema
# temporarily copied from model/data/mcVersion.py
from .mcVersions import MCVersion, getMCVersion
from .v1_17_schema import buildMCFunctionSchemaFor_v1_17


def buildMCFunctionSchemas() -> dict[str, MCFunctionSchema]:
	version1_18 = getMCVersion('1.18')
	schema_1_18 = buildMCFunctionSchemaFor_v1_18(version1_18)
	return {'Minecraft 1.18': schema_1_18}


def buildMCFunctionSchemaFor_v1_18(version: MCVersion) -> MCFunctionSchema:
	schema = buildMCFunctionSchemaFor_v1_17(version)

	# add 'block_marker' particle:
	particles = schema.commands[b'particle'].next
	block_marker = replace(next(p for p in particles if p.name == 'block' and isinstance(p, KeywordSchema)), name='block_marker')
	schema.commands[b'particle'].next.insert(-1, block_marker)

	return schema
