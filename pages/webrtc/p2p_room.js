;(function(){



    for(var [key, value] of Object.entries({
            "P2PRoom": P2PRoom,
    })){
        window[key] = value;
    }
})();