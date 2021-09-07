const OrganizationRelationUpdate = {
  template: `
    <div>
      <h1>{{ $t("comp.title") }}</h1>
      <b-overlay :show="isLoading">
        <div>
          <h2 v-if="relation">{{ relation.source_organization.name }}</h2>
          <ValidationObserver v-slot="{ handleSubmit }">
            <b-form @submit.stop.prevent="handleSubmit(submitForm)">
              <b-form-group>
                  <b-form-checkbox switch id="auto_verify_event_reference_requests" v-model="form.auto_verify_event_reference_requests">
                    {{ $t("shared.models.adminUnitRelation.autoVerifyEventReferenceRequests") }}
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
    isSubmitting: false,
    relation: null,
    form: {
      auto_verify_event_reference_requests: false,
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
    this.form = {
      auto_verify_event_reference_requests: false,
    };
    this.loadFormData();
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
          };
        });
    },
    handleLoading(isLoading) {
      this.isLoading = isLoading;
    },
    submitForm() {
      const data = {
        auto_verify_event_reference_requests: this.form.auto_verify_event_reference_requests,
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
