function when_loaded() {
    document.getElementById('style_editor_grid').addEventListener('keydown', function(event){
        if (event.ctrlKey === true) {
            event.stopImmediatePropagation();
            span = event.target.querySelector("span");
            if (event.key === 'c') {
                navigator.clipboard.writeText(span.textContent);
            }
            if (event.key === 'x') {
                navigator.clipboard.writeText(span.textContent);
                update(event.target, "");
            }
            if (event.key === 'v') {
                navigator.clipboard.readText().then((clipText) => (update(event.target,clipText)));
            }
        }
        if (event.target.tagName === 'TD') { // if a cell from the editor got a keydown
            if (event.target.querySelector("input")) { 
                return; // if it has an active 'INPUT' child, ok
            } else if (event.key === "Backspace" || event.key === "Delete") { 
                return; // we can delete
            } else {
                event.stopImmediatePropagation(); // otherwise stop right there
            }
        }
    }, { capture: true });
}

function update(target, text) { 
    // Update the cell in such a way as to get the backend to notice...
    // - generate a double click on the original target
    // - wait 10ms to make sure it has happened, then:
    //   - paste the text into the input that has been created
    //   - send a 'return' keydown event through the input
    const dblclk = new MouseEvent("dblclick");
    target.dispatchEvent(dblclk);
    setTimeout( function() {
        const the_input = target.querySelector('input');
        the_input.val(text);
        const rtrn = jQuery.Event("keydown", {
            'key':'Enter', 'target':the_input,
            'view': window, 'bubbles': true, 'cancelable': true            
        });
        the_input.trigger(rtrn);
    }, 10);
}

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
    let filename = prompt("New style filename", "");
    if (filename == null) { filename = "" }
    return filename;
}
