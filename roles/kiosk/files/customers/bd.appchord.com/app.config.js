(function() {
    'use strict';

    var app = angular.module('app');

    var config = {
        name: 'Buddys',
        appTitle: 'Buddys Portal',
        version: '0.0.1',
        logoImage: '/assets/images/Logo.png',
        packageIndex: '/assets/package-index.json',
        guidesPath: '/assets/guides',
        guidesIndexFile: 'index.html',
        guides: [
            {SKU: 'XBOX_SKU_HERE', GuideName: 'XBOX_SKU_HERE', Model: 'Xbox One', IsRefereshSupported: true, Manufacturer: 'Microsoft', DynamicGuideName: 'XboxOne'}
        ],

        demo: false
    };

    app.value('config', config);
})();
