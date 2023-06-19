# Style Editor

An extension for Automatic1111 to add a Style Editor, which allows you to view and edit saved styles in a spreadsheet-like format. 

See also:
- [Recent Changes](./changes.md "Recent Changes")
- [To Do](/todo.md "To Do")
- [Additional Style Files](/additional_style_files.md "Working with additional style files")

## Installation

In Automatic1111 you can add this extension through the extensions index.

Alternatively, paste the url `https://github.com/chrisgoringe/Styles-Editor` into the manual install URL box.

Or clone the repository into your extensions folder.

## Basic Usage

### Edit styles
Double-click in any of the boxes to get an edit cursor within the box.

### Search and replace
Enter a search term and a replace term and press the button...

### Cut, copy, paste
Click on a cell to select it, then use Ctrl-X, C and V.

### Delete styles
Right click on a style to select that row. Then hit `backspace` or `delete`. If you are using [additional style files](./additional_style_files.md) you need to delete the style in the additional style file, not the master style file.

### Add styles
Use the `New row` button, and then edit the boxes as you need. Note that if you have a filter applied the new row probably won't appear because it is empty, so best not to do that.

### Save styles
Styles are saved automatically. If you are using [additional style files](./additional_style_files.md) you need to use the merge files button.

### Filter view
Type into the filter text box to only show rows matching the text string. Matches from any of the columns. Filter can be set to Exact match, case insensitive, or regex.
If filtering by regex, if an invalid regex is entered it will be highlighted in red.

### Sorting
The `sort` column is automatically generated whenever you save or load. If you select `autosort` and the table will sort whenever you edit the `sort` value (as long as every value is numeric). 

### Backups
The master style file, and a zip of the additional style files directory, is backed up every ten minutes (with the most recent twelve backups retained) in `extensions/Styles-Editor/backups`