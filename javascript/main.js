function refresh_style_list(x) {
    setTimeout( function() { 
        document.getElementById('refresh_txt2img_styles').click();
        document.getElementById('refresh_img2img_styles').click();
        document.getElementById('style_editor_load').click();
    }, 1000);
    return x;
}

function filter_style_list() {
    filter_text = document.getElementById('style_editor_filter').firstElementChild.lastElementChild.value;
    rows = document.getElementById('style_editor_grid').querySelectorAll("tr");
    header = true;
    for (row of rows) {
        vis = false;
        for (cell of row.querySelectorAll("span")) {
            if (cell.textContent.includes(filter_text)) { vis = true; }
        }
        if (vis || header) { row.style.display = '' } else { row.style.display='none' }
        header = false;
    }
}