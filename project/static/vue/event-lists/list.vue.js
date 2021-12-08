const EventListList = {
  template: `
    <div>
        <h1>{{ $t("shared.models.eventList.listName") }}</h1>

        <div class="my-4">
            <b-button variant="outline-secondary" :to="{ path: 'create'}" append><i class="fa fa-plus"></i> {{ $t("comp.addTitle") }}</b-button>
        </div>

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
              <b-dropdown-item @click.prevent="editItem(data.item.id)">{{ $t("shared.edit") }}&hellip;</b-dropdown-item>
              <b-dropdown-item @click.prevent="deleteItem(data.item.id)">{{ $t("shared.delete") }}&hellip;</b-dropdown-item>
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
          addTitle: "Add list",
          deletedMessage: "List successfully deleted",
          deleteConfirmation: "Do you really want to delete the list?",
        },
      },
      de: {
        comp: {
          addTitle: "Liste hinzufügen",
          deletedMessage: "Liste erfolgreich gelöscht",
          deleteConfirmation: "Möchtest du die Liste wirklich löschen?",
        },
      },
    },
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
  computed: {
    adminUnitId() {
      return this.$route.params.admin_unit_id;
    },
  },
  methods: {
    loadTableData(ctx, callback) {
      const vm = this;
      axios
        .get(`/api/v1/organizations/${this.adminUnitId}/event-lists`, {
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
      this.$router.push({
        path: `/manage/admin_unit/${this.adminUnitId}/event-lists/${id}`,
      });
    },
    editItem(id) {
      this.$router.push({
        path: `/manage/admin_unit/${this.adminUnitId}/event-lists/${id}/update`,
      });
    },
    deleteItem(id) {
      if (confirm(this.$t("comp.deleteConfirmation"))) {
        axios
          .delete(`/api/v1/event-lists/${id}`, {
            withCredentials: true,
          })
          .then(() => {
            this.$root.makeSuccessToast(this.$t("comp.deletedMessage"));
            this.refreshTableData();
          });
      }
    },
  },
};
