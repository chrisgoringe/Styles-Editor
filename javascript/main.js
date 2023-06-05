function refresh_style_list(x) {
    setTimeout( function() { 
        document.getElementById('refresh_txt2img_styles').click();
        document.getElementById('refresh_img2img_styles').click();
        document.getElementById('style_editor_load').click();
    }, 1000);
    return x;
}

function filter_style_list(filter_text, type) {
    if (type=="regex") { 
        filter = document.getElementById('style_editor_filter').firstElementChild.lastElementChild;
        try {
            re = new RegExp(filter_text);
            filter.style.color="white";
        } 
        catch (error) { 
            re = new RegExp();
            filter.style.color="red";
        } 
    }
    rows = document.getElementById('style_editor_grid').querySelectorAll("tr");
    header = true;
    for (row of rows) {
        vis = false;
        for (cell of row.querySelectorAll("span")) {
            if ( (type=="Exact match" && cell.textContent.includes(filter_text)) ||
                 (type=="Case insensitive" && cell.textContent.toLowerCase().includes(filter_text.toLowerCase())) ||
                 (type=="regex" && cell.textContent.match(re)) )
                { vis = true; };
        }
        if (vis || header) { row.style.display = '' } else { row.style.display='none' }
        header = false;
    }
    return (filter_text, type);
}

function new_style_file_dialog(x) {
    let filename = prompt("New style filename (without extension)", "");
    if (filename == null) { filename = "" }
    return filename;
}
