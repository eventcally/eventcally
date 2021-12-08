const EventListAddEvent = {
  template: `
    <div>
        <p>{{ $t("comp.instruction") }}</p>
        <b-table
          ref="table"
          id="main-table"
          :fields="fields"
          :items="loadTableData"
          :current-page="currentPage"
          :per-page="perPage"
          primary-key="id"
          thead-class="d-none"
          outlined
          hover
          responsive
          show-empty
          :empty-text="$t('shared.emptyData')"
          style="min-height:100px"
          @row-clicked="rowClicked"
        >
        <template #cell(name)="data">
          <i class="fa fa-fw" :class="{ 'fa-check': data.item.contains_event }"></i> {{ data.item.event_list.name }}
        </template>
        </b-table>
        <b-pagination v-if="totalRows > perPage"
          v-model="currentPage"
          :total-rows="totalRows"
          :per-page="perPage"
          aria-controls="main-table"
        ></b-pagination>
    </div>
    `,
  i18n: {
    messages: {
      en: {
        comp: {
          instruction: "You can add and modify lists at Events > Event list.",
          addedMessage: "Event was added to list",
          removedMessage: "Event was removed list",
        },
      },
      de: {
        comp: {
          instruction: "Du kannst Listen unter Veranstaltungen > Veranstaltungslisten hinzufügen und ändern.",
          addedMessage: "Veranstaltung wurde der Liste hinzugefügt",
          removedMessage: "Veranstaltung wurde von der Liste entfernt",
        },
      },
    },
  },
  props: {
    eventId: {
      type: String
    },
    organizationId: {
      type: String
    }
  },
  data: () => ({
    errorMessage: null,
    fields: [
      {
        key: "name",
        label: i18n.t("shared.models.eventList.name"),
      },
    ],
    totalRows: 0,
    currentPage: 1,
    perPage: 10,
    searchResult: {
      items: [],
    },
  }),
  methods: {
    loadTableData(ctx, callback) {
      const vm = this;
      axios
        .get(`/api/v1/organizations/${this.organizationId}/event-lists/status/${this.eventId}`, {
          params: {
            page: ctx.currentPage,
            per_page: ctx.perPage,
          },
          withCredentials: true,
          handler: this,
        })
        .then((response) => {
          vm.totalRows = response.data.total;
          callback(response.data.items);
        })
        .catch(() => {
          callback([]);
        });
      return null;
    },
    refreshTableData() {
      this.$refs.table.refresh();
    },
    handleRequestStart() {
      this.errorMessage = null;
    },
    handleRequestError(error, message) {
      this.errorMessage = message;
    },
    rowClicked(status, index) {
      const eventList = status.event_list;
      const url = `/api/v1/event-lists/${eventList.id}/events/${this.eventId}`;

      if (status.contains_event) {
        axios.delete(url, {
          withCredentials: true,
        })
        .then(() => {
          this.$root.makeSuccessToast(this.$t("comp.removedMessage"));
          status.contains_event = false;
        });
      } else {
        axios.put(url, {
            withCredentials: true,
          })
          .then(() => {
            this.$root.makeSuccessToast(this.$t("comp.addedMessage"));
            status.contains_event = true;
          });
      }
    },
  },
};
