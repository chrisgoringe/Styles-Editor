function refresh_style_list(x) {
    setTimeout( function() { 
        document.getElementById('refresh_txt2img_styles').click();
        document.getElementById('style_editor_load').click();
    }, 1000);
    return x;
}