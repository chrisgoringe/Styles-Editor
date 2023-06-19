# Working with additional style files
If you have a lot of styles you might find it useful to break them up into categories. This functionality is available through the `Edit additional style files` checkbox. These additional style files are stored (as `.csv`) in `extensions/Styles-Editor/additonal_style_files`.

## Basic idea
Any style that is in an additional style file gets renamed to `filename::stylename`. So if you put a style `Picasso` into an additional style file `Artists`, it will now have the name `Artists::Picasso`. 

## Creating additional style files
Tick the `Edit additional style files` box, then use `Create new additional style file` to create the categories you want

## Working in an additional style file
With the `Edit additional style files` box ticked, select the style file you want to edit and use the editor as normal

## Saving
`Merge into master` saves the contents of the additional style files into the master style file

## Moving styles to an additional style file
In the master view (`Edit additional style files` box unticked) styles are shown in the `filename::stylename` format. You can manually edit the style name to move it to an **existing** additional style file. 

**Very important warning** - if you use additional style files, and manually rename a style into an additional style file that does not exist, it may well end up being deleted. Don't do it. [Issue 44](https://github.com/chrisgoringe/Styles-Editor/issues/44)

