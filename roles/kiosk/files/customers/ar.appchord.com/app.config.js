(function() {
    'use strict';

    var app = angular.module('app');

    var config = {
        name: 'Aarons',
        appTitle: 'Aarons Portal',
        version: '1.0.1',
        logoImage: '/assets/images/Logo.png',
        packageIndex: '/assets/package-index.json',
        guidesPath: '/assets/guides',
        guidesIndexFile: 'index.html',
        guides: {
            '7339F74': {SKU: '7339F74', GuideName: '7339F74', Model: 'Xbox One Console', IsRefereshSupported: true, Manufacturer: 'Microsoft', DynamicGuideName: 'XboxOne'},
            '7339FB1': {SKU: '7339FB1', GuideName: '7339FB1', Model: 'Xbox One 500GB with Kinect and Bonus Game', IsRefereshSupported: true, Manufacturer: 'Microsoft', DynamicGuideName: 'XboxOne'},
            '7339FB2': {SKU: '7339FB2', GuideName: '7339FB2', Model: 'Xbox One 500GB with Bonus Game and 1 Controller', IsRefereshSupported: true, Manufacturer: 'Microsoft', DynamicGuideName: 'XboxOne'},
            '7339NX1': {SKU: '7339NX1', GuideName: '7339NX1', Model: 'Xbox One with 2 Controllers Direct', IsRefereshSupported: true, Manufacturer: 'Microsoft', DynamicGuideName: 'XboxOne'},
            '7339XB1': {SKU: '7339XB1', GuideName: '7339XB1', Model: 'Xbox One with Kinect 8 Core 500BG Blu-Ray HDMI 1 Controller', IsRefereshSupported: true, Manufacturer: 'Microsoft', DynamicGuideName: 'XboxOne'},
            '7339XB2': {SKU: '7339XB2', GuideName: '7339XB2', Model: 'Xbox One with Kinect 500 GB Blu-Ray HDMI Play Charge', IsRefereshSupported: true, Manufacturer: 'Microsoft', DynamicGuideName: 'XboxOne'},
            '7339XB3': {SKU: '7339XB3', GuideName: '7339XB3', Model: 'Xbox One with Kinect 500GB Forza 5 Play Charge Unit', IsRefereshSupported: true, Manufacturer: 'Microsoft', DynamicGuideName: 'XboxOne'},
            '7339XB5': {SKU: '7339XB5', GuideName: '7339XB5', Model: 'Xbox One with Kinect 500GB', IsRefereshSupported: true, Manufacturer: 'Microsoft', DynamicGuideName: 'XboxOne'},
            '7339XC1': {SKU: '7339XC1', GuideName: '7339XC1', Model: 'Xbox One 500GB Includes Game', IsRefereshSupported: true, Manufacturer: 'Microsoft', DynamicGuideName: 'XboxOne'},
            '7339XC2': {SKU: '7339XC2', GuideName: '7339XC2', Model: 'Xbox One 500GB without Kinect', IsRefereshSupported: true, Manufacturer: 'Microsoft', DynamicGuideName: 'XboxOne'},
            '7339XC3': {SKU: '7339XC3', GuideName: '7339XC3', Model: 'Xbox One 500GB with Bonus Game and 1 Controller', IsRefereshSupported: true, Manufacturer: 'Microsoft', DynamicGuideName: 'XboxOne'},
            '7339XMH': {SKU: '7339XMH', GuideName: '7339XMH', Model: 'Xbox One Bundle', IsRefereshSupported: true, Manufacturer: 'Microsoft', DynamicGuideName: 'XboxOne'},
            '7393TS5': {SKU: '7393TS5', GuideName: '7393TS5', Model: 'Galaxy S5 5.1"', IsRefereshSupported: true, Manufacturer: 'Samsung', DynamicGuideName: 'Android'}
        },
        itemNumberRegEx: /^\d{10}$/,
        networkDevices: [
            {description: 'Meraki MX64 Cloud Managed Router', displayDescription: 'Cisco Firewall', deviceImageFile: 'FirewallMerakiMx64.png', wiringImageFile: 'WiringDiagramMerakiMx64.png', correctPort: '4', isServiceCenterConfig: false, isPortDetectable: false},
            {description: 'Meraki MS220-24P Cloud Managed PoE Switch', displayDescription: 'Cisco Switch', deviceImageFile: 'SwitchMerakiMs220-24.png', wiringImageFile: 'WiringDiagramMerakiMs220ServiceCenter.png', correctPort: '21', isServiceCenterConfig: true, isPortDetectable: true},
            {description: 'Meraki MS220-24P Cloud Managed PoE Switch', displayDescription: 'Cisco Switch', deviceImageFile: 'SwitchMerakiMs220-24.png', wiringImageFile: 'WiringDiagramMerakiMs220.png', correctPort: '22', isServiceCenterConfig: false, isPortDetectable: true},
            {description: 'SonicWALL TZ-210', displayDescription: 'SonicWALL', deviceImageFile: 'FirewallSonicWall.png', wiringImageFile: 'WiringDiagramSonicWallTz-210.png', correctPort: 'X5', isServiceCenterConfig: false, isPortDetectable: false}
        ],
        demo: false
    };

    app.value('config', config);
})();
