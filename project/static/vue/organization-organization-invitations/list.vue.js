const OrganizationOrganizationInvitationList = {
  template: `
    <div>
        <h1>{{ $t("comp.title") }}</h1>

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
          style="min-height:100px"
        >
          <template #cell(email)="data">
            <b-dropdown :id="'item-dropdown-' + data.item.id" :text="data.value" variant="link" toggle-class="m-0 p-0">
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
          title: "Invitations",
          addTitle: "Add invitation",
          deletedMessage: "Invitation successfully deleted",
          deleteConfirmation: "Do you really want to delete the invitation?",
        },
      },
      de: {
        comp: {
          title: "Einladungen",
          addTitle: "Einladung hinzufügen",
          deletedMessage: "Einladung erfolgreich gelöscht",
          deleteConfirmation: "Möchtest du die Einladung wirklich löschen?",
        },
      },
    },
  },
  data: () => ({
    errorMessage: null,
    fields: [
      {
        key: "email",
        label: i18n.t("shared.models.adminUnitInvitation.email"),
      },
      {
        key: "organization_name",
        label: i18n.t("shared.models.adminUnitInvitation.organizationName"),
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
        .get(`/api/v1/organizations/${this.adminUnitId}/organization-invitations`, {
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
    editItem(id) {
      this.$router.push({
        path: `/manage/admin_unit/${this.adminUnitId}/organization-invitations/${id}/update`,
      });
    },
    deleteItem(id) {
      if (confirm(this.$t("comp.deleteConfirmation"))) {
        axios
          .delete(`/api/v1/organization-invitation/${id}`, {
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
