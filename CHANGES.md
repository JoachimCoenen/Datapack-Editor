## Version 0.3.0-alpha
### Features
 * Added support for different data pack versions (separate from the MC version).
 * Added call tips for mcFunction files.
 * Added syntax checking for JSON files.
 * Added basic code suggestions for JSON files.
 * Added basic code insight (tooltips) for JSON files.
 * Added validation support for JSON files. (issue #4)
 * Added file specific validation & suggestions for tag files (files in 'data/{namespace}/tags/'). (issue #6)
 * Added validation for raw json text (`minecraft:component` type) in mcFunction files.
 * Added custom Styler support, including multi-language support for a single file.
 * Added color scheme support

### Improvements
 * Improved create-new-file dialog.
 * Added `minecraft:predicate` type (for mcFunction validation).
 * Improved code suggestions for mcFunction files.
 * Improved code insight (tooltips) for mcFunction files.
 * JsonStringContext implementations are now part of the datapack version.
 * Added `JsonArgType` to replace the `commands.ArgumentType` for JsonSchemas.
 * Added `gameEvents` field to `MCVersion`.

### Fixes
 * Reverted changes to resource location parsing.
 * Fixed validation of `minecraft:component` command argument returning wrong error type.

## Version 0.2.1-alpha
### Fixes
 * Fixed crash in `clickableRangesForFilterArgs(...)` (issue #19).
 * Fixed crash in `getBestFAMatch(...)` (issue #20).

### Improvements
 * Slightly improved suggestions for coordinates

## Version 0.2.0-alpha
### Features
 * Added support for MC versions 1.17 & 1.18 (can be changed in settings)
 * Exclude specific datapack(s) in "Check All Files" dialog
 * Exclude specific datapack(s) in "Search All" dialog
 * Added progress bar to "Search All" dialog
 * Improved "new Data Pack" dialog
 * Added "About Qt" dialog
 * Added code suggestions for block states (mcFunction)
 * Added code suggestions for target selector arguments (mcFunction)

### Fixes
 * Fixed infinite recursion when parsing incomplete block states.
 * Wrong argument for `execute rotated` subcommand.
 * Added missing entities, blocks, etc...
 * Added Parser for UUIDs.
 * Fixed crash when querying suggestions for `minecraft:item_stack`

### Internal Changes
 * replaced many instances of `SerializableContainer` with `dataclass` 