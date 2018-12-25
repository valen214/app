(function(){

    var uuid;
    var serverConnection;
    var peerConnection;

    var peerConnectionConfig = {
        "iceServers": [
            {"urls": "stun:stun.stunprotocol.org:3478"},
            {"urls": "stun:stun.l.google.com:19302"},
        ]
    }

    function initialize(){
        uuid = uuidv4();

        serverConnection = new WebSocket(
                    "wss://" + window.location.hostname + ":8443");
        serverConnection.onmessage = gotMessageFromServer;
    }

    function start(isCaller){
        peerConnection = new RTCPeerConnection(peerConnectionConfig);
        peerConnection.onicecandidate = gotIceCandidate;
        // peerConnection.ontrack = gotRemoteStream;
        // peerConnection.addStream(localStream);

        if(isCaller){
            peerConnection.createOffer().then(
                    createdDescription).catch(errorHandler);
        }
    }

    function createdDescription(description){
        console.log("got description", description);
        peerConnection.setLocalDescription(description).then(function(){
            serverConnection.send(JSON.stringify({
                    "sdp": peerConnection.localDescription,
                    "uuid": uuid,
            }));
        }).catch(errorHandler);
    }

    function gotMessageFromServer(message){
        if(!peerConnection) start(false);

        var signal = JSON.parse(message.data);

        if(signal.uuid == uuid) return;
        if(signal.sdp){
            peerConnection.setRemoteDescription(
                    new RTCSessionDescription(signal.sdp)).then(function(){
                    if(signal.sdp.type == "offer"){
                        peerConnection.createAnswer().then(
                                createdDescription).catch(errorHandler);
                    }
                    var dc = peerConnection.createDataChannel("Channel_Label");
                    window["dc"] = dc;
            }).catch(errorHandler);
        } else if(signal.ice){
            peerConnection.addIceCandidate(
                    new RTCIceCandidate(signal.ice)).catch(errorHandler);
        }
    }

    function gotIceCandidate(event){
        if(event.candidate != null){
            serverConnection.send(JSON.stringify({
                    "ice": event.candidate,
                    "uuid": uuid,
            }));
        }
    }

    function errorHandler(e){
        console.error(e);
    }

    
    for(var [key, value] of Object.entries({
        "initialize": initialize,
        "start": start,
    })){
        if(value !== undefined){
            window[key] = value;
        }
    }
})();