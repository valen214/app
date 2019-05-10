
/* snippet
var obj = {};
Object.defineProperty(obj, "prop", {
value: "readonly",
writable: false,
});

// regex: /[ -~]+/

https://www.google.com.hk/search?ei=HCztW7CbC4zBoATW94eIBg&q=地城邂逅+同人+h
https://ck101.com/thread-3293610-1-1.html
https://7mm.tv/zh/hcomic_list/novellas/152.html

https://18h.animezilla.com/topic/%E5%9C%A8%E5%9C%B0%E4%B8%8B
%E5%9F%8E%E5%B0%8B%E6%B1%82%E9%82%82%E9%80%85%E6%98%AF%E5%90
%A6%E6%90%9E%E9%8C%AF%E4%BA%86%E4%BB%80%E9%BA%BC
https://18h.animezilla.com/manga/1586/3
https://18h.animezilla.com/manga/1559/2
https://18h.animezilla.com/manga/1119/7

https://18h.animezilla.com/topic/%E5%9C%A8%E5%9C%B0%E4%B8%8B%E5%9F%8E
%E5%B0%8B%E6%B1%82%E9%82%82%E9%80%85%E6%98%AF%E5%90%A6%E6%90%9E%E9%8C
%AF%E4%BA%86%E4%BB%80%E9%BA%BC
https://hugongck.wordpress.com/h%E6%BC%AB/
https://hugongck.wordpress.com/%E5%9C%A8%E5%9C%B0%E4%B8%8B%E5
%9F%8E%E5%B0%8B%E6%B1%82%E9%82%82%E9%80%85%E6%98%AF%E5%90%A6
%E6%90%9E%E9%8C%AF%E4%BA%86%E4%BB%80%E9%BA%BC%E7%A5%9E%E7%B9
%A9%E9%81%8A%E6%88%B2/
https://hugongck.wordpress.com/%E5%9C%A8%E5%9C%B0%E4%B8%8B
%E5%9F%8E%E5%B0%8B%E6%B1%82%E9%82%82%E9%80%85%E6%98%AF%E5
%90%A6%E6%90%9E%E9%8C%AF%E4%BA%86%E4%BB%80%E9%BA%BChappy-together-05-
%E3%83%98%E3%82%B9%E3%83%86%E3%82%A3/

*/

// window.requestAnimationFrame()

// top_nav, side_nav are elements IDs

// top_nav, side_nav are elements IDs
(function(){window.addEventListener("load", () =>{

// new Promise(resolve =>{
var positionStickySupport = function(){
    var el = document.createElement('a'), mStyle = el.style;
    mStyle.cssText = "position:sticky;" +
        "position:-webkit-sticky;position:-ms-sticky;";
    return mStyle.position.indexOf('sticky') !== -1;
}();

/*
var side_nav_anim_duration = 250;

var body_style = window.getComputedStyle(document.body);
var var_style = body_style.getPropertyValue("--side-nav-anim-duration");
document.body.style.setProperty(
        "--side-nav-anim-duration",
        side_nav_anim_duration / 100.0 + "s");
*/

function is_large_screen(){
    return window.matchMedia(
            "screen and (min-width: 768px)").matches;
}
function setDocVar(name, value){
    document.documentElement.style.setProperty(name, value);
}
function getDocVar(name){
    return String(window.getComputedStyle(
            document.documentElement).getPropertyValue(name)).trim();
}

function message(html){
    end_message.innerHTML = html;
    end_message.classList.remove("hide");
    setTimeout(() => {
            end_message.classList.add("hide");
    }, 1000);
}





// add getElementById if the namespace is polluted

function copyTextToClipboard(text){
    if(!copyTextToClipboard.elem){
        var elem = document.createElement("input");
        elem.type = "text";
        elem.id = "clipboard_text";
        Object.assign(elem.style, {
                "background": "transparent", "color": "transparent",
                "width": "1px", "height": "1px", "border": "none",
                "position": "fixed", "display": "block", "zIndex": "-1"});
        document.body.appendChild(elem);
        copyTextToClipboard.elem = elem;
    }
    copyTextToClipboard.elem.value = text;
    copyTextToClipboard.elem.select();
    // selectElement(copyTextToClipboard.elem);
    var suc = document.execCommand("Copy");
    console.log(suc, copyTextToClipboard.elem.value);
    message('"' + text + "\" copied to clipboard");
}
function selectElement(elem){
    var range;
    if(document.body.createTextRange){
        range = document.body.createTextRange();
        range.moveToElementText(element);
        range.select();
    } else if(window.getSelection){
        var select = window.getSelection();
        range = document.createRange();
        range.selectNodeContents(elem);
        select.removeAllRanges();
        select.addRange(range);
    }
}

/**
 * wheel event listener
 */
document.addEventListener("wheel", e => { // e.target
    // console.assert(e.deltaMode === e.DOM_DELTA_PIXEL,
    //        "WheelEvent.deltaMode is not 0 (px) but %d", e.deltaMode);
    var found = false; // redundant in this context
    var elem = e.target || e.srcElement;
    if(!found && (found = side_nav.contains(elem) || top_nav.contains(elem))){
        if(side_nav.contains(elem)){
            elem = side_nav;
        } else if(item_container.contains(elem)){
            elem = item_container;
        } else if(top_nav.contains(elem)){
            if(!elem.classList){
                elem = elem.parentElement;
            }
            if(elem.classList.contains("content")){
                elem = elem.parentElement;
            }
            elem = elem.classList.contains("content-list") ? elem : null;
        }
        
        if(elem){
            // prevent scroll bar in the upper layer gain focus and scroll
            if(elem.scrollTop + e.deltaY < 0){
                e.preventDefault();
                elem.scrollTop = 0;
            } else if(elem.scrollTop + e.deltaY >
                    elem.scrollHeight - elem.clientHeight){
                e.preventDefault();
                // it's actually larger than maximum
                elem.scrollTop = elem.scrollHeight;
            }
        }
    } else{
        /*
        if(document.body.scrollTop > top_nav.getBoundingClientRect().bottom){
            if(e.deltaY < 0){
                $("#main").css("margin-top", $("#top_nav").clientHeight + "px");
                $("#top_nav").addClass("fixed");
            }
        }
        */
    }
}, {
    passive: false
});

/**
 * click action handler
 */
// textarea with textContent or input with value
document.addEventListener("click", e =>{
    var elem = e.target || e.srcElement;
    var found = false; // reduce execution of .contains()
    // if template
    // if(!found && (found = target.contains(elem))){
    
    if(!found && (found = side_nav_btn.contains(elem))){
        side_nav.classList.toggle("fixed");
    } else if(!is_large_screen()){
        side_nav.classList.remove("fixed");
    }
    
    if(!found && (found = top_nav_lbl.contains(elem))){
        if(document.body.classList.contains("theme-rainbow")){
            document.body.classList.remove("theme-rainbow");
            document.body.classList.add("theme-blue");
        } else{
            document.body.classList.add("theme-rainbow");
            document.body.classList.remove("theme-blue");
        }
    }
    
    if(!found && (found = local_btn.contains(elem))){
        copyTextToClipboard(
                "file:///D:/workspace/main-custom-project/index.htm");
    } else if(!found && (found = webgl_btn.contains(elem))){
        copyTextToClipboard(
                "file:///D:/workspace/main-custom-project/pages/webgl/webgl.htm");
    }
    
    if(!found && (found = more_btn.contains(elem))){
        var show = item_container.classList.toggle("show");
        more_btn.innerHTML = show ? "&#708;" : "&#709;";
    } else if(!item_container.contains(elem) &&
            item_container.classList.contains("show")){
        more_btn.innerHTML = "&#709;";
        item_container.classList.remove("show");
    }
});




/*
top_nav_css_top: small screen only
top_nav_scroll_buffer: hide top_nav when scrolling lower (small screen only)
*/
var last_scroll_top = 0, last_large_screen = "HEH",
        top_nav_css_top = 0,
        top_nav_scroll_buffer = 256,
        content_scroll_buffer = parseInt(
                getDocVar("--content_scroll_buffer")),
        side_nav_height_refreshed = false;

document.body.style.height = banner.clientHeight +
        top_nav.clientHeight + main.clientHeight +
        (is_large_screen() ? content_scroll_buffer : 0) + "px";
top_nav.style.top = 0;

// document.body.style.height = 0;
// elem.getClientRects()[]
for(var i in top_nav.childNodes){
    if(top_nav.childNodes[i].nodeType === 1){
        top_nav.childNodes[i].top_nav_width =
                top_nav.childNodes[i].getBoundingClientRect().width;
    }
}

var running = false; // extremely important
function layout_refresh(e){ // trigger when scroll and resize
    if(running){ return; }
    running = true;
    var scroll_top = (window.pageYOffset ||
            window.scrollY || document.body.scrollTop);
    var scroll_over_banner = scroll_top -
                    banner.offsetTop - banner.clientHeight;
    var large_screen = is_large_screen();
    var top_nav_height = top_nav.getBoundingClientRect().height;
    
    /**
     * RESIZE
     */
    if(e && e.type == "resize"){
        if(top_nav.getBoundingClientRect().height >
                parseInt(getDocVar("--top_nav-height").slice(0, -2))){
            var last = top_nav.lastElementChild;
            var count = 0;
            while(++count < 25 && last && top_nav_height > 120){
                // last instanceof HTMLElement
                if(last.classList && last.classList.contains("top_nav_item")){
                    item_container.insertBefore(last,
                            item_container.firstElementChild);
                    last = top_nav.lastElementChild;
                } else{
                    last = last.previousSibling;
                }
                top_nav_height = top_nav.getBoundingClientRect().height;
            }
        } else if(item_container.firstElementChild){
            var rightmost_elem = top_nav.lastElementChild === item_container ?
                    home_btn : top_nav.lastElementChild;
            var empty_space = more_btn.getBoundingClientRect().left -
                        rightmost_elem.getBoundingClientRect().right;
            var elem = item_container.firstElementChild;
            // suppose to be 16, same as padding on top_nav
            while(elem && (empty_space > elem.top_nav_width + 32)){
                top_nav.appendChild(elem);
                empty_space -= 16 + elem.top_nav_width;
                elem = item_container.firstElementChild;
            }
        }
        // setDocVar("--top_nav-height", top_nav_height + "px");
    }
    
    
    /**
     * SIDE_NAV, TOP_NAV and MAIN
     */
    if(scroll_over_banner < 0 || large_screen !== last_large_screen){
        if(scroll_over_banner > 0){
            document.body.style.height = banner.clientHeight +
                    top_nav_height + main.clientHeight +
                    (large_screen ? content_scroll_buffer : 0) + "px";
        }
        // main.classList.remove("fixed");
        top_nav.style.top = 0;
        side_nav_height_refreshed = false;
        
        if(large_screen !== last_large_screen){
            side_nav.classList.add("no_anim");
            side_nav.classList.remove("fixed");
            setTimeout(() =>{side_nav.classList.remove("no_anim");}, 30);
        }
    }
    
    if(scroll_over_banner > 0){
        if(large_screen){
            side_nav.classList.add("fixed");
            
            if(scroll_over_banner < content_scroll_buffer){
                main.classList.add("fixed");
            }
        
        
        } else{ // small screen
            if(scroll_over_banner < top_nav_scroll_buffer){
                top_nav_css_top = 0;
            } else{
                var deltaY = scroll_top - last_scroll_top;
                console.assert(top_nav_height === 80);
                top_nav_css_top -= deltaY;
                if(deltaY > 0){
                    top_nav_css_top = Math.max(
                            -top_nav_height, top_nav_css_top);
                    if(item_container.classList.contains("show")){
                        more_btn.innerHTML = "&#709;";
                        item_container.classList.remove("show");
                    }
                } else{
                    top_nav_css_top = Math.min(0, top_nav_css_top);
                } // considering one line ternery if
            }
            top_nav.style.top = top_nav_css_top + "px";
        }
    }
    
    // it will keep refreshing side_nav height
    // there's a flaw in switching screen size
    if(!side_nav_height_refreshed){
        // window.innerHeight includes scroll bar
        side_nav.style.height = document.documentElement.clientHeight -
        (large_screen ? top_nav.getBoundingClientRect().bottom : 0) + "px";
    }
    side_nav_height_refreshed = scroll_over_banner > 0;
    
    last_scroll_top = scroll_top;
    last_large_screen = large_screen;
    
    running = false;
}


document.addEventListener("scroll", layout_refresh, {
    passive: false
});
/****/
window.addEventListener("resize", layout_refresh);
/*/
var resize_timer;
window.addEventListener("resize", e =>{
    clearTimeout(resize_timer);
    resize_timer = setTimeout(layout_refresh, 33, e);
});
/*****/
document.getElementById("loading_cover").style.display = "none";
layout_refresh({type: "resize"});


});})();




