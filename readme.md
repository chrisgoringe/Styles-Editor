# Style Editor

An extension for Automatic1111 to add a Style Editor, which allows you to view and edit saved styles in a spreadsheet-like format. 

## Installation

Put the repository `https://github.com/chrisgoringe/Styles-Editor` in your extensions folder and restart the UI.

Or paste that URL into the manual install box.

## Usage

### Load and view styles
Click on the `Style Editor` tab. If you need to reload the styles for any reason,  click `Reload Styles`.

### Edit styles
Click on any box and it will be highlighted. You can then type and it will replace what was there.
Double-click in any of the boxes to get an edit cursor within the box.

### Search and replace
Enter a search term and a replace term and press the button...

### Cut, copy, paste
Ctrl-X, C and V all work as you might expect them to.

### Delete styles
A style with no name won't be saved. So delete the name (click on the name to highlight the box and hit 'backspace') and then when you save (which happens automatically in the background) the style will be removed. To check, you can use the 'Reload syles' button.

### Add styles
Use the `New row` button, and then edit the boxes as you need. Note that if you have a filter applied (see below) the new row probably won't appear because it is empty!

### Save styles
The `Save Styles` button will save the styles, and refresh the styles dropdown menus.

### Add notes
You can use the notes column for any notes you want to make.

### Filter view
Type into the filter text box to only show rows matching the text string. Matches from any of the columns. Filter can be set to Exact match, case insensitive, or regex.
If filtering by regex, if an invalid regex is entered it will be highlighted in red.

### Sorting
The "index" column is automatically generated whenever you save or load. If you edit the value, you can then sort the list by index (using the arrow in the header). 

### Working with additional style files
If you have a lot of styles you might want to break them up into smaller files. See the instructions in the UI.

## To Do (definitely)
- some sort of backup mechanism
- automatically merge changes into master (so editing subfiles is just a view on the master)

## To Do (maybe)
- duplicate style (duplicate a row in the table)
- swap between multiple style files
- add style from txt2img or img2img prompts
- copy selected styles between tabs not just prompt (not really this extension, but a pain)
- refresh style lists in UI


