# Working with additional style files
If you have a lot of styles you might find it useful to break them up into categories. This functionality is available through the `Edit additional style files` checkbox. These additional style files are stored (as `.csv`) in `extensions/Styles-Editor/additonal_style_files`.

## Basic idea
Any style that is in an additional style file gets renamed to `filename::stylename`. So if you put a style `Picasso` into an additional style file `Artists`, it will now have the name `Artists::Picasso`. 

## Creating and removing additional style files
Tick the `Edit additional style files` box, then use `Create new additional style file` to create the categories you want. 

Alternatively, add the prefix `title::` to a style in the master view: the additional style file `title` will be created for you when you next tick the `Edit additional style files` box.

Empty additional style files are removed when you merge.

## Saving
`Merge into master` saves the contents of the additional style files into the master style file. If you don't merge, the changes will be retained in the additional style file, but not available for use.

## Moving styles to an additional style file
In the master view (`Edit additional style files` box unticked) styles are shown in the `filename::stylename` format. You can manually edit the style name to move it to an additional style file.


