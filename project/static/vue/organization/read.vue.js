const OrganizationRead = {
  template: `
    <div>
      <b-overlay :show="isLoading">
        <div v-if="organization">
          <b-row class="mb-5">
            <b-col v-if="organization.logo" cols="12" sm="auto">
              <figure class="figure mx-5">
                <b-img :src="organization.logo.image_url + '?s=120'" class="figure-img img-fluid" style="max-width:120px;" alt="Logo"></b-img>
              </figure>
            </b-col>
            <b-col cols="12" sm>
              <h1 class="my-0">{{ organization.name }} <template v-if="organization.is_verified"><i class="fa fa-check-circle text-primary"></i></template></h1>
              <div class="mb-3 text-muted">@{{ organization.short_name }}</div>

              <div v-if="organization.url">
                <i class="fa fa-fw fa-link"></i>
                <a :href="organization.url" target="_blank" rel="noopener noreferrer" style="word-break: break-all;">{{ organization.url }}</a>
              </div>

              <div v-if="organization.email">
                <i class="fa fa-fw fa-envelope"></i>
                <a :href="'mailto:' + organization.email">{{ organization.email }}</a>
              </div>

              <div v-if="organization.phone">
                <i class="fa fa-fw fa-phone"></i>
                <a :href="'tel:' + organization.phone">{{ organization.phone }}</a>
              </div>

              <div v-if="organization.fax">
                <i class="fa fa-fw fa-fax"></i>
                {{ organization.fax }}
              </div>

              <div v-if="organization.location && (organization.location.street || organization.location.postalCode || organization.location.city)">
                <i class="fa fa-fw fa-map-marker"></i>
                <template v-if="organization.location.street">{{ organization.location.street }}, </template>
                {{ organization.location.postalCode }} {{ organization.location.city }}
              </div>

              <b-button v-b-modal.modal-ical variant="outline-secondary" class="mt-4">
                <i class="fa fa-fw fa-calendar"></i>
                {{ $t("comp.icalExport") }}
              </b-button>

              <b-modal id="modal-ical" :title="$t('comp.icalExport')" size="lg" ok-only>
                <template #default="{ hide }">
                  <b-input-group class="mb-3">
                    <b-form-input :value="icalUrl" ref="icalInput"></b-form-input>
                  </b-input-group>
                </template>
                <template #modal-footer="{ ok, cancel, hide }">
                  <b-button variant="primary" @click.prevent="copyIcal()">{{ $t('comp.copy') }}</b-button>
                  <b-button variant="secondary" :href="icalUrl">{{ $t('comp.download') }}</b-button>
                  <b-button variant="outline-secondary" @click="hide()">{{ $t("shared.close") }}</b-button>
                </template>
              </b-modal>
            </b-col>
          </b-row>

          <div>
            <iframe id="eventcally-widget" :src="'/' + organization.short_name + '/widget/eventdates'" style="width: 1px; min-width: 100%; max-width:100%;"></iframe>
          </div>
        </div>
      </b-overlay>
    </div>
    `,
  i18n: {
    messages: {
      en: {
        comp: {
          copy: "Copy link",
          download: "Download",
          icalCopied: "Link copied",
          icalExport: "iCal calendar",
        },
      },
      de: {
        comp: {
          copy: "Link kopieren",
          download: "Runterladen",
          icalCopied: "Link kopiert",
          icalExport: "iCal Kalender",
        },
      },
    },
  },
  data: () => ({
    isLoading: false,
    organization: null,
  }),
  computed: {
    organizationId() {
      return this.$route.params.organization_id;
    },
    icalUrl() {
      return `${window.location.origin}/organizations/${this.organizationId}/ical`;
    },
  },
  mounted() {
    this.isLoading = false;
    this.organization = null;
    this.loadData();
  },
  methods: {
    loadData() {
      axios
        .get(`/api/v1/organizations/${this.organizationId}`, {
          withCredentials: true,
          handleLoading: this.handleLoading,
        })
        .then((response) => {
          this.organization = response.data;
          Vue.nextTick(function () {
            iFrameResize({ minHeight: 300, onMessage: function(m) {} }, '#eventcally-widget');
          });
        });
    },
    handleLoading(isLoading) {
      this.isLoading = isLoading;
    },
    copyIcal() {
      this.$refs.icalInput.select();
      document.execCommand("copy");
      this.$root.makeSuccessToast(this.$t("comp.icalCopied"))
    }
  },
};
