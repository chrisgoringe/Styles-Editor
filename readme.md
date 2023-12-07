# Style Editor

*Note that due to me moving across to ComfyUI this repository is no longer being maintained*

An extension for Automatic1111 to add a Style Editor, which allows you to view and edit saved styles in a spreadsheet-like format. 

See also:
- [Recent Changes](./changes.md "Recent Changes")
- [To Do](/todo.md "To Do")
- [Additional Style Files](/additional_style_files.md "Working with additional style files")

## Installation

In Automatic1111 you can add this extension through the extensions index.

Alternatively, paste the url `https://github.com/chrisgoringe/Styles-Editor` into the manual install URL box.

Or clone the repository into your extensions folder.

## Gradio
This extension requires `gradio 3.30` or above. Automatic1111 moved to this on May 19th 2023, so if you have updated since then you'll be fine.

If you get an error `AttributeError: 'Dataframe' object has no attribute 'input'`, then you are probably still running `gradio 3.29`. Check before raising an issue!

## Basic Usage

### Edit styles
Double-click in any of the boxes to get an edit cursor within the box.

### Search and replace
Enter a search term and a replace term and press the button...

### Cut, copy, paste
Click on a cell to select it, then use Ctrl-X, C and V.

### Delete styles
Right-click on a style to select that row. Then hit `backspace` or `delete`. You can select multiple rows by ctrl-clicking.

### Add styles
Use the `New row` button, and then edit the boxes as you need. Or select a row and press `D` to duplicate it.
Note that if you have a filter applied the new row probably won't appear because it is empty, so best not to do that.

### Duplicate style names
The editor will not allow styles to have the same name, so one or more 'x's will be appended to any duplicates.

### Save styles
Styles are saved automatically. 

### Filter view
Type into the filter text box to only show rows matching the text string. Matches from any of the columns. Filter can be set to Exact match, case insensitive, or regex.
If filtering by regex, if an invalid regex is entered it will be highlighted in red.

### Sorting
The `sort` column is automatically generated whenever you save or load. If you select `autosort` (under `Advanced`) the table will automatically sort whenever you change any `sort` value (as long as every `sort` value is numeric). 

### Notes 
You can put whatever you want in the notes column. 

### Encryption
Check the `Use encryption` box and all (subsequent) backups will be encrypted using the key you specify.
Encryption is done using [pyAesCrypt](https://pypi.org/project/pyAesCrypt/).

### Backups
The master style file is backed up every ten minutes (if changes have been made), with the most recent 24 backups retained. Backups are stored in `extensions/Styles-Editor/backups`.

To restore a backup, drag and drop the backup style file into the `restore from backup` box, or select one of the backups from the dropdown (the names are date_time in format `YYMMDD_HHMM`). If it is encrypted (`.aes`) then the encryption key in the `Encryption` section is used to decrypt.

To download a backup, select it from the dropdown then click the `download` link that appears in the upload/download box.

### Stargazers
Thanks to those who've starred this - knowing people value the extension makes it worth working on.
- 20 on 21 June 2023
- 31 on 6 July 2023
