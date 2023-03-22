const WidgetConfigurator = {
  template: `
    <b-container fluid class="h-100 d-flex flex-column">
      <b-row class="flex-shrink-0 bg-light" align-v="center">
        <b-col cols="auto">
          <h1 class="my-3">{{ $t("comp.title") }}</h1>
        </b-col>
        <b-col cols="auto">
          <b-overlay :show="isLoading">
            <b-form inline>
              <b-input-group :prepend="$t('shared.models.customWidget.widgetType')" class="mb-2 mr-sm-2 mb-sm-0">
                <b-form-select v-model="widgetType" :options="widgetTypes"></b-form-select>
              </b-input-group>
              <b-input-group :prepend="$t('shared.models.customWidget.name')" class="mb-2 mr-sm-2 mb-sm-0">
                <b-form-input v-model="name"></b-form-input>
              </b-input-group>
              <b-button variant="secondary" @click="goBack" v-bind:disabled="isSubmitting" class="mb-2 mr-sm-2 mb-sm-0">{{ $t("shared.cancel") }}</b-button>
              <b-button variant="primary" @click.prevent="submitForm()" v-bind:disabled="isSubmitting" class="mb-2 mb-sm-0">
                  <b-spinner small v-if="isSubmitting"></b-spinner>
                  {{ $t("shared.save") }}
              </b-button>
            </b-form inline>
          </b-overlay>
        </b-col>
      </b-row>
      <b-row class="flex-fill" style="min-height:0;">
        <b-col sm="3" class="mh-100 py-3" style="overflow-y: scroll;">
        <b-overlay :show="isLoading">
          <b-card no-body>
            <b-tabs card>
              <b-tab :title="$t('comp.tabSettings')" active>
                <div v-if="widgetType == 'search'">
                  <custom-typeahead
                    v-model="searchEventList"
                    rules=""
                    validClass=""
                    :fetchURL="eventListFetchUrl"
                    :labelValue="$t('comp.search.eventListId')"
                    :showOnFocus="true"
                    :serializer="i => i.name"
                  />
                  <b-form-group :label="$t('comp.search.layout')">
                    <b-form-select v-model="form.search.layout" :options="searchLayouts"></b-form-select>
                  </b-form-group>
                  <b-form-group :label="$t('comp.search.eventsPerPage')">
                    <b-form-input v-model="form.search.eventsPerPage"></b-form-input>
                  </b-form-group>

                  <b-form-group :label="$t('comp.search.view')">
                    <b-form-checkbox v-model="form.search.showFilter">
                      {{ $t("comp.search.showFilter") }}
                    </b-form-checkbox>
                    <b-form-checkbox v-model="form.search.showPagination">
                      {{ $t("comp.search.pagination") }}
                    </b-form-checkbox>
                    <b-form-checkbox v-model="form.search.showEventCallyLink">
                      {{ $t("comp.search.showEventCallyLink") }}
                    </b-form-checkbox>
                    <b-form-checkbox v-model="form.search.showPrintButton">
                      {{ $t("comp.search.printButton") }}
                    </b-form-checkbox>
                  </b-form-group>

                  <b-form-group :label="$t('comp.search.iFrameMinHeight')">
                    <b-form-input v-model="form.search.iFrameMinHeight" debounce="500"></b-form-input>
                  </b-form-group>
                  <b-form-group :label="$t('comp.search.iFrameMaxHeight')">
                    <b-form-input v-model="form.search.iFrameMaxHeight" debounce="500"></b-form-input>
                  </b-form-group>
                </div>

                <div v-if="widgetType == 'calendar'">
                  <b-form-group :label="$t('comp.calendar.calendarType')">
                    <b-form-select v-model="form.calendar.calendarType" :options="calendarTypes"></b-form-select>
                  </b-form-group>
                  <b-form-group :label="$t('comp.calendar.iFrameHeight')">
                    <b-form-input v-model="form.calendar.iFrameHeight" debounce="500"></b-form-input>
                  </b-form-group>
                </div>
              </b-tab>
              <b-tab :title="$t('comp.tabStyles')">
                <div v-if="widgetType == 'search'">
                  <b-form-group :label="$t('comp.generic.fontFamily')">
                    <b-form-input v-model="form.search.fontFamily"></b-form-input>
                  </b-form-group>
                  <b-form-group :label="$t('comp.generic.padding')">
                    <b-form-input v-model="form.search.padding"></b-form-input>
                  </b-form-group>
                  <b-form-group :label="$t('comp.generic.backgroundColor')">
                    <b-form-input v-model="form.search.background" type="color"></b-form-input>
                  </b-form-group>
                  <b-form-group :label="$t('comp.generic.textColor')">
                    <b-form-input v-model="form.search.textColor" type="color"></b-form-input>
                  </b-form-group>
                  <b-form-group :label="$t('comp.generic.linkColor')">
                    <b-form-input v-model="form.search.linkColor" type="color"></b-form-input>
                  </b-form-group>

                  <template v-if="form.search.layout == 'card'">
                    <b-form-group :label="$t('comp.search.event') + ' ' + $t('comp.generic.backgroundColor')">
                      <b-form-input v-model="form.search.eventBackgroundColor" type="color"></b-form-input>
                    </b-form-group>
                    <b-form-group :label="$t('comp.search.event') + ' ' + $t('comp.generic.borderColor')">
                      <b-form-input v-model="form.search.eventBorderColor" type="color"></b-form-input>
                    </b-form-group>
                    <b-form-group :label="$t('comp.search.eventName') + ' ' + $t('comp.generic.textColor')">
                      <b-form-input v-model="form.search.eventNameTextColor" type="color"></b-form-input>
                    </b-form-group>
                    <b-form-group :label="$t('comp.search.eventDate') + ' ' + $t('comp.generic.textColor')">
                      <b-form-input v-model="form.search.eventDateTextColor" type="color"></b-form-input>
                    </b-form-group>
                    <b-form-group :label="$t('comp.search.eventInfo') + ' ' + $t('comp.generic.textColor')">
                      <b-form-input v-model="form.search.eventInfoTextColor" type="color"></b-form-input>
                    </b-form-group>
                  </template>

                  <b-form-group :label="$t('comp.search.eventBadgeWarning') + ' ' + $t('comp.generic.backgroundColor')">
                    <b-form-input v-model="form.search.eventBadgeWarningBackgroundColor" type="color"></b-form-input>
                  </b-form-group>
                  <b-form-group :label="$t('comp.search.eventBadgeWarning') + ' ' + $t('comp.generic.textColor')">
                    <b-form-input v-model="form.search.eventBadgeWarningTextColor" type="color"></b-form-input>
                  </b-form-group>
                  <b-form-group :label="$t('comp.search.eventBadgeInfo') + ' ' + $t('comp.generic.backgroundColor')">
                    <b-form-input v-model="form.search.eventBadgeInfoBackgroundColor" type="color"></b-form-input>
                  </b-form-group>
                  <b-form-group :label="$t('comp.search.eventBadgeInfo') + ' ' + $t('comp.generic.textColor')">
                    <b-form-input v-model="form.search.eventBadgeInfoTextColor" type="color"></b-form-input>
                  </b-form-group>

                  <template v-if="form.search.showFilter">
                    <b-form-group :label="$t('comp.search.filterLabel') + ' ' + $t('comp.generic.backgroundColor')">
                      <b-form-input v-model="form.search.filterLabelBackgroundColor" type="color"></b-form-input>
                    </b-form-group>
                    <b-form-group :label="$t('comp.search.filterLabel') + ' ' + $t('comp.generic.borderColor')">
                      <b-form-input v-model="form.search.filterLabelBorderColor" type="color"></b-form-input>
                    </b-form-group>
                    <b-form-group :label="$t('comp.search.filterLabel') + ' ' + $t('comp.generic.textColor')">
                      <b-form-input v-model="form.search.filterLabelTextColor" type="color"></b-form-input>
                    </b-form-group>

                    <b-form-group :label="$t('comp.search.filterInput') + ' ' + $t('comp.generic.backgroundColor')">
                      <b-form-input v-model="form.search.filterInputBackgroundColor" type="color"></b-form-input>
                    </b-form-group>
                    <b-form-group :label="$t('comp.search.filterInput') + ' ' + $t('comp.generic.borderColor')">
                      <b-form-input v-model="form.search.filterInputBorderColor" type="color"></b-form-input>
                    </b-form-group>
                    <b-form-group :label="$t('comp.search.filterInput') + ' ' + $t('comp.generic.textColor')">
                      <b-form-input v-model="form.search.filterInputTextColor" type="color"></b-form-input>
                    </b-form-group>

                    <b-form-group :label="$t('comp.search.filterButton') + ' ' + $t('comp.generic.backgroundColor')">
                      <b-form-input v-model="form.search.buttonBackgroundColor" type="color"></b-form-input>
                    </b-form-group>
                    <b-form-group :label="$t('comp.search.filterButton') + ' ' + $t('comp.generic.borderColor')">
                      <b-form-input v-model="form.search.buttonBorderColor" type="color"></b-form-input>
                    </b-form-group>
                    <b-form-group :label="$t('comp.search.filterButton') + ' ' + $t('comp.generic.textColor')">
                      <b-form-input v-model="form.search.buttonTextColor" type="color"></b-form-input>
                    </b-form-group>
                  </template>

                  <template v-if="form.search.showPagination">
                    <b-form-group :label="$t('comp.search.pagination') + ' ' + $t('comp.generic.borderColor')">
                      <b-form-input v-model="form.search.pagingBorderColor" type="color"></b-form-input>
                    </b-form-group>
                    <b-form-group :label="$t('comp.search.pagination') + ' ' + $t('comp.generic.color')">
                      <b-form-input v-model="form.search.pagingColor" type="color"></b-form-input>
                    </b-form-group>
                    <b-form-group :label="$t('comp.search.pagination') + ' ' + $t('comp.generic.textColor')">
                      <b-form-input v-model="form.search.pagingTextColor" type="color"></b-form-input>
                    </b-form-group>
                    <b-form-group :label="$t('comp.search.pagination') + ' ' + $t('comp.generic.disabled') + ' ' + $t('comp.generic.textColor')">
                      <b-form-input v-model="form.search.pagingDisabledTextColor" type="color"></b-form-input>
                    </b-form-group>
                    <b-form-group :label="$t('comp.search.pagination') + ' ' + $t('comp.generic.active') + ' ' + $t('comp.generic.textColor')">
                      <b-form-input v-model="form.search.pagingActiveTextColor" type="color"></b-form-input>
                    </b-form-group>
                  </template>

                  <template v-if="form.search.showPrintButton">
                    <b-form-group :label="$t('comp.search.printButton') + ' ' + $t('comp.generic.backgroundColor')">
                      <b-form-input v-model="form.search.printButtonBackgroundColor" type="color"></b-form-input>
                    </b-form-group>
                    <b-form-group :label="$t('comp.search.printButton') + ' ' + $t('comp.generic.borderColor')">
                      <b-form-input v-model="form.search.printButtonBorderColor" type="color"></b-form-input>
                    </b-form-group>
                    <b-form-group :label="$t('comp.search.printButton') + ' ' + $t('comp.generic.textColor')">
                      <b-form-input v-model="form.search.printButtonTextColor" type="color"></b-form-input>
                    </b-form-group>
                  </template>
                </div>

                <div v-if="widgetType == 'calendar'">
                  <b-form-group :label="$t('comp.calendar.eventBackgroundColor')">
                    <b-form-input v-model="form.calendar.eventBackgroundColor" type="color"></b-form-input>
                  </b-form-group>
                </div>
              </b-tab>
            </b-tabs>
          </b-card>
          </b-overlay>
        </b-col>
        <b-col sm="9" class="mh-100 py-3" style="overflow-y: scroll;">
          <b-container fluid class="h-100 d-flex flex-column px-0">
            <b-row class="flex-shrink-0">
              <b-col class="my-2">
                <b-form inline class="float-sm-right">
                  <b-form-input
                    v-model="previewBackgroundColor"
                    type="color"
                    class="mr-sm-2"
                    style="min-width:40px;"></b-form-input>
                  <b-form-radio-group
                    v-model="previewSize"
                    :options="previewSizes"
                    size="sm"
                    button-variant="outline-secondary"
                    buttons
                  ></b-form-radio-group>
                </b-form>
              </b-col>
            </b-row>
            <b-row class="flex-fill" style="min-height:0;">
              <b-col class="mh-100" style="overflow-y: scroll;">
                <div ref="previewPage" class="h-100 border p-3 m-auto" :style="{width: previewSize, 'background-color': previewBackgroundColor + '!important', 'overflow-y': 'scroll'}">
                  <div class="mb-2 font-weight-bold">{{ $t("comp.preview") }}</div>
                  <iframe v-if="iFrameActive" :key="iFrameCounter" class="preview_iframe" ref="previewIframe" :src="iFrameSource" style="width:100%; height:300px;" frameborder="0"></iframe>
                </div>
              </b-col>
            </b-row>
          </b-container>
        </b-col>
      </b-row>
    </b-container>
    `,
  i18n: {
    messages: {
      en: {
        comp: {
          title: "Widget configurator",
          successMessage: "Widget successfully saved",
          preview: "Preview",
          tabSettings: "Serrings",
          tabStyles: "Styles",
          generic: {
            fontFamily: "Font family",
            padding: "Padding",
            backgroundColor: "Background color",
            textColor: "Text color",
            linkColor: "Link color",
            borderColor: "Border color",
            color: "Color",
            disabled: "Deactivated",
            active: "Activ",
          },
          calendar: {
            iFrameHeight: "Height",
            eventBackgroundColor: "Event color",
            calendarType: "Calendar type",
          },
          search: {
            iFrameMinHeight: "Min. Height",
            iFrameMaxHeight: "Max. Height",
            eventListId: "Event list",
            view: "Display",
            showFilter: "Filter",
            showEventCallyLink: "Link",
            layout: "Layout",
            eventsPerPage: "Events per page",
            event: "Event",
            eventName: "Event name",
            eventDate: "Event datum",
            eventInfo: "Event info",
            eventBadgeWarning: "Event warning badge",
            eventBadgeInfo: "Event info badge",
            filterLabel: "Filter label",
            filterInput: "Filter input",
            filterButton: "Filter button",
            pagination: "Pagination",
            printButton: "Print button",
          },
        },
      },
      de: {
        comp: {
          title: "Widget Konfigurator",
          successMessage: "Widget erfolgreich gespeichert",
          preview: "Vorschau",
          tabSettings: "Einstellungen",
          tabStyles: "Styles",
          generic: {
            fontFamily: "Schriftart",
            padding: "Abstand",
            backgroundColor: "Hintergrundfarbe",
            textColor: "Textfarbe",
            linkColor: "Link-Farbe",
            borderColor: "Rahmen-Farbe",
            color: "Farbe",
            disabled: "Deaktiviert",
            active: "Aktiv",
          },
          calendar: {
            iFrameHeight: "Höhe",
            eventBackgroundColor: "Event Farbe",
            calendarType: "Kalender Typ",
          },
          search: {
            iFrameMinHeight: "Min. Höhe",
            iFrameMaxHeight: "Max. Höhe",
            eventListId: "Veranstaltungsliste",
            view: "Anzeige",
            showFilter: "Filter",
            showEventCallyLink: "Link",
            layout: "Layout",
            eventsPerPage: "Events pro Seite",
            event: "Event",
            eventName: "Event-Name",
            eventDate: "Event-Datum",
            eventInfo: "Event-Info",
            eventBadgeWarning: "Event Warnungszeichen",
            eventBadgeInfo: "Event Infozeichen",
            filterLabel: "Filter-Label",
            filterInput: "Filter-Eingabe",
            filterButton: "Filter-Button",
            pagination: "Paginierung",
            printButton: "Drucken-Button",
          },
        },
      },
    },
  },
  data: () => ({
    iFrameActive: true,
    iFrameCounter: 0,
    previewSize: '100%',
    previewSizes: [
      { text: 'Desktop', value: '100%' },
      { text: 'Tablet', value: '768px' },
      { text: 'Mobile', value: '400px' },
    ],
    previewBackgroundColor: '#f8f9fa',
    isLoading: false,
    isSubmitting: false,
    customWidget: null,
    form: {
      search: {
        layout: "card",
        iFrameMinHeight: 400,
        iFrameMaxHeight: "Infinity",
        iFrameAutoResize: true,
        organizationId: null,
        eventListId: null,
        eventsPerPage: 10,
        showFilter: true,
        showPagination: true,
        showPrintButton: false,
        showEventCallyLink: true,
        fontFamily: "",
        background: "#ffffff",
        textColor: "#212529",
        padding: "1rem",
        linkColor: "#007bff",
        buttonBackgroundColor: "#007bff",
        buttonBorderColor: "#007bff",
        buttonTextColor: "#ffffff",
        printButtonBackgroundColor: "#6c757d",
        printButtonBorderColor: "#6c757d",
        printButtonTextColor: "#ffffff",
        filterLabelBackgroundColor: "#e9ecef",
        filterLabelBorderColor: "#ced4da",
        filterLabelTextColor: "#495057",
        filterInputBackgroundColor: "#ffffff",
        filterInputBorderColor: "#ced4da",
        filterInputTextColor: "#495057",
        eventBackgroundColor: "#ffffff",
        eventBorderColor: "#00000020",
        eventNameTextColor: "#000000",
        eventDateTextColor: "#212529",
        eventInfoTextColor: "#6c757d",
        pagingBorderColor: "#dee2e6",
        pagingColor: "#007bff",
        pagingTextColor: "#007bff",
        pagingActiveTextColor: "#ffffff",
        pagingDisabledTextColor: "#6c757d",
        eventBadgeWarningBackgroundColor: "#ffc107",
        eventBadgeWarningTextColor: "#212529",
        eventBadgeInfoBackgroundColor: "#17a2b8",
        eventBadgeInfoTextColor: "#ffffff",
      },
      calendar: {
        iFrameHeight: 600,
        iFrameAutoResize: false,
        organizationId: null,
        eventListId: null,
        calendarType: "week",
        eventBackgroundColor: "#007bff",
      }
    },
    calendarTypes: [
      { value: "week", text: 'Woche' },
      { value: 'month', text: 'Monat' },
    ],
    searchLayouts: [
      { value: "card", text: 'Karten' },
      { value: 'text', text: 'Text' },
    ],
    widgetType: "search",
    widgetTypes: [],
    name: "Widget",
    searchEventList: null,
  }),
  computed: {
    iFrameSource() {
      return `${window.location.origin}/static/widget/${this.widgetType}.html`;
    },
    organizationId() {
      return this.$route.params.organization_id;
    },
    customWidgetId() {
      return this.$route.params.custom_widget_id;
    },
    settings() {
      return this.form[this.widgetType];
    },
    iFrameResizerOptions() {
      return {
        autoResize: this.settings.iFrameAutoResize,
        minHeight: this.settings.iFrameMinHeight != null ? this.settings.iFrameMinHeight : this.settings.iFrameHeight,
        maxHeight: this.settings.iFrameMaxHeight != null ? this.settings.iFrameMaxHeight : this.settings.iFrameHeight,
        scrolling: "omit",
      };
    },
    eventListFetchUrl() {
      return `/api/v1/organizations/${this.organizationId}/event-lists?name={query}`;
    },
  },
  mounted() {
    this.isLoading = false;
    this.customWidget = null;
    this.widgetTypes = [
      { value: "search", text: this.$t("shared.models.customWidget.widgetTypeSearch") },
      { value: "calendar", text: this.$t("shared.models.customWidget.widgetTypeCalendar") },
    ]
    this.form.search.organizationId = this.organizationId;
    this.form.calendar.organizationId = this.organizationId;

    if (this.customWidgetId == null) {
      this.initResizer();
    } else {
      this.loadFormData();
    }
  },
  watch: {
    settings: {
        handler: function (val, oldVal) {
          this.updatePreview();
        },
        deep: true
    },
    iFrameResizerOptions: {
      handler: function (val, oldVal) {
        this.reloadIframe();
      },
      deep: true
    },
    searchEventList: function(val) {
      this.form.search.eventListId = val != null ? val.id : null;
    },
    previewSize: function(val) {
      this.resizePreview();
    }
  },
  methods: {
    reloadIframe() {
      this.iFrameActive = false;
      this.iFrameCounter++;
      this.iFrameActive = true;
      this.initResizer();
    },
    initResizer() {
      const vm = this;
      Vue.nextTick(function () {
        iFrameResize({
          autoResize: vm.iFrameResizerOptions.autoResize,
          minHeight: vm.iFrameResizerOptions.minHeight,
          maxHeight: vm.iFrameResizerOptions.maxHeight,
          scrolling: vm.iFrameResizerOptions.scrolling,
          onMessage: function(m) {},
          onInit: function() { vm.updatePreview() },
        },
        '.preview_iframe');
      });
    },
    updatePreview() {
      const resizer = this.$refs.previewIframe.iFrameResizer;

      if (resizer === undefined) {
        return;
      }

      resizer.sendMessage({'type': 'EVENTCALLY_WIDGET_SETTINGS_UPDATE_EVENT', 'data': this.settings});
    },
    resizePreview() {
      const resizer = this.$refs.previewIframe.iFrameResizer;

      if (resizer === undefined) {
        return;
      }

      resizer.resize();
    },
    loadFormData() {
      axios
        .get(`/api/v1/custom-widgets/${this.customWidgetId}`, {
          withCredentials: true,
          handleLoading: this.handleLoading,
        })
        .then((response) => {
          this.customWidget = response.data;
          this.widgetType = this.customWidget.widget_type;
          this.name = this.customWidget.name;

          for (var key in this.customWidget.settings) {
              this.settings[key] = this.customWidget.settings[key];
          }
        });
    },
    handleLoading(isLoading) {
      this.isLoading = isLoading;
    },
    submitForm() {
      let data = {
          'widget_type': this.widgetType,
          'name': this.name,
          'settings': this.settings,
      };

      if (this.customWidgetId == null) {
        axios
        .post(`/api/v1/organizations/${this.organizationId}/custom-widgets`,
          data,
          {
            withCredentials: true,
            handleLoading: this.handleSubmitting,
          })
        .then(() => {
          this.$root.makeSuccessToast(this.$t("comp.successMessage"))
          this.goBack()
        })
      } else {
        axios
        .put(`/api/v1/custom-widgets/${this.customWidgetId}`,
          data,
          {
            withCredentials: true,
            handleLoading: this.handleSubmitting,
          })
        .then(() => {
          this.$root.makeSuccessToast(this.$t("comp.successMessage"))
          this.goBack()
        })
      }
    },
    handleSubmitting(isLoading) {
        this.isSubmitting = isLoading;
    },
    goBack() {
      window.location.href = `/manage/admin_unit/${this.organizationId}/custom-widgets`;
    },
  },
};
