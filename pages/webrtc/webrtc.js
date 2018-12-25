/* jshint -W069 */
/* jshint -W093 */

/** 
###########################################################################
TEST CODE
###########################################################################
    


function loadURLScript(url, callback){
    var s = document.createElement("script");
    if(typeof callback === "function") s.onload = callback;
    s.src = url;
    document.body.appendChild(s);
}
var HOST_NAME = "ec2-18-222-252-221.us-east-2.compute.amazonaws.com"
loadURLScript(`http://${HOST_NAME}:8129/webrtc/webrtc.js`);
new Promise(resolve => setTimeout(resolve, 1000
)).then(() => new Promise(resolve => {
    window["p"] = new Peer();
    p.on("connection", function(pc){
        pc.on("open", function(_pc){
            __console.assert(pc === _pc);
            pc.on("message", console.log);
            window["send"] = pc.send.bind(pc);
        })
    });
    setTimeout(resolve, 500);
})).then(() => {
    console.log(p.uuid);
})

function connect(uuid){
    var pc = p.connect(uuid);
    pc.on("open", function(_pc){
        __console.assert(_pc === pc);
        pc.on("message", function(data){
            console.log(data);
        });
        window["send"] = pc.send.bind(pc);
    });
}

###########################################################################

https://www.pkc.io/blog/untangling-the-webrtc-flow/#initialization-phase

*/

/*
 thread: main
 |
 var p = new Peer()
 connect to socket server 
 |-thread: server
 | |
 var pc = p.connect(remote uuid)
 |---thread: offer exchange
 | | |
 | | join thread: server 
 p.on("open", callback_open)
 | server send back uuid & set identifier
 | . create data channel
 | . |-thread: data channel open
 | . | |
 | . create offer
 | . |---thread: offer exchange
 | . | | |
 |
 |
 |
 |
 |
 |
 |
 |
 |




https://jscompress.com/

*/

(function(){
    // const __console__ = console;
    var __console = {
        log: console.log,
        info: console.info,
        warn: console.warn,
        error: console.error,
        assert: console.assert,
    };

    var PORT = "<? PORT ?>";
    var HOST_NAME = "<? HOST_NAME ?>";
    if(!parseInt(PORT)){
        __console.error("probably whole script not working");
        PORT = 8080;
    }
    if(HOST_NAME.startsWith("<")){
        HOST_NAME = "ec2-18-222-252-221.us-east-2.compute.amazonaws.com";
    }

    const SOCKET_SERVER_ADDRESS = "ws://" + HOST_NAME + ":" + PORT;
    const RTC_PEER_CONFIGURATION = {
        "iceServers": [
            {"urls": "stun:stun.l.google.com:19302"},
            {"urls": "stun:stun.stunprotocol.org:3478"},
        ]
    };

    function catch_error(...args){
        __console.error(...args);
    }

    class PeerConnection
    {
        constructor(local_peer, remote_uuid, conn, isOfferer){
            this.local_peer = local_peer;
            this.remote_uuid = remote_uuid;
            this.connection = conn;
            this.datachannel = null;
            this.isOfferer = isOfferer;
            this.listeners = Object.freeze({
                "open": [],
                "message": []
            });

            // (function(){console.log(this)}).bind(0).bind(1)() == 0;
            conn.onicecandidate = this.onicecandidate.bind(this);
            conn.onnegotiationneeded = this.onnegotiationneeded.bind(this);
            conn.ondatachannel = this.ondatachannel.bind(this);
        }

        onicecandidate(e){
            this.local_peer.sendToServer({
                    "type": "ice_candidate",
                    "ice": e.candidate,
                    "local_uuid": this.local_peer.uuid,
                    "remote_uuid": this.remote_uuid,
            });
        }
        addicecandidate(o){
            var ice_candidate = null;
            if(o instanceof RTCIceCandidate){
                ice_candidate = o;
            } else if(typeof o === "string"){
                if(o) ice_candidate = new RTCIceCandidate(o);
            } else if((o instanceof Object) && ("ice" in o)){
                if(o["ice"]) ice_candidate = new RTCIceCandidate(o["ice"]);
            } else{
                throw new Error("FATAL: invalid ice candidate");
            }

            if(ice_candidate){
                this.connection.addIceCandidate(
                        ice_candidate).catch(catch_error);
            } else{
                __console.log("all ice candidate received");
            }
        }

        onnegotiationneeded(e){
            if(!this.isOfferer){
                __console.error("negotiationneeded invoked on receiver");
                return;
            }
            if(1){
                __console.warn("skipping negotiation (esp. on chrome)");
                return;
            }

            const peer = this.local_peer;
            __console.warn(`negotiationneeded: offerer? ${this.isOfferer}` +
                    "; local_uuid: " + peer.uuid +
                    "; remote_uuid: " + this.remote_uuid);
            if(this.isOfferer){
                createOfferWithPeerConnection(this);
            } else{
                createAnswerWithPeer(peer);
            }
        }

        ondatachannel(e){
            if(this.isOfferer){
                __console.error("ondatachannel invoked on offerer");
                return;
            }
            const __this = this;

            var ch = e.channel;
            __console.log("ondatachannel: channel received, id:", ch.id);
            new Promise(resolve => {
                ch.addEventListener("open", resolve);
            }).then(e => new Promise(resolve => {
                const onchannelmessage = __this.onchannelmessage.bind(__this);
                ch.addEventListener("message", onchannelmessage);
                __console.log("ondatachannel: channel opened, id:", ch.id);
                __console.assert(ch === e.target);

                if(__this.datachannel_opened){
                    __console.log("webrtc.js: channel opened before, skipped");
                } else{
                    __console.log("webrtc.js: dispatching open event");
                    __this.datachannel_opened = true;
                    __this.dispatch("open", __this);
                }
                
                if(__this.datachannel){
                    __console.log("old datachannel#" +
                    __this.datachannel.id + " exists, closing");
                    __this.datachannel.close();
                    __this.datachannel.removeEventListener(
                            "message", __this.last_channelmessage_handler);
                }
                
                __this.last_channelmessage_handler = onchannelmessage;
                __this.datachannel = ch;
            })).catch(catch_error);
        }

        onchannelmessage(e){
            this.dispatch("message", e.data);
        }

        send(data){
            const __this = this;
            this.datachannel_pending_message = (
                    this.datachannel_pending_message || []);
            this.datachannel_pending_message.push(data);
            function sendFirstPendingMessage(){
                if(__this.datachannel_pending_message.length && (
                        __this.datachannel &&
                        __this.datachannel.readyState == "open")){
                    __this.datachannel.send(
                            __this.datachannel_pending_message.shift());
                }
                if(__this.datachannel_pending_message.length){
                    setTimeout(sendFirstPendingMessage, 100);
                }
            }
            sendFirstPendingMessage()
            // this.datachannel.send(data);
        }

        on(event, l){
            if(typeof l !== "function"){
                throw new Error("invalid listener: not a function");
            }
            switch(event){
            case "data":
                event = "message";
            case "message":
            case "open":
                if((event == "open") && this.datachannel){
                    l(this);
                }
                this.listeners[event].push(l);
            break;
            default:
                throw new Error("unsupported event");
            }
        }

        dispatch(event, e){
            switch(event){
            case "open":
            case "message":
                for(var l of this.listeners[event]){
                    l(e);
                }
                break;
            default:
                throw new Error("unsupported event");
            }
        }
        close(){
            this.connection.close();
        }

    }

    function onPeerCreated(peer, callback, ...args){
        switch(typeof callback){
        case "number":
            switch(!peer.peer_created){
            case false: break; // peer is created, do nothing
            case (callback < 5):
                __console.warn(`onPeerCreated(count=${callback
                        }): peer(${peer.uuid}) not created in server`);
                setTimeout(onPeerCreated, 1000, peer, callback+1);
                break;
            case true:
                throw new Error("peer creation timeout");
            }
            break;
        case "function":
            if(peer.peer_created){
                callback(...args);
            } else{
                peer.on("create", () => {
                    callback(...args);
                });
                setTimeout(onPeerCreated, 1000, peer, 0);
            }
            break;
        
        default:
            throw new Error("onPeerCreated(): invalid callback");
        }
    }
    function createPeerConnectionForPeer(peer,
            offerer_uuid, receiver_uuid, isOfferer){
        const remote_uuid = (isOfferer ? receiver_uuid : offerer_uuid);
        var pc = peer.peer_connections[remote_uuid];
        if(!(remote_uuid in peer.peer_connections)){
            var conn = new RTCPeerConnection(RTC_PEER_CONFIGURATION);
            pc = new PeerConnection(peer, remote_uuid, conn, isOfferer);
            peer.peer_connections[remote_uuid] = pc;
        }
        if(!pc){
            __console.error("FATAL: EMPTY PEER CONNECTION");
        }
        return pc;
    }
    function createDataChannelAndOfferWithPeerAndConnection(peer, pc){
        createDataChannelWithConnection(pc);
        onPeerCreated(peer, createOfferWithPeerConnection, pc);
    }
    function createDataChannelWithConnection(pc){
        new Promise(resolve =>
                pc.connection.createDataChannel("text", {
            // negotiated: true
        }).addEventListener("open", resolve
        )).then(oe => new Promise(() => {
            pc.dispatch("open", pc);
            const dc = oe.target;
            if(pc.datachannel){
                __console.log("old datachannel#" +
                        pc.datachannel + " exists, closing");
                pc.datachannel.close();
            }
            pc.datachannel = dc;
            dc.addEventListener("message", function(me){
                pc.dispatch("message", me.data);
            });
        })).catch(catch_error);
    }
    function createOfferWithPeerConnection(pc){
        __console.assert(pc instanceof PeerConnection);
        __console.log("creating offer:",
                `${pc.local_peer.uuid
                } => ${pc.remote_uuid}`);
        const conn = pc.connection;
        conn.createOffer().then(desc => {
            return conn.setLocalDescription(desc);
        }).then(() => {
            __console.log("sending session description protocol");
            pc.local_peer.sendToServer({
                "type": "create_offer",
                "sdp": conn.localDescription,
                "offerer_uuid": pc.local_peer.uuid,
                "receiver_uuid": pc.remote_uuid,
            });
        }).catch(catch_error);
    }
    function receiveOfferForPeer(peer, o){
        __console.assert(peer.uuid == o["receiver_uuid"]);
        const conn = createPeerConnectionForPeer(peer,
                o["offerer_uuid"], o["receiver_uuid"], false
        ).connection;

        __console.log("receive_offer", JSON.stringify(o));
        conn.setRemoteDescription(
                new RTCSessionDescription(o.sdp)
        ).then(() => {
            if(o.sdp.type != "offer"){
                throw new Error("received invalid offer: invalid sdp");
            }
            return conn.createAnswer();
        }).then(desc => {
            __console.warn("An error will probably come up next " +
                    "RTCPeerConnection object:", conn);
            return conn.setLocalDescription(desc);
        }).then(() => {
            __console.log("local descrp set, creating & sending answer");

            __console.log("send to server:", JSON.stringify({
                "type": "created_answer",
                "sdp": conn.localDescription,
                "offerer_uuid": o["offerer_uuid"],
                "receiver_uuid": o["receiver_uuid"],
            }));
            peer.sendToServer({
                "type": "created_answer",
                "sdp": conn.localDescription,
                "offerer_uuid": o["offerer_uuid"],
                "receiver_uuid": o["receiver_uuid"],
            });
            peer.dispatch("connection",
                    peer.peer_connections[o["offerer_uuid"]]);
        }).catch(catch_error);
    }
    function receiveAnswerWithPeer(peer, o){
        __console.log("receives answer:", JSON.stringify(o));
        __console.assert(o["type"] == "receive_answer");

        const conn = peer.peer_connections[o["receiver_uuid"]].connection;
        if(!conn){
            throw new Error("empty connection");
        }
        const sdp = o["sdp"];
        if(sdp.type != "answer"){
            throw new Error(
                    "error when receiving answer: " +
                    "invalid sdp.type: " + sdp);
        }
        __console.log(`conn.signalingState: ${conn.signalingState}`);
        switch(conn.signalingState){
        case "have-local-offer":
            __console.log("receives answer, setting remote description");
            conn.setRemoteDescription(new RTCSessionDescription(sdp
            )).then(() => {
                __console.log("remote description set");
            }).catch(catch_error);
            break;
        case "have-remote-offer":
        case "stable":
        default:
        }
    }
    


    function onMessageFromServer(e){
        __console.assert(this instanceof Peer);
        const o = JSON.parse(e.data);
        __console.warn("received from server:", o);
        switch(o.type){
        case "peer_created":
            if(this.uuid == o.uuid){
                this.peer_created = true;
                this.dispatch("create", e);
            }
            break;
        case "receive_offer":
            receiveOfferForPeer(this, o);
            break;
        case "receive_answer":
            receiveAnswerWithPeer(this, o);
            break;
        case "ice_candidate":
            // remote peer set their uuid as "local"
            this.peer_connections[o["local_uuid"]].addicecandidate(o);
            break;
        default:
            __console.error("unhandled server socket message:", o);
        }
    }

    class Peer
    {
        constructor(name){
            this.name = name;
            // avoided receiving from server because of the delay in connect
            this.peer_created = false;
            this.uuid = name || uuidv4();
            this.peer_connections = {};
            this.server_socket = new WebSocket(SOCKET_SERVER_ADDRESS);
            this.server_socket.addEventListener(
                    "message", onMessageFromServer.bind(this));
            this.listeners = Object.freeze({
                "connection": [],
                "create": [],
            });
            
            this.sendToServer({
                    "type": "create_peer",
                    "uuid": this.uuid,
            });
        }
        sendToServer(o){
            const pending_messages = this.__pending_messages || (
                    this.__pending_messages = []);
            const last_sent = this.last_sent || (
                    this.last_sent = performance.now());
            const ws = this.server_socket;
    
    
            let data = JSON.stringify(o);
            __console.log(`sendToServer: ${data}`);
            pending_messages.push(data);
            function sendFirstPendingMessage(){
                if(pending_messages.length && (
                    ws.readyState == ws.OPEN)){
                            ws.send(pending_messages.shift());
                }
                if(pending_messages.length){
                    setTimeout(sendFirstPendingMessage, 100);
                }
            }
    
            // CLOSING, CLOSED
            switch(ws.readyState){
            case ws.CONNECTING:
                // lambda function doesn't block `${this}`
                setTimeout(sendFirstPendingMessage, 50);
                setTimeout(() => {
                    if(ws.readyState == ws.CONNECTING){
                        ws.close();
                        throw new Error("connection to server time out");
                    }
                }, 10000);
                break;
            case ws.OPEN:
                sendFirstPendingMessage();
                break;
            default:
                break;
            }
        }

        connect(uuid){
            var pc = createPeerConnectionForPeer(this, this.uuid, uuid, true);
            createDataChannelAndOfferWithPeerAndConnection(this, pc);
            return pc;
        }


        on(event, l){
            if(typeof l !== "function"){
                throw new Error("invalid listener: not a function");
            }
            switch(event){
            case "create":
                if(this.peer_created) __console.error(
                        'peer.on("create"): peer already created');
                this.listeners["create"].push(l);
                break;
            case "conn":
            case "connection":
            case "connections":
                this.listeners["connection"].push(l);
                break;
            default:
                throw new Error("invalid event:", event);
            }
        }
        dispatch(event, e){
            switch(event){
            case "create":
            case "connection":
                for(var l of this.listeners[event]){
                    l(e);
                }
                break;
            default:
                throw new Error("unsupported event");
            }
        }






        static log_level(i=0){
            const empty = () => {};
    
            Object.assign(__console, {
                log:    i > 0 ? empty: console.log,
                info:   i > 0 ? empty: console.info,
                warn:   i > 1 ? empty: console.warn,
                error:  i > 2 ? empty: console.error,
                assert: __console.assert, // no need to bind
            });
        }
    }


    /*
    https://stackoverflow.com/questions/105034/
    create-guid-uuid-in-javascript#answer-2117523
    */
   function uuidv4(){
        return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(
                /[018]/g, c =>(c ^ crypto.getRandomValues(
                new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
        );
    }

    for(var [key, value] of Object.entries({
        "Peer": Peer,
        "PeerConnection": PeerConnection,
        "": undefined,
    })){
        if(value !== undefined){
            window[key] = value;
        }
    }
})();
