const OrganizationOrganizationInvitationUpdate = {
  template: `
    <div>
      <h1>{{ $t("comp.title") }}</h1>
      <b-overlay :show="isLoading || isLoadingAdminUnit">
        <div v-if="adminUnit && invitation">
        <h2 v-if="invitation">{{ invitation.email }}</h2>
          <ValidationObserver v-slot="{ handleSubmit }">
            <b-form @submit.stop.prevent="handleSubmit(submitForm)">
              <validated-input
                :label="$t('shared.models.adminUnitInvitation.organizationName')"
                name="organizationName"
                v-model="form.organization_name"
                rules="required|uniqueOrganizationName"
                :debounce="500" />
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
          title: "Update invitation",
          successMessage: "Invitation successfully updated",
        },
      },
      de: {
        comp: {
          title: "Einladung aktualisieren",
          successMessage: "Einladung erfolgreich aktualisiert",
        },
      },
    },
  },
  data: () => ({
    isLoading: false,
    isLoadingAdminUnit: false,
    isSubmitting: false,
    invitation: null,
    adminUnit: null,
    form: {
      organization_name: null,
      relation_auto_verify_event_reference_requests: false,
      relation_verify: true,
    },
  }),
  computed: {
    adminUnitId() {
      return this.$route.params.admin_unit_id;
    },
    invitationId() {
      return this.$route.params.organization_invitation_id;
    },
  },
  mounted() {
    this.isLoading = false;
    this.invitation = null;
    this.adminUnit = null;
    this.form = {
      organization_name: null,
      relation_auto_verify_event_reference_requests: false,
      relation_verify: true,
    };
    this.loadFormData();
    this.loadAdminUnit();
  },
  methods: {
    loadFormData() {
      axios
        .get(`/api/v1/organization-invitation/${this.invitationId}`, {
          withCredentials: true,
          handleLoading: this.handleLoading,
        })
        .then((response) => {
          this.invitation = response.data;
          this.form = {
            organization_name: response.data.organization_name,
            relation_auto_verify_event_reference_requests: response.data.relation_auto_verify_event_reference_requests,
            relation_verify: response.data.relation_verify,
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
          'organization_name': this.form.organization_name,
          'relation_auto_verify_event_reference_requests': this.form.relation_auto_verify_event_reference_requests,
          'relation_verify': this.form.relation_verify,
      };

      axios
        .put(`/api/v1/organization-invitation/${this.invitationId}`, data, {
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
      this.$root.goBack(`/manage/admin_unit/${this.adminUnitId}/organization-invitations`);
    },
  },
};
