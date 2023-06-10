const OrganizationList = {
  template: `
    <div>
        <h1>{{ $t("shared.models.adminUnit.listName") }}</h1>

        <div class="alert alert-danger" role="alert" v-if="errorMessage">
            {{ errorMessage }}
        </div>

        <b-form-group>
          <b-form-input
            id="filter-input"
            v-model="filter"
            type="search"
            :placeholder="$t('shared.autocomplete.instruction')"
            debounce="500"
          ></b-form-input>
        </b-form-group>

        <b-table
          ref="table"
          id="main-table"
          :fields="fields"
          :items="loadTableData"
          :filter="filter"
          :current-page="currentPage"
          :per-page="perPage"
          primary-key="id"
          thead-class="d-none"
          outlined
          hover
          responsive
          show-empty
          :empty-text="$t('shared.emptyData')"
          :empty-filtered-text="$t('shared.emptyData')"
          style="min-height:100px"
        >
          <template #cell(name)="data">
            <b-link :to="{ name: 'OrganizationById', params: { organization_id: data.item.id } }">
              <div>{{ data.item.name }}</div>
              <div class="text-muted">@{{ data.item.short_name }}</div>
            </b-link>
          </template>
        </b-table>
        <total-pagination
          v-model="currentPage"
          :per-page="perPage"
          :totalPages="totalPages"
          :totalRows="totalRows"
          aria-controls="main-table">
        </total-pagination>
    </div>
    `,
  data: () => ({
    errorMessage: null,
    fields: [
      {
        key: "name",
        label: i18n.t("shared.models.adminUnit.name"),
      },
    ],
    filter: null,
    currentPage: 1,
    perPage: 10,
    totalPages: 0,
    totalRows: 0,
    searchResult: {
      items: [],
    },
  }),
  watch: {
    filter(newVal) {
      this.currentPage = 1;
    }
  },
  methods: {
    loadTableData(ctx, callback) {
      const vm = this;
      axios
        .get(`/api/v1/organizations`, {
          params: {
            page: ctx.currentPage,
            per_page: ctx.perPage,
            keyword: ctx.filter,
          },
          withCredentials: true,
          handler: this,
        })
        .then((response) => {
          vm.totalRows = response.data.total;
          vm.totalPages = response.data.pages;
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
  },
};
