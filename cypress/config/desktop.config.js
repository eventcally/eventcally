const { defineConfig } = require("cypress");

module.exports = defineConfig({
  video: false,

  e2e: {
    experimentalRunAllSpecs: true,
    setupNodeEvents(on, config) {
      return require('../plugins/index.js')(on, config)
    },
    baseUrl: 'http://127.0.0.1:5000',
  },
});
