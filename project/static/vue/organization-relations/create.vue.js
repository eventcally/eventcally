const OrganizationRelationCreate = {
  template: `
    <div>
      <h1>{{ $t("comp.title") }}</h1>
      <ValidationObserver v-slot="{ handleSubmit }">
        <b-form @submit.stop.prevent="handleSubmit(submitForm)">
          <custom-typeahead
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
          <b-button variant="secondary" @click="goBack" v-bind:disabled="isSubmitting">{{ $t("shared.cancel") }}</b-button>
          <b-button variant="primary" type="submit" v-bind:disabled="isSubmitting">
              <b-spinner small v-if="isSubmitting"></b-spinner>
              {{ $t("shared.submit") }}
          </b-button>
        </b-form>
      </ValidationObserver>
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
    isSubmitting: false,
    form: {
        targetOrganization: null,
        auto_verify_event_reference_requests: false
    },
  }),
  computed: {
    adminUnitId() {
      return this.$route.params.admin_unit_id
    },
  },
  mounted() {
    this.form = {
        targetOrganization: null,
        auto_verify_event_reference_requests: false
    }
  },
  methods: {
      submitForm() {
        const data = {
            'auto_verify_event_reference_requests': this.form.auto_verify_event_reference_requests,
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
