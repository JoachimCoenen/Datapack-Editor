## Version 0.5.0-alpha
### Features 
 * Plugin support
   * Plugins can...:
     * add sidebars & bottombars (GUI).
     * define parser, stylers, & contextProviders for new languages.
     * add new contexts for existing languages.
     * add new schemas for existing & new languages.
     * add schema mappings (which schema to used for what file).
     * add custom document types (like `.json`, `.mcfunction`, or even `.png`).
     * add custom settings (aka. SettingsAspect).
     * add custom functionality to Projects (aka. ProjectAspect, mostly useful for file content indexing for custom languages or filetypes).
     * define custom indices for Roots (aka. IndexBundle).
     * customize what happens when a new project gets created (via.ProjectCreators).
 * Projects:
   * Multi-root Projects! Projects can have multiple subprojects (called Roots) now.
   * Project configuration is now stored inside the project folder as `.dpeproj`.
   * Directories can be excluded on a per-project basis.
 * Indentation & Whitespace:
   * Added indentation settings for documents.
   * Added whitespace visibility setting.
   * Added `globalStyles.whiteSpaceStyle` setting to color schemes.
 * Misc
   * Multiple Minecraft versions can be configured simultaneously.
 * JSON Schemas:
   * Added schema for loot tables (minecraft:loot_table)
   * Added schema for item modifiers (minecraft:item_modifier)

### Improvements
 * Improved layout of the Setup Dialog shown when the application is started for the first time.
 * New and improved dialog for opening existing and creating new projects.
 * Json schemas are now stored as Json files and can be viewed in the editor

### Fixes
 * Save As now selects correct file extension by default.
 * Saving an untitled file now correctly opens the Save As dialog instead of just saving the file to `untitled n`.
 * Fixed potential crashes when loading or saving files, settings, etc.
 * Fixed renamed files not being recognized correctly.
 * Fixed parsing of numbers in JSON files
 * Fixed crashes caused by the DocumentLexer.
 * Fixed syntax highlighting desyncing from actual text.
 * Fixed index mapping for escape sequences in JSON strings.


## Version 0.4.0-alpha
### Features
 * Added a dark theme, and support for custom themes.
 * Added file specific validation & suggestions for:
   * predicate files
   * recipe files
   * `pack.mcmeta`
   * `dependencies.json`
 * migrated to a project based structure:
   * dependencies are now specified using `dependencies.json` in the root directory of your datapack.
   * a common search location for dependencies can be changed in settings (default location is `C:/Users/<your username>/.dpe/dependencies`).

### Improvements
 * Improved parsing and validation performance for files with many errors
 * Drastically improved parsing and validation performance for json files in certain circumstances
 * Drag & drop files into the editor to open them


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