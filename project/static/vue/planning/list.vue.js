const PlanningList = {
  template: `
  <div v-cloak>
    <template>
        <v-app>
            <v-row class="fill-height" style="margin:0;">
                <v-col class="px-0">
                  <v-sheet height="64">
                            <v-toolbar flat>
                              <v-btn outlined class="mr-4" color="grey darken-2" @click="setToday">
                                {{ $t("comp.today") }}
                              </v-btn>
                                <v-btn fab text small color="grey darken-2" @click="$refs.calendar.prev()">
                                    <v-icon small>
                                        mdi-chevron-left
                                    </v-icon>
                                </v-btn>
                                <v-btn fab text small color="grey darken-2" @click="$refs.calendar.next()">
                                    <v-icon small>
                                        mdi-chevron-right
                                    </v-icon>
                                </v-btn>
                                <v-toolbar-title>
                                    {{ title }}
                                </v-toolbar-title>
                                <v-toolbar-title class="mx-4 text--secondary font-weight-light">
                                    {{ countTitle }}
                                </v-toolbar-title>
                                <v-progress-circular
                                  indeterminate
                                  color="primary"
                                  class="mx-4"
                                  v-show="isLoading"
                                ></v-progress-circular>
                                <v-btn color="primary"
                                depressed outlined class="mr-4" @click="openFilter" v-show="!isLoading">
                                  <v-icon small>
                                    mdi-filter
                                  </v-icon>
                                  {{ $t("comp.filter") }}
                                </v-btn>
                                <v-spacer></v-spacer>

                                <v-btn-toggle
                                  v-model="type"
                                  color="primary"
                                  dense
                                  group
                                >
                                  <v-btn value="day">
                                    {{ $t("comp.day") }}
                                  </v-btn>
                                  <v-btn value="week">
                                    {{ $t("comp.week") }}
                                  </v-btn>
                                  <v-btn value="month">
                                    {{ $t("comp.month") }}
                                  </v-btn>
                                </v-btn-toggle>
                            </v-toolbar>
                    </v-sheet>
                    <v-sheet v-show="warning">
                        <v-alert dense
                        outlined
                        text
                        type="warning">
                          {{ warning }}
                        </v-alert>
                    </v-sheet>
                    <v-sheet height="800">
                            <v-calendar
                                ref="calendar"
                                v-model="focus"
                                locale="de"
                                :weekdays="[1, 2, 3, 4, 5, 6, 0]"
                                :type="type"
                                :events="events"
                                :event-color="getEventColor"
                                event-more-text="{0} weitere"
                                @click:event="showEvent"
                                @click:more="viewDay"
                                @click:date="viewDay"
                                @change="calendarChanged">
                              </v-calendar>
                            <v-menu
                                v-model="selectedOpen"
                                :close-on-content-click="false"
                                :activator="selectedElement"
                                offset-x
                              >
                                <v-card flat v-if="selectedEvent">
                                  <v-card-title>{{ selectedEvent.name }}</v-card-title>
                                  <v-card-subtitle>
                                      <v-icon small>mdi-calendar</v-icon> {{ $root.render_event_date(selectedEvent.date.start, selectedEvent.date.end, selectedEvent.date.allday) }}
                                      <event-warning-pills :event="selectedEvent.date.event"></event-warning-pills>
                                  </v-card-subtitle>
                                  <v-card-text>
                                    <div><v-icon small>mdi-database</v-icon> {{ selectedEvent.date.event.organization.name }}</div>
                                    <div v-if="selectedEvent.date.event.organizer.name != selectedEvent.date.event.organization.name"><v-icon small>mdi-server</v-icon> {{ selectedEvent.date.event.organizer.name }}</div>
                                    <div><v-icon small>mdi-map-marker</v-icon> {{ selectedEvent.date.event.place.name }}</div>
                                  </v-card-text>

                                  <v-card-actions>
                                    <v-spacer></v-spacer>
                                    <v-btn
                                      text
                                      color="secondary"
                                      @click="selectedOpen = false"
                                    >
                                    {{ $t("shared.close") }}
                                    </v-btn>
                                    <v-btn
                                      text
                                      color="primary"
                                      @click="openEventDate(selectedEvent.date)"
                                    >
                                      {{ $t("shared.view") }}
                                    </v-btn>
                                  </v-card-actions>
                                </v-card>
                              </v-menu>
                        </v-sheet>
                    </v-col>
                </v-row>
        </v-app>
    </template>
  </div>
    `,
  i18n: {
    messages: {
      en: {
        comp: {
          countTitle: "{count} dates",
          maxWarning: "The maximum number of dates was loaded. Shorten the time period or refine the search for better results.",
          today: "Today",
          day: "Day",
          week: "Week",
          month: "Month",
          filter: "Filter",
        },
      },
      de: {
        comp: {
          countTitle: "{count} Termine",
          maxWarning: "Es wurde die maximale Anzahl an Terminen geladen. Verkürze den Zeitraum oder verfeinere die Suche für bessere Ergebnisse.",
          today: "Heute",
          day: "Tag",
          week: "Woche",
          month: "Monat",
          filter: "Filter",
        },
      },
    },
  },
  data: () => ({
    focus: '',
    type: 'month',
    title: "",
    countTitle: "",
    events: [],
    selectedEvent: null,
    selectedElement: null,
    selectedOpen: false,
    isLoading: false,
    maxDates: 200,
    warning: null,
  }),
  mounted () {
    this.$refs.calendar.checkChange();
  },
  methods: {
    parameterChanged() {
      if (this.$refs.calendar) {
          this.loadEvents();
      }
    },
    calendarChanged({ start, end }) {
      $('#date_from').val(start.date);
      $('#date_to').val(end.date);
      this.loadEvents();
    },
    loadEvents(page = 1) {
      $('#page').val(page);
      this.title = this.$refs.calendar.title;

      if (page == 1) {
        this.events = [];
        this.warning = null;
        this.countTitle = "";
      }
      const vm = this;
      axios
          .get(`/api/v1/event-dates/search?` + $("#filter_form").serialize(), {
              withCredentials: true,
              handleLoading: this.handleLoading,
          })
          .then((response) => {
              for (const date of response.data.items) {
                  vm.events.push({
                      name: date.event.name,
                      start: moment(date.start).toDate(),
                      end: date.end != null ? moment(date.end).toDate() : null,
                      timed: !date.allday,
                      date: date,
                      color: vm.$root.event_has_status_info(date.event) ? '#17a2b8' : '#007bff'
                  });
              }

              const count = vm.events.length;
              vm.countTitle = vm.$t('comp.countTitle', { count: count });
              vm.scrollToMinTime();

              if (count >= vm.maxDates) {
                vm.warning = vm.$t('comp.maxWarning');
                return;
              }

              if (response.data.has_next) {
                vm.loadEvents(response.data.next_num);
              }
          });
    },
    viewDay ({ date }) {
      this.focus = date;
      this.type = 'day';
    },
    setToday () {
      this.focus = ''
    },
    openFilter () {
      $('#filterFormModal').modal('show');
    },
    getEventColor (event) {
      return event.color;
    },
    scrollToMinTime() {
        if (!this.$refs.calendar) {
            return;
        }

        if (this.$refs.calendar.type == 'month') {
            return;
        }

        if (this.events.length < 1) {
            return;
        }

        const min_event = this.events.reduce(function(prev, curr) {
            return prev.start.getHours() < curr.start.getHours() ? prev : curr;
        });
        this.$refs.calendar.scrollToTime({ hour: min_event.start.getHours(), minute: 0 });
    },
    showEvent ({ nativeEvent, event }) {
        const open = () => {
            this.selectedEvent = event
            this.selectedElement = nativeEvent.target
            requestAnimationFrame(() => requestAnimationFrame(() => this.selectedOpen = true))
        }

        if (this.selectedOpen) {
            this.selectedOpen = false
            requestAnimationFrame(() => requestAnimationFrame(() => open()))
        } else {
            open()
        }

        nativeEvent.stopPropagation()
    },
    openEventDate(date) {
        const url = `${axios.defaults.baseURL}/eventdate/${date.id}`;
        window.open(url);
    },
    handleLoading(isLoading) {
      this.isLoading = isLoading;
    },
  },
};
