const WidgetConfiguratorList = {
  template: `
    <div>
        <h1>{{ $t("shared.models.customWidget.listName") }}</h1>

        <div class="my-4">
            <b-button variant="outline-secondary" @click.prevent="createItem()"><i class="fa fa-plus"></i> {{ $t("comp.addTitle") }}</b-button>
        </div>

        <div class="alert alert-danger" role="alert" v-if="errorMessage">
            {{ errorMessage }}
        </div>

        <b-modal id="custom-widget-installation-modal" title="Installation" size="lg" ok-only>
          <p>Kopiere den unten stehenden Code und füge ihn auf deiner Website ein.</p>
          <p>Füge den folgenden Code im <code>&lt;head&gt;</code> der Seite ein.</p>

          <b-form-textarea rows="3" max-rows="8" size="sm" disabled class="text-monospace" style="font-size: 0.7rem;" v-model="installationHeader"></b-form-textarea>
          <p class="mt-3">Füge den folgenden Code an der Stelle im <code>&lt;body&gt;</code> der Seite ein, wo das Widget dargestellt werden soll.</p>
          <b-form-textarea rows="1" max-rows="8" size="sm" disabled class="text-monospace" style="font-size: 0.7rem;" v-model="installationBody"></b-form-textarea>
        </b-modal>

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
              <b-dropdown-item @click.prevent="installItem(data.item.id)">{{ $t("comp.installation") }}&hellip;</b-dropdown-item>
              <b-dropdown-item @click.prevent="editItem(data.item.id)">{{ $t("shared.edit") }}&hellip;</b-dropdown-item>
              <b-dropdown-item @click.prevent="deleteItem(data.item.id)">{{ $t("shared.delete") }}&hellip;</b-dropdown-item>
            </b-dropdown>
          </template>
          <template #cell(widget_type)="data">
            {{ widgetTypes[data.value] }}
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
          addTitle: "Add widget",
          installation: "Installation",
          deletedMessage: "Widget successfully deleted",
          deleteConfirmation: "Do you really want to delete the widget?",
        },
      },
      de: {
        comp: {
          addTitle: "Widget hinzufügen",
          installation: "Installation",
          deletedMessage: "Widget erfolgreich gelöscht",
          deleteConfirmation: "Möchtest du das Widget wirklich löschen?",
        },
      },
    },
  },
  data: () => ({
    errorMessage: null,
    fields: [
      {
        key: "name",
        label: i18n.t("shared.models.customWidget.name"),
      },
      {
        key: "widget_type",
        label: i18n.t("shared.models.customWidget.widgetType"),
      },
    ],
    totalRows: 0,
    currentPage: 1,
    perPage: 10,
    searchResult: {
      items: [],
    },
    widgetTypes: {
      "search": "Search",
      "calendar": "Calendar",
    },
    installationWidgetId: 0,
  }),
  computed: {
    organizationId() {
      return this.$route.params.organization_id;
    },
    installationHeader() {
      return "<!-- Event calendar widget -->\n<script>(function(w,d,s,o,f,js,fjs){w['GsevptWidget']=o;w[o]=w[o]||function(){(w[o].q=w[o].q||[]).push(arguments)};js=d.createElement(s),fjs=d.getElementsByTagName(s)[0];js.id=o;js.src=f;js.async=1;fjs.parentNode.insertBefore(js,fjs);}(window,document,'script','gsevpt','" + window.location.origin  + "/static/widget-loader.js'));</script>\n<!-- End event calendar widget -->";
    },
    installationBody() {
      return '<div class="gsevpt-widget" data-widget-id="' + this.installationWidgetId + '"></div>';
    }
  },
  mounted() {
    this.widgetTypes["search"] = this.$t("shared.models.customWidget.widgetTypeSearch");
    this.widgetTypes["calendar"] = this.$t("shared.models.customWidget.widgetTypeCalendar");
  },
  methods: {
    loadTableData(ctx, callback) {
      const vm = this;
      axios
        .get(`/api/v1/organizations/${this.organizationId}/custom-widgets`, {
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
    createItem() {
      window.location.href = `/manage/admin_unit/${this.organizationId}/custom-widgets/create`;
    },
    editItem(id) {
      window.location.href = `/manage/admin_unit/${this.organizationId}/custom-widgets/${id}/update`;
    },
    deleteItem(id) {
      if (confirm(this.$t("comp.deleteConfirmation"))) {
        axios
          .delete(`/api/v1/custom-widgets/${id}`, {
            withCredentials: true,
          })
          .then(() => {
            this.$root.makeSuccessToast(this.$t("comp.deletedMessage"));
            this.refreshTableData();
          });
      }
    },
    installItem(id) {
      this.installationWidgetId = id;
      this.$bvModal.show("custom-widget-installation-modal");
    },
  },
};
