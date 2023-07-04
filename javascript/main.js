function api_post(path, payload, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", path, true);
    xhr.onload = function() { callback(JSON.parse(xhr.responseText)); };
    xhr.setRequestHeader("Content-type", "application/json");
    xhr.send(JSON.stringify(payload));
}

function when_loaded() {
    api_post("/style-editor/check-api/", {}, function(x) { console.log( "Style Editor Check API", x['value'] )});
    globalThis.selectedRows = [];
    grid = document.getElementById('style_editor_grid');
    grid.addEventListener('keydown', function(event){
        // if a key is pressed in a TD which has an INPUT child, or an INPUT, this is typing in a cell, allow it
        if (event.target.tagName === 'TD' && event.target.querySelector("input")) { return; }
        if (event.target.tagName === 'INPUT') { return; }
        
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

        // if M is pressed, move the selected styles
        if (event.key === "m" && globalThis.selectedRows.length > 0) {
            new_prefix = prompt("Move to style file:", "");
            if (new_prefix != null) { 
                globalThis.selectedRows.forEach( function(row) { 
                    api_post("/style-editor/move-style", 
                            {"style":{"value":row_style_name(row)}, "new_prefix":{"value":new_prefix}}, 
                            function(x){} );    
                });
                document.getElementById("style_editor_handle_api").click();
                unselect_rows();
            }
        }

        // if backspace or delete are pressed, delete selected rows
        if (event.key === "Backspace" || event.key === "Delete") { 
            globalThis.selectedRows.forEach( function(row) { 
                api_post("/style-editor/delete-style", 
                        {"value":row_style_name(row)}, 
                        function(x){} );    
            });
            document.getElementById("style_editor_handle_api").click();
            globalThis.selectedRows = [];
        } 

        // if we get to here, stop the keypress from propogating
        event.stopImmediatePropagation(); 
    }, { capture: true });

    grid.addEventListener('contextmenu', function(event){
        if(event.shiftKey) { return; }
        if(!event.ctrlKey) { unselect_rows(); }
        row = event.target.closest("tr");
        if (row) { select_row(row); event.stopImmediatePropagation(); event.preventDefault(); }  
    }, { capture: true });

    grid.addEventListener('click', function(event){
        unselect_rows()
    }, { capture: true });
}

function row_style_name(row) {
    return row.querySelectorAll("td")[1].querySelector("span").textContent;
}

function select_row(row) {
    globalThis.selectedRows.push(row);
    row.style.backgroundColor = "#840";
}

function unselect_rows() {
    globalThis.selectedRows.forEach( function(row){ row.style.backgroundColor = '';  })
    globalThis.selectedRows = []
}

function press_refresh_button(tab) {
    b = document.getElementById("refresh_txt2img_styles");
    if (b) {b.click()}
    b = document.getElementById("refresh_img2img_styles");
    if (b) {b.click()}
}

function update(target, text) { 
    // Update the cell in such a way as to get the backend to notice...
    // - generate a double click on the original target
    // - wait 10ms to make sure it has happened, then:
    //   - paste the text into the input that has been created
    //   - send a 'return' keydown event through the input
    const dblclk = new MouseEvent("dblclick", {"bubbles":true, "cancelable":true});
    target.dispatchEvent(dblclk);
    setTimeout( function() {
        const the_input = target.querySelector('input');
        the_input.value = text;
        const rtrn = new KeyboardEvent( "keydown", {
            'key': 'Enter', 'target': the_input,
            'view': window, 'bubbles': true, 'cancelable': true            
        });
        the_input.dispatchEvent(rtrn);
    }, 10);
}

function encryption_change(value) {
    accordian_style = document.getElementById('style_editor_encryption_accordian').style;
    if (value) {
        accordian_style.color = "#f88";
    } else {
        accordian_style.color = "white";
    }
    return value
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
    accordian_style = document.getElementById('style_editor_filter_accordian').style;
    if (filter_text==="") {
        accordian_style.color = "white";
    } else {
        accordian_style.color = "#f88";
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
    return [filter_text, type]
}

function style_file_selection_change(x,y) {
    if (x==='--Create New--') {
        return [new_style_file_dialog(''),'']
    }
    return [x,'']
}

function new_style_file_dialog(x) {
    let filename = prompt("New style filename", "");
    if (filename == null) { filename = "" }
    return filename;
}
