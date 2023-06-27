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

              <div v-if="organization.description" class="mt-3">
                <span style="white-space: pre-wrap;">{{ organization.description }}</span>
              </div>

              <div v-if="canRelation" class="mt-3">
                <b-overlay :show="isLoadingRelation">
                  <div>
                    <b-card v-if="relation">
                      <b-card-text>
                        <div v-if="relation.verify">
                          <i class="fa fa-fw fa-check-circle"></i> {{ $t('comp.relationVerify', { source: $root.currentAdminUnit.name, target: organization.name }) }}
                        </div>
                        <div v-if="relation.auto_verify_event_reference_requests">
                          <i class="fa fa-fw fa-check-circle"></i> {{ $t('comp.relationAutoVerifyEventReferenceRequests', { source: $root.currentAdminUnit.name, target: organization.name }) }}
                        </div>
                      </b-card-text>
                      <b-link :href="relationEditUrl">
                        {{ $t("comp.relationEdit") }}
                      </b-link>
                    </b-card>

                    <template v-if="relationDoesNotExist">
                      <b-card v-if="organization.is_verified">
                        <b-card-text>
                          {{ $t('comp.relationDoesNotExist', { source: $root.currentAdminUnit.name, target: organization.name }) }}
                        </b-card-text>
                        <b-link :href="relationCreateUrl">
                          {{ $t("comp.relationCreate") }}
                        </b-link>
                      </b-card>

                      <b-card v-else border-variant="warning">
                        <b-card-text>
                          {{ $t("comp.organizationNotVerified", { organization: organization.name }) }}
                        </b-card-text>
                        <b-link :href="relationCreateUrl">
                          {{ $t("comp.relationCreateToVerify", { organization: organization.name }) }}
                        </b-link>
                      </b-card>
                    </template>
                  </div>
                </b-overlay>
              </div>

              <b-list-group class="mt-4">
                <b-list-group-item :href="'/eventdates?admin_unit_id=' + organization.id">
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
                  <b-button variant="outline-info" :href="icalDocsUrl" target="_blank" rel="noopener noreferrer" v-if="icalDocsUrl">{{ $t('shared.docs') }}</b-button>
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
          organizationNotVerified: "{organization} is not verified",
          relationVerify: "{source} verifies {target}",
          relationAutoVerifyEventReferenceRequests: "{source} verifies reference requests from {target} automatically",
          relationDoesNotExist: "There is no relation from {source} to {target}",
          relationEdit: "Edit relation",
          relationCreate: "Create relation",
          relationCreateToVerify: "Verify {organization}",
        },
      },
      de: {
        comp: {
          copy: "Link kopieren",
          download: "Runterladen",
          icalCopied: "Link kopiert",
          icalExport: "iCal Kalender",
          organizationNotVerified: "{organization} ist nicht verifiziert",
          relationVerify: "{source} verifiziert {target}",
          relationAutoVerifyEventReferenceRequests: "{source} verifiziert Empfehlungsanfragen von {target} automatisch",
          relationDoesNotExist: "Es besteht keine Beziehung von {source} zu {target}",
          relationEdit: "Beziehung bearbeiten",
          relationCreate: "Beziehung erstellen",
          relationCreateToVerify: "Verifiziere {organization}",
        },
      },
    },
  },
  data: () => ({
    isLoading: false,
    isLoadingRelation: false,
    organization: null,
    relation: null,
    canRelation: false,
    relationDoesNotExist: false,
  }),
  computed: {
    organizationId() {
      return this.$route.params.organization_id;
    },
    icalUrl() {
      return `${window.location.origin}/organizations/${this.organizationId}/ical`;
    },
    icalDocsUrl() {
      return this.$root.docsUrl ? `${this.$root.docsUrl}/goto/ical-calendar` : null;
    },
    relationEditUrl() {
      return `/manage/admin_unit/${this.$root.currentAdminUnit.id}/relations/${this.relation.id}/update`;
    },
    relationCreateUrl() {
      return `/manage/admin_unit/${this.$root.currentAdminUnit.id}/relations/create?target=${this.organizationId}&verify=1`;
    },
  },
  mounted() {
    this.isLoading = false;
    this.isLoadingRelation = false;
    this.organization = null;
    this.relation = null;
    this.canRelation = this.$root.has_access("admin_unit:update");
    this.relationDoesNotExist = false;
    this.loadData();
    this.loadRelationData();
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
        });
    },
    loadRelationData() {
      if (!this.$root.hasOwnProperty("currentAdminUnit")) {
        return;
      }
      if (this.$root.currentAdminUnit.id == this.organizationId) {
        return;
      }
      const vm = this;
      axios
        .get(`/api/v1/organizations/${this.$root.currentAdminUnit.id}/relations/outgoing/${this.organizationId}`, {
          withCredentials: true,
          handleLoading: this.handleLoadingRelation,
          handler: {
            handleLoading: function(isLoading) {
                vm.isLoadingRelation = isLoading;
            },
            handleRequestError: function(error, message) {
              const status = error && error.response && error.response.status;
              if (status == 404) {
                vm.relationDoesNotExist = true;
                return;
              }
              this.$root.makeErrorToast(message);
            }
          }
        })
        .then((response) => {
          this.relation = response.data;
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
