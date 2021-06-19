var klaroConfig = {
    version: 1,
    styling: {
        theme: ['top', 'wide'],
    },
    acceptAll: true,
    hideDeclineAll: true,
    services: [
      {
        name: 'google-tag-manager',
        title: 'Google Tag Manager',
        purposes: ['analytics'],
      },
      {
        name: 'google-analytics',
        title: 'Google Analytics',
        purposes: ['analytics'],
        cookies: [
          /^_ga(_.*)?/
        ],
        callback: function(consent, app) {
            if(consent !== false) {
              window.dataLayer.push({'event' : 'consent-google-analytics'});
            }
        },
        required: false,
        optOut: false,
        onlyOnce: true,
      },
      {
        name: 'hotjar',
        title: 'Hotjar',
        purposes: ['analytics'],
        cookies: [
          /^_hj.*/
        ],
        callback: function(consent, app) {
            if(consent !== false) {
              window.dataLayer.push({'event' : 'consent-hotjar'});
            }
        },
        required: false,
        optOut: false,
        onlyOnce: true,
      },
    ],
    translations: {
      de: {
        privacyPolicyUrl: '/privacy',
        purposes: {
          analytics: 'Verbesserung der Benutzererfahrung',
        },
      },
      en: {
        privacyPolicyUrl: '/privacy',
        purposes: {
          analytics: 'Improvement of the user experience',
        },
      },
    }
  };