'use strict';

var fs = require('fs');
var socket = require('socket.io-client')('https://api2.basechord.com', {path: '/rswatcher',query:"token=ljP8GkRn7WXSgFv4x9TAwQQhsqRU82TV"});
var os = require("os");
var request = require("request");
var yaml = require('yamljs');




var kioskStatus = null;




function getStore(callback) {
    request('http://192.168.200.1/index.json', function (error, response) {
        if (error){
            callback(error, null);
        }
        else {
            var data = JSON.parse(response.body);
            var fw = data.config.node_name;
            callback(null, fw.split('-')[0]);

        }
    })
}


// Kiosk Status check http://localhost:80
setInterval(function checkKioskStatus() {

    request('http://localhost', function (error, response) {
        if (error){
            var newKioskStatus = false;
            if (newKioskStatus !== kioskStatus) {
                socket.emit('kiosk', false);
                kioskStatus = newKioskStatus;
            }

        }
        else if (response.statusCode === 200) {
            var newKioskStatus = true;
            if (newKioskStatus !== kioskStatus) {
                socket.emit('kiosk', true);
                kioskStatus = newKioskStatus;
            }
        }
        else {
            var newKioskStatus = false;
            if (newKioskStatus !== kioskStatus) {
                socket.emit('kiosk', false);
                kioskStatus = newKioskStatus;
            }
        }
    });

}, 900000 );

 function getKioskVersion(callback) {
 fs.readFile('/var/www/kiosk/package.json', 'utf8', function (err, data) {
 if (err) throw err;
 var package_obj = JSON.parse(data);
 callback (package_obj.version);
 })

 }

 function getPuppetFailedResources(file) {
 return yaml.load(file).resources.failed;

 }



 fs.watch('/var/www/kiosk/package.json', function () {
 getKioskVersion(function(version) {
 socket.emit('kiosk_version', version);
 });
 }

 );

 fs.watch('/var/lib/puppet/state/last_run_summary.yaml', function (file) {
 socket.emit('puppet_fails', getPuppetFailedResources(file));

 }

 );


socket.on('connect', function(){
    getStore(function (error, store) {
        if (error) {
            socket.emit('register', {"station": os.hostname(), "store": null });
        }
        else {
            console.log(store);
            socket.emit('register', {"station": os.hostname(), "store": store });

        }

    })
    getKioskVersion(function(version) {
        socket.emit('kiosk_version', version);
    });

});
