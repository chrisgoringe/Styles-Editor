# Recent changes

## 9 July 2023
- Allow backups to be downloaded

## 8 July 2023
- Fixed some bugs
- List existing backups to restore from

## 5 July 2023
- Changes under the covers to increase performance
- Automatically merge additional styles when moving to another tab

## 4 July 2023
- Move styles to new additional style file

## 3 July 2023
- Moved delete style functionality into an API call
- Ctrl-right-click to select multiple rows

## 1 July 2023
- Moved `create new additional style file` to the dropdown menu
- Removed `merge into master` - now it happens automatically when `Edit additional` is unchecked
- Fixed a crashing bug when a style had no name
- Added a subtle color shading to indicate filter and encryption are active even when closed
- Moved checkboxes to an `Advanced Options` accordian

## 30 June 2023
- Delete from master list removes from additional style file as well
- Major refactoring of code - sorry if I broke things, but it's going to be a lot easier going forward.

## 29 June 2023
- Layout tweaks and minor fixes

## 28 June 2023
- Allow linebreaks in styles (represented as `<br>` in editor)
- Restore from backups

## 22 June 2023
- Option to encrypt backups

## 21 June 2023
- Automatically create new Additional Style Files if needed
- Automatically delete empty Additional Style Files on merge
- Added notes column back in
- Fixed some minor bugs

## 20 June 2023
- Regular backups created in `extensions/Styles-Editor/backups` (saved every ten minutes if changes have been made, last 12 retained)
- Updated most of the documentation
- Removed `Renumber Sort Column` button (just switch tabs and switch back!)
- Removed `Extract from Master` button (automatically done when you go into additional style files view)

## 19 June 2023
- Right-click can be used to select a row in the table (a style)
- Delete the selected style by pressing `backspace`/`delete`