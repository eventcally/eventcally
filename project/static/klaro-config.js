var klaroConfig = {
    version: 1,
    styling: {
        theme: ['top', 'wide'],
    },
    noticeAsModal: true,
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
        consentNotice: {
            description: 'Hallo! Könnten wir bitte einige zusätzliche Dienste für die Verbesserung der Benutzererfahrung aktivieren? Sie können Ihre Zustimmung später jederzeit ändern oder zurückziehen.',
            learnMore: 'Einstellen',
        },
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