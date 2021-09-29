const OrganizationRelationCreate = {
  template: `
    <div>
      <h1>{{ $t("comp.title") }}</h1>
      <b-overlay :show="isLoadingAdminUnit">
        <div v-if="adminUnit">
          <ValidationObserver v-slot="{ handleSubmit }">
            <b-form @submit.stop.prevent="handleSubmit(submitForm)">
              <custom-typeahead
                id="targetOrganization"
                v-model="form.targetOrganization"
                fetchURL="/api/v1/organizations?keyword={query}"
                labelKey="shared.models.adminUnitRelation.targetOrganization"
                :serializer="i => i.name"
              />
              <b-form-group>
                  <b-form-checkbox switch id="auto_verify_event_reference_requests" v-model="form.auto_verify_event_reference_requests">
                    {{ $t("shared.models.adminUnitRelation.autoVerifyEventReferenceRequests") }}
                  </b-form-checkbox>
              </b-form-group>
              <b-form-group v-if="adminUnit.can_verify_other">
                  <b-form-checkbox switch id="verify" v-model="form.verify">
                    {{ $t("shared.models.adminUnitRelation.verify") }}
                  </b-form-checkbox>
              </b-form-group>
              <b-button variant="secondary" @click="goBack" v-bind:disabled="isSubmitting">{{ $t("shared.cancel") }}</b-button>
              <b-button variant="primary" type="submit" v-bind:disabled="isSubmitting">
                  <b-spinner small v-if="isSubmitting"></b-spinner>
                  {{ $t("shared.submit") }}
              </b-button>
            </b-form>
          </ValidationObserver>
        </div>
      </b-overlay>
    </div>
    `,
  i18n: {
    messages: {
      en: {
        comp: {
          title: "Add relation",
          successMessage: "Relation successfully created",
        },
      },
      de: {
        comp: {
          title: "Beziehung hinzufügen",
          successMessage: "Beziehung erfolgreich erstellt",
        },
      },
    },
  },
  data: () => ({
    isLoadingAdminUnit: false,
    isSubmitting: false,
    adminUnit: null,
    form: {
        targetOrganization: null,
        auto_verify_event_reference_requests: false,
        verify: false,
    },
  }),
  computed: {
    adminUnitId() {
      return this.$route.params.admin_unit_id
    },
  },
  mounted() {
    this.isLoadingAdminUnit = false;
    this.adminUnit = null;
    this.form = {
        targetOrganization: null,
        auto_verify_event_reference_requests: false,
        verify: false,
    }
    this.loadAdminUnit();
  },
  methods: {
      loadAdminUnit() {
        axios
          .get(`/api/v1/organizations/${this.adminUnitId}`, {
            withCredentials: true,
            handleLoading: this.handleLoadingAdminUnit,
          })
          .then((response) => {
            this.adminUnit = response.data;
          });
      },
      handleLoadingAdminUnit(isLoading) {
        this.isLoadingAdminUnit = isLoading;
      },
      submitForm() {
        let data = {
            'auto_verify_event_reference_requests': this.form.auto_verify_event_reference_requests,
            'verify': this.form.verify,
            'target_organization': {
                'id': this.form.targetOrganization.id
            }
        }

        axios
          .post(`/api/v1/organizations/${this.adminUnitId}/relations/outgoing`,
            data,
            {
              withCredentials: true,
              handleLoading: this.handleSubmitting,
            })
          .then(() => {
            this.$root.makeSuccessToast(this.$t("comp.successMessage"))
            this.goBack()
          })
    },
    handleSubmitting(isLoading) {
        this.isSubmitting = isLoading;
    },
    goBack() {
      this.$root.goBack(`/manage/admin_unit/${this.adminUnitId}/relations`)
    },
  }
};
