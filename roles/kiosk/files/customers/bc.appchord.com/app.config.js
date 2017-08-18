(function() {
    'use strict';

    var app = angular.module('app');

    var config = {
        name: 'BaseChord',
        appTitle: 'BaseChord Portal',
        version: '0.0.1',
        logoImage: '/assets/images/Logo.png',
        packageIndex: '/assets/package-index.json',
        guidesPath: '/assets/guides',
        guidesIndexFile: 'index.html',
        guides: [
            {SKU: '1375XB1', GuideName: '1375XB1', Model: 'Xbox One', IsRefereshSupported: true, Manufacturer: 'Microsoft', DynamicGuideName: 'XboxOne'}
        ],

        demo: false
    };

    app.value('config', config);
})();
