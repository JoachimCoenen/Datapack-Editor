

# Minecraft Datapack-Editor
![GitHub](https://img.shields.io/github/license/JoachimCoenen/Datapack-Editor)
![GitHub repo size](https://img.shields.io/github/repo-size/JoachimCoenen/Datapack-Editor?color=0072FF)
![Lines of code](https://img.shields.io/tokei/lines/github/JoachimCoenen/Datapack-Editor?color=0072FF)
[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2FJoachimCoenen%2FDatapack-Editor&count_bg=%230072FF&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false)](https://hits.seeyoufarm.com)
![GitHub all releases](https://img.shields.io/github/downloads/JoachimCoenen/Datapack-Editor/total?color=0072FF)

<br />
<p align="center">
  <img src="icon/icon.png" width="150" >
</p>
An advanced creator & editor for Minecraft Datapacks for Minecraft 1.20.2 - 1.20.4+ (datapack version 18-23+).


![MainWindow1_IMG][MainWindow1_IMG]


## Features
- Code Editing
  - Syntax highlighting 
  - Error checking
  - Rich code suggestions and code completion for `.mcFunction` and `.json` files
  - Add, rename and delete files and folders via the left-side tree view
- Project
  - Open or create a new datapack project
  - Validate all files (for `.mcFunction` and `.json` files) within a project
  - Multi-root projects
  - supports dependencies between datapacks / projects via `dependencies.json`
- Customization
  - custom themes
  - plugin support
- Navigation:
  - Ctrl-Click to follow symbols (functions & function tags, block tags, ... )
  - Multi-tab & multi-view editor
  - Quickly find and open files with `Ctrl`+`P`
  - Search in all files


## Keyboard Shortcuts

| Action                     | Shortcut           |
|----------------------------|--------------------|
| Find in all files          | `Ctrl`+`Shift`+`F` |
| Quickly find & open a file | `Ctrl`+`P`         |
| New (scratch) file         | `Ctrl`+`N`         |
| Save current file          | `Ctrl`+`S`         |
| Save as                    | `Ctrl`+`Shift`+`S` |

| Action                   | Shortcut       |
|--------------------------|----------------|
| Duplicate line           | `Ctrl`+`D`     |
| Find in current document | `Ctrl`+`F`     |
| Trigger code suggestions | `Ctrl`+`Space` |
| Show call tips           | `Ctrl`+`K`     |


## Download & Install


[Current Version][DownloadLatest_LINK] <--  
[Other Versions][Releases_LINK]

Download the zip file, extract it to an empty folder and run the `start.cmd` file.

If you have any questions, problems or suggestions, feel free to create an [Issue][NewIssue_LINK]. 

## Screenshots 
<table style="width:100%;border-spacing:0px">
  <tr style="padding:0px">
    <td style="padding:0px"><table style="width:100%;border-spacing:0px">
      <tr style="padding:0px">
        <td style="padding:0px"> <img src="screenshots/mainWindow.png" alt="Main Window" style="width:width;height:height;"> </td>
        <td style="padding:0px"> <img src="screenshots/quickFind.png" alt="Quickly find and open a file" style="width:width;height:height;"> </td>
      </tr>
    </table></td>
  </tr>
  <tr style="padding:0px">
    <td style="padding:0px"><table style="width:100%;border-spacing:0px">
      <tr style="padding:0px">
        <td style="padding:0px"> <img src="screenshots/createNewProject.png" alt="Search Dialog" style="width:width;height:height;"> </td>
        <td style="padding:0px"> <img src="screenshots/search.png" alt="Search Dialog" style="width:width;height:height;"> </td>
        <td style="padding:0px"> <img src="screenshots/validateFiles.png" alt="Validate File" style="width:width;height:height;"> </td>
      </tr>
    </table></td>
  </tr>
</table>


## Disclaimer
Some contents in the program are from the Minecraft Wiki (see [Minecraft Wiki:General disclaimer][MCWikiGeneralDisclaimer_LINK]).
This program is not affiliated with Mojang Studios.




[MainWindow1_IMG]:    screenshots/mainWindow.png    "Main Window"
[QuickFind_IMG]:      screenshots/quickFind.png     "Quick Find"
[NewProject_IMG]:     screenshots/createNewProject.png     "Create New Project Dialog"
[Search_IMG]:         screenshots/search.png        "Search Dialog"
[ValidateFiles_IMG]:  screenshots/validateFiles.png "Validate File"

[MCWikiGeneralDisclaimer_LINK]:  https://minecraft.wiki/w/Minecraft_Wiki:General_disclaimer "Minecraft Wiki:General disclaimer"

[Releases_LINK]:                 https://github.com/JoachimCoenen/Datapack-Editor/releases "Datapack-Editor/releases"
[DownloadLatest_LINK]:           https://github.com/JoachimCoenen/Datapack-Editor/releases/latest  "latest"
[NewIssue_LINK]:                 https://github.com/JoachimCoenen/Datapack-Editor/issues/new  "New issue"

