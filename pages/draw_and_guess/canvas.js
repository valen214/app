/* jshint -W069 */
/* jshint -W014 */
/* jshint sub:true */

(function(){
    
    class CanvasEvent
    {
        static get STROKE_START(){ return "strokestart"; }
        static get STROKE_UPDATE(){ return "strokeupdate"; }
        static get STROKE_END(){ return "strokeend"; }

        static get UNDO(){ return "undo"; }
        static get REDO(){ return "redo"; }

        constructor(event, action){
            switch(event){
            case CanvasEvent.STROKE_START:
            case CanvasEvent.STROKE_UPDATE:
            case CanvasEvent.STROKE_END:
                break;
            default:
                throw new Error("invalid event for CanvasEvent");
            }
            if(!action){
                throw new Error("invalid canvas action");
            }
            
        }
    }

    // CanvasEvent unused
    class CanvasAction
    {
        static get TYPE(){ return "action"; }

        constructor(canvas){
            if(!(canvas instanceof CustomCanvas)){
                throw new Error("invalid canvas");
            }

            /*
            use Object.defineProperty(this, "key", {description})
            to hide it from JSON.stringify
            */
            Object.defineProperty(this, "canvas", {
                get(){ return canvas; }
            });
        }
        get type(){ return this.TYPE; }
    }
    class CanvasClear extends CanvasAction
    {
        constructor(canvas){
            super(canvas);
        }
    }
    class CanvasUndo extends CanvasAction
    {

    }
    class CanvasRedo extends CanvasAction
    {

    }
    class CanvasStroke extends CanvasAction
    {
        static get TYPE(){ return "stroke"; }

        constructor(canvas, {
                strokeStyle = "#aaf",
                lineWidth = 5,
                lineJoin = "round",
        } = {}){
            super(canvas);
            this.points = [];
            this.strokeStyle = strokeStyle;
            this.lineWidth = lineWidth;
            this.lineJoin = lineJoin;
            this.globalCompositeOperation = "source-over";
        }

        add(x, y, silence){
            const __c = this.canvas;
            if(x != undefined && y != undefined){ // null == undefined
                this.points.push({x: x, y: y});
                if(__c && !silence){
                    __c.dispatch("strokeupdate", this);
                }
            }
            return this;
        }
    }


    /**
     * listeners related functions: on, do, dispatch
     * do(action) would create a new CanvasAction(this, ...)
     * which would likely to dispatch a "create" event
     * other event would be dispatch from CanvasAction
     */
    class CustomCanvas
    {
        constructor(c){
            if(typeof c == "string"){
                c = document.getElementById(c);
            }
            if(!c){
                c = new HTMLCanvasElement();
            }
            this.canvas = c;
            this.actions = [];
            this.drawing = false;
            this.listeners = Object.freeze({
                "pointerdown": [],
                "pointermove": [],
                "pointerup": [],
                [CanvasEvent.STROKE_START]: [],
                [CanvasEvent.STROKE_UPDATE]: [],
                [CanvasEvent.STROKE_END]: [],
                "clear": [],
            });


            this.resize();
        }

        resize(){
            const c = this.canvas;
            var rect = c.getBoundingClientRect();
            console.log("checking canvas dimension");
            if(c.width != rect.width
            || c.height != rect.height){
                c.width = rect.width;
                c.height = rect.height;
                console.log(`canvas resize: ${c.width} ${c.height}`);
                this.redraw();
            }
        }


        on(event, listener){
            if(typeof listener === "function"){
                (this.listeners[event] || []).push(listener.bind(this));
            }
            return this;
        }
        do(action, option){
            var return_value = "WHAT";
            switch(action){
            case "stroke":
                action = new CanvasStroke(this, option);
                this.actions.push(action);
                this.dispatch("strokestart", action);

                return_value = action;
                break;
            case "clear":
                action = new CanvasClear(this);
                this.actions.push(action);
                return_value = action;
                break;
            default:
                throw new Error("canvas action unsupported");
            }
            console.log(return_value);
            return return_value;
        }
        dispatch(event, action){
            switch(event){
            case "strokestart":
            case "strokeupdate":
            case "strokeend":
            case "clear":
                if(!( action instanceof CanvasAction )){
                    throw new Error("invalid action dispatching");
                }
                for(var l of (this.listeners)[event]){
                    l(action, event);
                }
                /*
                let iter = this.listeners[Symbol.iterator]();
                let func = resolve => {
                    let l = iter.next();
                    if(!l.done){
                        l(action, event);
                        // resolve();
                        return new Promise(func);
                    }
                };
                */

                break;
            default:
                throw new Error("invalid event dispatching");
            }
        }

        redraw(){
            throw new Error("not implemented");
        }


        register_handlers(){
            const cnv = this.canvas;
            const ctx = this.context;
            const __this = this;

            var last_action = null; // potential error on multithread

            function set_touchevent_offset(e){
                console.assert(e instanceof TouchEvent);
                var rect = cnv.getBoundingClientRect();
                var t = (e.touches || e.targetTouches || e.changedTouches);
                t = t[0];
                e.offsetX = t.clientX - rect.left;
                e.offsetY = t.clientY - rect.top;
            }

            function pointer_down(e){
                __this.drawing = true;
                if(e instanceof TouchEvent){
                    set_touchevent_offset(e);
                }
                last_action = __this.do("stroke", randomColor(), 5
                        ).add(e.offsetX, e.offsetY);
                
            }
            function pointer_move(e){
                if(__this.drawing){
                    if(e instanceof TouchEvent){
                        set_touchevent_offset(e);
                    }
                    last_action.add(e.offsetX, e.offsetY);
                }
            }
            function pointer_up(e){
                __this.drawing = false;
            }


            var resizing = false;
            var resizeTimer;
            function resize_action(){
                __this.resize();
                __this.redraw();
                resizing = false;
            }
            function resize_listener(){
                if(resizing) return;
                resizing = true;
                clearTimeout(resizeTimer);
                resizeTimer = setTimeout(resize_action, 0);
            }
            window.addEventListener("resize", resize_listener);
            
            // pointer events?
            function resize_on_first_shown(){
                console.log("main canvas loaded");
                __this.resize();

                cnv.removeEventListener("mouseenter", resize_on_first_shown);
                cnv.removeEventListener("touchstart", resize_on_first_shown);
            }
            cnv.addEventListener("mouseenter", resize_on_first_shown);
            cnv.addEventListener("touchstart", resize_on_first_shown);

            cnv.addEventListener("touchstart", pointer_down);
            cnv.addEventListener("touchmove", pointer_move, 0);
            cnv.addEventListener("touchend", pointer_up);
            cnv.addEventListener("touchcancel", pointer_up);
            
            cnv.addEventListener("mousedown", pointer_down);
            cnv.addEventListener("mousemove", pointer_move, 0);
            cnv.addEventListener("mouseup", pointer_up);
            cnv.addEventListener("mouseout", pointer_up);

            return this;
        }
    }

    class CustomAnimatedCanvas extends CustomCanvas
    {
        constructor(c){
            super(c);
            this.context = this.canvas.getContext("2d");
            this.rendered_actions = 0;
            this.rendered_points = 0;
        }

        render(){
            const __c = this.canvas;
            const ctx = this.context;
            const ac_list = this.actions;

            const cw = __c.width;
            const ch = __c.height;

            while(this.rendered_actions < ac_list.length){
                var action = ac_list[this.rendered_actions];
                switch(action.constructor){
                case CanvasStroke:
                    var count = this.rendered_points;
                    while(count < action.points.length){
                        var pt = action.points[count];
                        if(pt.x > 1 || pt.y > 1){
                            pt.x = pt.x / cw;
                            pt.y = pt.y / ch;
                        }
                        var x = pt.x * cw;
                        var y = pt.y * ch;
                        if(count == 0){
                            ctx.strokeStyle = action.strokeStyle;
                            ctx.lineJoin = action.lineJoin;
                            ctx.lineWidth = action.lineWidth;
                            ctx.globalCompositeOperation =
                                    action.globalCompositeOperation;
    
                            // create dot on click
                            ctx.beginPath();
                            ctx.moveTo(x, y);
                            ctx.lineTo(x+0.1, y+0.1);
                            ctx.closePath();
                            ctx.stroke();
    
                            // begin line
                            ctx.beginPath();
                            ctx.moveTo(x, y);
                        } else{
                            ctx.lineTo(x, y);
                        }
                        ++count;
                    }
                    ctx.stroke();

                    this.rendered_points = count;
                    this.dispatch("strokeend", action);
                    break;
                case CanvasClear:
                    ctx.clearRect(0, 0, __c.width, __c.height);

                    this.dispatch("clear", action);
                    break;
                }

                if(this.rendered_actions + 1 == ac_list.length){
                    break;
                } else{
                    this.rendered_actions += 1;
                    this.rendered_points = 0;
                }
            }

            this.requestID = requestAnimationFrame(this.render.bind(this));
        }


        do(action, ...args){
            var return_value;
            switch(action){
            case "redraw":
                this.rendered_points = 0;
                this.rendered_actions = 0;
                return_value = this;
                break;
            default:
                return_value = super.do(action, ...args);
            }
            return return_value;
        }


        start(){
            this.requestID = requestAnimationFrame(this.render.bind(this));
        }
        stop(){
            cancelAnimationFrame(this.requestID);
        }

        redraw(){
            this.rendered_actions = 0;
            this.rendered_points = 0;
            return this;
        }
    }

    class CustomEventCanvas extends CustomCanvas
    {
        constructor(c){
            super(c);

        }
    }


    class CustomWebGLCanvas extends CustomCanvas
    {
        constructor(c){
            super(c);

        }
    }


    
    for(var [key, value] of Object.entries({
        "CanvasAction": CanvasAction,
            "CanvasStroke": CanvasStroke,
            "CanvasClear": CanvasClear,
        "CanvasEvent": CanvasEvent,
        "CustomCanvas": CustomCanvas,
            "CustomAnimatedCanvas": CustomAnimatedCanvas,
    })){
        if(value !== undefined){
            window[key] = value;
        }
    }
})();