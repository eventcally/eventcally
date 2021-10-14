const OrganizationOrganizationInvitationCreate = {
  template: `
    <div>
      <h1>{{ $t("comp.title") }}</h1>
      <b-overlay :show="isLoadingAdminUnit">
        <div v-if="adminUnit">
          <ValidationObserver v-slot="{ handleSubmit }">
            <b-form @submit.stop.prevent="handleSubmit(submitForm)">
              <validated-input
                :label="$t('shared.models.adminUnitInvitation.email')"
                :description="$t('shared.models.adminUnitInvitation.emailDescription')"
                name="email"
                v-model="form.email"
                rules="required|email" />
              <validated-input
                :label="$t('shared.models.adminUnitInvitation.organizationName')"
                name="organizationName"
                v-model="form.organization_name"
                rules="required" />
              <validated-switch
                v-if="adminUnit.can_verify_other"
                :label="$t('shared.models.adminUnitInvitation.relationVerify')"
                :description="$t('shared.models.adminUnitInvitation.relationVerifyDescription')"
                name="relationVerify"
                v-model="form.relation_verify" />
              <validated-switch
                v-if="adminUnit.incoming_reference_requests_allowed"
                :label="$t('shared.models.adminUnitInvitation.relationAutoVerifyEventReferenceRequests')"
                :description="$t('shared.models.adminUnitInvitation.relationAutoVerifyEventReferenceRequestsDescription')"
                name="relationAutoVerifyEventReferenceRequests"
                v-model="form.relation_auto_verify_event_reference_requests" />
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
          title: "Add invitation",
          successMessage: "Invitation successfully created",
        },
      },
      de: {
        comp: {
          title: "Einladung hinzufügen",
          successMessage: "Einladung erfolgreich erstellt",
        },
      },
    },
  },
  data: () => ({
    isLoadingAdminUnit: false,
    isSubmitting: false,
    adminUnit: null,
    form: {
        email: null,
        organization_name: null,
        relation_auto_verify_event_reference_requests: false,
        relation_verify: true,
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
        email: null,
        organization_name: null,
        relation_auto_verify_event_reference_requests: false,
        relation_verify: true,
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
            'email': this.form.email,
            'organization_name': this.form.organization_name,
            'relation_auto_verify_event_reference_requests': this.form.relation_auto_verify_event_reference_requests,
            'relation_verify': this.form.relation_verify,
        };

        axios
          .post(`/api/v1/organizations/${this.adminUnitId}/organization-invitations`,
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
      this.$root.goBack(`/manage/admin_unit/${this.adminUnitId}/organization-invitations`)
    },
  }
};
