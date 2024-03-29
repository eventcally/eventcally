const OrganizationRelationUpdate = {
  template: `
    <div>
      <h1>{{ $t("comp.title") }}</h1>
      <b-overlay :show="isLoading || isLoadingAdminUnit">
        <div v-if="adminUnit && relation">
          <h2 v-if="relation">{{ relation.target_organization.name }}</h2>
          <ValidationObserver v-slot="{ handleSubmit }">
            <b-form @submit.stop.prevent="handleSubmit(submitForm)">
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
          title: "Update relation",
          successMessage: "Relation successfully updated",
        },
      },
      de: {
        comp: {
          title: "Beziehung aktualisieren",
          successMessage: "Beziehung erfolgreich aktualisiert",
        },
      },
    },
  },
  data: () => ({
    isLoading: false,
    isLoadingAdminUnit: false,
    isSubmitting: false,
    relation: null,
    adminUnit: null,
    form: {
      auto_verify_event_reference_requests: false,
      verify: false,
    },
  }),
  computed: {
    adminUnitId() {
      return this.$route.params.admin_unit_id;
    },
    relationId() {
      return this.$route.params.relation_id;
    },
  },
  mounted() {
    this.isLoading = false;
    this.relation = null;
    this.adminUnit = null;
    this.form = {
      auto_verify_event_reference_requests: false,
      verify: false,
    };
    this.loadFormData();
    this.loadAdminUnit();
  },
  methods: {
    loadFormData() {
      axios
        .get(`/api/v1/organization-relation/${this.relationId}`, {
          withCredentials: true,
          handleLoading: this.handleLoading,
        })
        .then((response) => {
          this.relation = response.data;
          this.form = {
            auto_verify_event_reference_requests: response.data.auto_verify_event_reference_requests,
            verify: response.data.verify,
          };
        });
    },
    handleLoading(isLoading) {
      this.isLoading = isLoading;
    },
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
        auto_verify_event_reference_requests: this.form.auto_verify_event_reference_requests,
        verify: this.form.verify,
      };

      axios
        .put(`/api/v1/organization-relation/${this.relationId}`, data, {
          withCredentials: true,
          handleLoading: this.handleSubmitting,
        })
        .then(() => {
          this.$root.makeSuccessToast(this.$t("comp.successMessage"));
          this.goBack();
        });
    },
    handleSubmitting(isLoading) {
      this.isSubmitting = isLoading;
    },
    goBack() {
      this.$root.goBack(`/manage/admin_unit/${this.adminUnitId}/relations`);
    },
  },
};
