const OrganizerRead = {
  template: `
    <div class="w-normal">
      <b-overlay :show="isLoading">
        <div v-if="organizer">
          <b-row class="mb-5">
            <b-col v-if="organizer.logo" cols="12" sm="auto">
              <figure class="figure mx-5">
                <b-img :src="organizer.logo.image_url + '?s=120'" class="figure-img img-fluid" style="max-width:120px;" alt="Logo"></b-img>
              </figure>
            </b-col>
            <b-col cols="12" sm>
              <h1 class="my-0">{{ organizer.name }}</h1>

              <div v-if="organizer.url">
                <i class="fa fa-fw fa-link"></i>
                <a :href="organizer.url" target="_blank" rel="noopener noreferrer" style="word-break: break-all;">{{ organizer.url }}</a>
              </div>

              <div v-if="organizer.email">
                <i class="fa fa-fw fa-envelope"></i>
                <a :href="'mailto:' + organizer.email">{{ organizer.email }}</a>
              </div>

              <div v-if="organizer.phone">
                <i class="fa fa-fw fa-phone"></i>
                <a :href="'tel:' + organizer.phone">{{ organizer.phone }}</a>
              </div>

              <div v-if="organizer.fax">
                <i class="fa fa-fw fa-fax"></i>
                {{ organizer.fax }}
              </div>

              <div v-if="organizer.location && (organizer.location.street || organizer.location.postalCode || organizer.location.city)">
                <i class="fa fa-fw fa-map-marker"></i>
                <template v-if="organizer.location.street">{{ organizer.location.street }}, </template>
                {{ organizer.location.postalCode }} {{ organizer.location.city }}
              </div>

              <div v-if="organizer.organization">
                <a :href="'/organizations/' + organizer.organization.id">{{ organizer.organization.name }}</a>
              </div>

              <b-list-group class="mt-4">
                <b-list-group-item :href="'/eventdates?organizer_id=' + organizer.id">
                  <i class="fa fa-fw fa-list"></i>
                  {{ $t("shared.models.event.listName") }}
                </b-list-group-item>
                <b-list-group-item button v-b-modal.modal-ical>
                  <i class="fa fa-fw fa-calendar"></i>
                  {{ $t("comp.icalExport") }}
                </b-list-group-item>
              </b-list-group>

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
    organizer: null,
  }),
  computed: {
    organizerId() {
      return this.$route.params.organizer_id;
    },
    icalUrl() {
      return `${window.location.origin}/organizers/${this.organizerId}/ical`;
    },
  },
  mounted() {
    this.isLoading = false;
    this.organizer = null;
    this.loadData();
  },
  methods: {
    loadData() {
      axios
        .get(`/api/v1/organizers/${this.organizerId}`, {
          withCredentials: true,
          handleLoading: this.handleLoading,
        })
        .then((response) => {
          this.organizer = response.data;
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
