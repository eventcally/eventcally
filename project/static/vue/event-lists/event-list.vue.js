const EventListEventList = {
  template: `
    <div>
        <div class="alert alert-danger" role="alert" v-if="errorMessage">
            {{ errorMessage }}
        </div>

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
          style="min-height:120px"
        >
          <template #cell(name)="data">
            <b-dropdown :id="'item-dropdown-' + data.item.id" :text="data.value" variant="link" toggle-class="m-0 p-0">
              <b-dropdown-item @click.prevent="viewItem(data.item.id)">{{ $t("shared.view") }}&hellip;</b-dropdown-item>
              <b-dropdown-item @click.prevent="removeItem(data.item.id)">{{ $t("shared.remove") }}&hellip;</b-dropdown-item>
            </b-dropdown>
          </template>
        </b-table>
        <b-pagination v-if="totalRows > 0"
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
          removedMessage: "Event successfully removed",
          removeConfirmation: "Do you really want to remove the event?",
        },
      },
      de: {
        comp: {
          removedMessage: "Veranstaltung erfolgreich entfernt",
          removeConfirmation: "Möchtest du die Veranstaltung wirklich entfernen?",
        },
      },
    },
  },
  data: () => ({
    errorMessage: null,
    fields: [
      {
        key: "name",
        label: i18n.t("shared.models.event.name"),
      },
    ],
    totalRows: 0,
    currentPage: 1,
    perPage: 10,
    searchResult: {
      items: [],
    },
  }),
  computed: {
    eventListId() {
      return this.$route.params.event_list_id;
    },
  },
  methods: {
    loadTableData(ctx, callback) {
      const vm = this;
      axios
        .get(`/api/v1/event-lists/${this.eventListId}/events`, {
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
    viewItem(id) {
      window.location.href = `/event/${id}`;
    },
    removeItem(id) {
      if (confirm(this.$t("comp.removeConfirmation"))) {
        axios
          .delete(`/api/v1/event-lists/${this.eventListId}/events/${id}`, {
            withCredentials: true,
          })
          .then(() => {
            this.$root.makeSuccessToast(this.$t("comp.removedMessage"));
            this.refreshTableData();
          });
      }
    },
  },
};
