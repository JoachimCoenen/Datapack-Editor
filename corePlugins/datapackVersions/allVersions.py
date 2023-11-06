REGISTRY_TAGS = {
	'tags/attribute':                            'tags/attribute',  # Attribute
	'tags/block':                                'tags/blocks',  # Block
	'tags/block_entity_type':                    'tags/block_entity_type',  # Block entity type
	'tags/chunk_status':                         'tags/chunk_status',  # Chunk status
	'tags/command_argument_type':                'tags/command_argument_type',  # Command argument type
	'tags/dimension':                            'tags/dimension',  # Dimension and Level stem
	'tags/dimension_type':                       'tags/dimension_type',  # Dimension type
	'tags/enchantment':                          'tags/enchantment',  # Enchantment
	'tags/entity_type':                          'tags/entity_types',  # Entity type
	'tags/fluid':                                'tags/fluids',  # Fluid
	'tags/game_event':                           'tags/game_events',  # Game event
	'tags/position_source_type':                 'tags/position_source_type',  # Position source type (used by game events)
	'tags/item':                                 'tags/items',  # Item
	'tags/menu':                                 'tags/menu',  # Menu type
	'tags/mob_effect':                           'tags/mob_effect',  # Mob effect
	'tags/particle_type':                        'tags/particle_type',  # Particle type
	'tags/potion':                               'tags/potion',  # Potion
	'tags/recipe_serializer':                    'tags/recipe_serializer',  # Recipe serializer
	'tags/recipe_type':                          'tags/recipe_type',  # Recipe type
	'tags/sound_event':                          'tags/sound_event',  # Sound event
	'tags/stat_type':                            'tags/stat_type',  # Statistics type
	'tags/custom_stat':                          'tags/custom_stat',  # Custom Statistics
	# Entity data registries
	'tags/activity':                             'tags/activity',  # Entity schedule activity
	'tags/memory_module_type':                   'tags/memory_module_type',  # Entity memory module type
	'tags/schedule':                             'tags/schedule',  # Entity schedule
	'tags/sensor_type':                          'tags/sensor_type',  # Entity AI sensor type
	'tags/motive':                               'tags/motive',  # Painting motive
	'tags/villager_profession':                  'tags/villager_profession',  # Villager profession
	'tags/villager_type':                        'tags/villager_type',  # Villager type
	'tags/point_of_interest_type':               'tags/point_of_interest_type',  # Poi type
	# Loot table serializer registries:
	'tags/loot_condition_type':                  'tags/loot_condition_type',  # Loot condition type
	'tags/loot_function_type':                   'tags/loot_function_type',  # Loot function type
	'tags/loot_nbt_provider_type':               'tags/loot_nbt_provider_type',  # Loot nbt provider type
	'tags/loot_number_provider_type':            'tags/loot_number_provider_type',  # Loot number provider type
	'tags/loot_pool_entry_type':                 'tags/loot_pool_entry_type',  # Loot pool entry type
	'tags/loot_score_provider_type':             'tags/loot_score_provider_type',  # Loot score provider type
	# Json file value provider registries:
	'tags/float_provider_type':                  'tags/float_provider_type',  # Float provider type
	'tags/int_provider_type':                    'tags/int_provider_type',  # Int provider type
	'tags/height_provider_type':                 'tags/height_provider_type',  # Height provider type
	# World generator registries:
	'tags/block_predicate_type':                 'tags/block_predicate_type',  # Block predicate type
	'tags/rule_test':                            'tags/rule_test',  # Structure featrue rule test type
	'tags/pos_rule_test':                        'tags/pos_rule_test',  # Structure featrue position rule test type
	'tags/worldgen/carver':                      'tags/worldgen/carver',  # World carver
	'tags/worldgen/configured_carver':           'tags/worldgen/configured_carver',  # Configured world carver
	'tags/worldgen/feature':                     'tags/worldgen/feature',  # Feature
	'tags/worldgen/configured_feature':          'tags/worldgen/configured_feature',  # Configured feature
	'tags/worldgen/structure_set':               'tags/worldgen/structure_set',  # Structure set
	'tags/worldgen/structure_processor':         'tags/worldgen/structure_processor',  # Structure processor type
	'tags/worldgen/processor_list':              'tags/worldgen/processor_list',  # Structure processor list
	'tags/worldgen/structure_pool_element':      'tags/worldgen/structure_pool_element',  # Structure pool element type
	'tags/worldgen/template_pool':               'tags/worldgen/template_pool',  # Structure template pool
	'tags/worldgen/structure_piece':             'tags/worldgen/structure_piece',  # Structure piece type
	'tags/worldgen/structure_type':              'tags/worldgen/structure_type',  # Structure feature
	'tags/worldgen/structure':                   'tags/worldgen/structure',  # Configured structure feature
	'tags/worldgen/structure_placement':         'tags/worldgen/structure_placement',  # Structure placement type
	'tags/worldgen/placement_modifier_type':     'tags/worldgen/placement_modifier_type',  # Placement modifier type
	'tags/worldgen/placed_feature':              'tags/worldgen/placed_feature',  # Placed feature
	'tags/worldgen/biome':                       'tags/worldgen/biome',  # Biome
	'tags/worldgen/biome_source':                'tags/worldgen/biome_source',  # Biome source
	'tags/worldgen/noise':                       'tags/worldgen/noise',  # Normal noise
	'tags/worldgen/noise_settings':              'tags/worldgen/noise_settings',  # Noise generator settings
	'tags/worldgen/density_function':            'tags/worldgen/density_function',  # Density function
	'tags/worldgen/density_function_type':       'tags/worldgen/density_function_type',  # Density function type
	'tags/worldgen/world_preset':                'tags/worldgen/world_preset',  # World preset
	'tags/worldgen/flat_level_generator_preset': 'tags/worldgen/flat_level_generator_preset',  # Flat world generator preset
	'tags/worldgen/chunk_generator':             'tags/worldgen/chunk_generator',  # Chunk generator
	'tags/worldgen/material_condition':          'tags/worldgen/material_condition',  # Surface condition source
	'tags/worldgen/material_rule':               'tags/worldgen/material_rule',  # Surface rule source
	'tags/worldgen/block_state_provider_type':   'tags/worldgen/block_state_provider_type',  # Block state provider type
	'tags/worldgen/foliage_placer_type':         'tags/worldgen/foliage_placer_type',  # Foliage placer type
	'tags/worldgen/trunk_placer_type':           'tags/worldgen/trunk_placer_type',  # Trunk placer type
	'tags/worldgen/tree_decorator_type':         'tags/worldgen/tree_decorator_type',  # Tree decorator type
	'tags/worldgen/feature_size_type':           'tags/worldgen/feature_size_type',  # Feature size type
}


WORLDGEN = {
	'worldgen/biome':                        'worldgen/biome',
	'worldgen/configured_carver':            'worldgen/configured_carver',
	'worldgen/configured_feature':           'worldgen/configured_feature',
	'worldgen/configured_structure_feature': 'worldgen/configured_structure_feature',
	'worldgen/configured_surface_builder':   'worldgen/configured_surface_builder',
	'worldgen/density_function':             'worldgen/density_function',
	'worldgen/flat_level_generator_preset':  'worldgen/flat_level_generator_preset',
	'worldgen/noise':                        'worldgen/noise',
	'worldgen/noise_settings':               'worldgen/noise_settings',
	'worldgen/placed_feature':               'worldgen/placed_feature',
	'worldgen/processor_list':               'worldgen/processor_list',
	'worldgen/structure':                    'worldgen/structure',
	'worldgen/structure_set':                'worldgen/structure_set',
	'worldgen/template_pool':                'worldgen/template_pool',
	'worldgen/world_preset':                 'worldgen/world_preset',
}
