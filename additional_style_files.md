# Working with additional style files
If you have a lot of styles you might find it useful to break them up into categories. This functionality is available through the `Edit additional style files` checkbox (under `Advanced`). These additional style files are stored (as `.csv`) in `extensions/Styles-Editor/additonal_style_files`.

## Basic idea
Any style that is in an additional style file gets renamed to `filename::stylename`. So if you put a style `Picasso` into an additional style file `Artists`, it will now have the name `Artists::Picasso`. 

## Creating and removing additional style files
Tick the `Edit additional style files` box, then use `--Create New--` in the dropdown menu to create the categories you want. If there are no additional style files when you tick the box, you will automatically be prompted to create one.

Alternatively, add the prefix `title::` to a style in the master view: the additional style file `title` will be created for you when you next tick the `Edit additional style files` box.

Empty additional style files are removed when you uncheck the `Edit additional style files` box.

## Saving
The additional style files are autosaved as you edit. They are merged into the master style file when you uncheck the `Edit additional style files` box.

## Moving styles to or between an additional style file
Select style or styles (with right click) then press `M` and enter the new prefix.

