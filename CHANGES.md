## Next Version
### Features
 * Added support for different data pack versions.
 * Added syntax checking for JSON files.
 * Added validation support for JSON files. (#4)
 * Added basic validation for tag files (files in 'data/{namespace}/tags/'). (#6)

### Improvements
 * Improved create-new-file dialog.
 * Added `minecraft:predicate` type (for mcFunction validation).

### Fixes
 * Reverted changes to resource location parsing.

## Version 0.2.1-alpha
### Fixes
 * Fixed crash in `clickableRangesForFilterArgs(...)` (#19).
 * Fixed crash in `getBestFAMatch(...)` (#20).

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