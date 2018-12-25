(function(){

    /**
    return "#abcdef";
    */
    var __h = 0;
    function randomColor(h=false,
            s = (0.99 + 0.0*Math.random()),
            v = (0.99 + 0.0*Math.random())){
       /*
https://martin.ankerl.com/2009/12/09/
how-to-create-random-colors-programmatically/

https://www.w3schools.com/colors/colors_wheels.asp

https://color.adobe.com/create/color-wheel/
       */
        /*
        if(!h){
            return ["#ff6770", "#a476e8", "#81d8ff", "#6ae881", "#fff000"][
                Math.floor(Math.random() * 6)
            ];
        }
        */
        
        if(!h){
            __h += 0.01;
            __h %= 1;
            h = __h;
            // h = (Math.random() + 0.6180339) % 1;
        }
        var h_i = Math.floor(h * 6);
        var f = h * 6 - h_i;
        var p = v * (1 - s);
        var q = v * (1 - f * s);
        var t = v * (1 - (1 - f) * s);
        // p is low, v is high, t is rising edge, q is falling edge
        var [r, g, b] = [
            [v, t, p], [q, v, p], [p, v, t],
            [p, q, v], [t, p, v], [v, p, q]
        ][h_i];
        
        // not work because of missing leading zero
        // return "#" +
        //         Math.floor(r * 255).toString(16) +
        //         Math.floor(g * 255).toString(16) +
        //         Math.floor(b * 255).toString(16);
        return "#" + ("00" + (
                Math.floor(r * 255) * 0x010000 +
                Math.floor(g * 255) * 0x000100 +
                Math.floor(b * 255) * 0x000001).toString(16)).slice(-6);
    }

    function loadScript(src, callback){
        var s = document.createElement("script");
        if(typeof callback === "function") s.onload = callback;
        s.innerHTML = src;
        document.body.appendChild(s);
    }
    function loadURLScript(url, callback){
        var s = document.createElement("script");
        if(typeof callback === "function") s.onload = callback;
        s.src = url;
        document.body.appendChild(s);
    }

    function removeElementFromArray(elem, arr){
        var index = arr.indexOf(elem);
        if(index >= 0){
            return arr.aplice(index, 1);
        }
    }

    function removeURLQuery(){
        var url = window.location.href.split("?")[0];
        window.history.replaceState({path: url}, "", url);
    }

    /*
    https://stackoverflow.com/questions/105034/
    create-guid-uuid-in-javascript#answer-2117523
    */
    function uuidv4(){
        return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>(
            c ^ crypto.getRandomValues(
                    new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
        );
    }

    /*
    window.addEventListener("beforeunload", function(e){

    });
    */

    for(var [key, value] of Object.entries({
        "randomColor": randomColor,
        "loadScript": loadScript,
        "loadURLScript": loadURLScript,
        "removeElementFromArray": removeElementFromArray,
        "removeURLQuery": removeURLQuery,
        "uuidv4": uuidv4,
    })){
        if(value !== undefined){
            window[key] = value;
        }
    }
})();