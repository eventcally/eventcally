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
              <validated-switch
                v-if="adminUnit.can_verify_other"
                :label="$t('shared.models.adminUnitRelation.verify')"
                :description="$t('shared.models.adminUnitRelation.verifyDescription')"
                name="verify"
                v-model="form.verify" />
              <validated-switch
                v-if="adminUnit.incoming_reference_requests_allowed"
                :label="$t('shared.models.adminUnitRelation.autoVerifyEventReferenceRequests')"
                :description="$t('shared.models.adminUnitRelation.autoVerifyEventReferenceRequestsDescription')"
                name="auto_verify_event_reference_requests"
                v-model="form.auto_verify_event_reference_requests" />
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
        verify: this.$route.query.verify == "1",
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
            this.loadTarget();
          });
      },
      loadTarget() {
        if (this.$route.query.target == undefined) {
          return;
        }
        axios
          .get(`/api/v1/organizations/${this.$route.query.target}`, {
            withCredentials: true,
          })
          .then((response) => {
            this.form.targetOrganization = {
              id: response.data.id,
              name: response.data.name
            };
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
