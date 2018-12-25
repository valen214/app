

const HTTPS_PORT = 8443;

const fs = require('fs');
const https = require('https');
const WebSocket = require('ws');
const WebSocketServer = WebSocket.Server;

// Yes, TLS is required
const serverConfig = {
    key: fs.readFileSync('key.pem'),
    cert: fs.readFileSync('cert.pem'),
};

// -----------------------------------------------------------------------------


function guessMIME(name){
    for(var [regex, type] of Object.entries({
            [/.js$/]: "application/javascript",
            [/.html?$/]: "text/html",
    })){
        if(name.match(regex)){
            return type;
        }
    }

    return "text/plain";
}


// Create a server for the client html page
const handleRequest = function(request, response) {
    // Render the single client html file for any request the HTTP server receives
    console.log('request received: ' + request.url);

  
    switch(request.url){
    default:
        if(fs.existsSync("." + request.url)){
            response.writeHead(200, {'Content-Type': guessMIME(request.url)});
            response.end(fs.readFileSync("." + request.url));
            break;
        }
    case "/":
        response.writeHead(200, {'Content-Type': 'text/html'});
        response.end(fs.readFileSync('index.htm'));
        break;
    }
};

const httpsServer = https.createServer(serverConfig, handleRequest);
httpsServer.listen(HTTPS_PORT, '0.0.0.0');

// -----------------------------------------------------------------------------

// Create a server for handling websocket calls
const wss = new WebSocketServer({server: httpsServer});

wss.on('connection', function(ws) {
    ws.on('message', function(message) {
        // Broadcast any received message to all clients
        console.log('received: %s', message);
        wss.broadcast(message);
    });
});

wss.broadcast = function(data) {
    this.clients.forEach(function(client) {
        if(client.readyState === WebSocket.OPEN) {
            client.send(data);
        }
    });
};

console.log('Server running. Visit https://localhost:' + HTTPS_PORT + ' in Firefox/Chrome.\n\n\
Some important notes:\n\
  * Note the HTTPS; there is no HTTP -> HTTPS redirect.\n\
  * You\'ll also need to accept the invalid TLS certificate.\n\
  * Some browsers or OSs may not allow the webcam to be used by multiple pages at once. You may need to use two different browsers or machines.\n'
);