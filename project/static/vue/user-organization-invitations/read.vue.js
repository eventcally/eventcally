const UserOrganizationInvitationRead = {
  template: `
    <div>
      <h1>{{ $t("comp.title") }}</h1>
      <div class="mt-3 w-normal">
        <b-overlay :show="isLoading">
          <div v-if="invitation">
            <p>{{ $t("comp.instruction", { name: invitation.organization.name }) }}</p>
            <div class="d-flex justify-content-between my-4 decision-container">
              <b-button variant="success" class="m-1" @click="accept()"><i class="fa fa-check"></i> {{ $t("comp.accept") }}&hellip;</b-button>
              <b-button variant="danger" class="m-1" @click="decline()"><i class="fa fa-ban"></i> {{ $t("shared.decline") }}</b-button>
            </div>
          </div>
        </b-overlay>
      </div>
    </div>
    `,
  i18n: {
    messages: {
      en: {
        comp: {
          title: "Invitation",
          instruction: "{name} invited you to create an organization.",
          accept: "Create organization",
          declinedMessage: "Invitation successfully declined",
          declineConfirmation: "Do you really want to decline the invitation?",
        },
      },
      de: {
        comp: {
          title: "Einladung",
          instruction: "{name} hat dich eingeladen, eine Organisation zu erstellen.",
          accept: "Organisation erstellen",
          declinedMessage: "Einladung erfolgreich abgelehnt",
          declineConfirmation: "Möchtest du die Einladung wirklich ablehnen?",
        },
      },
    },
  },
  data: () => ({
    isLoading: false,
    invitation: null,
  }),
  computed: {
    invitationId() {
      return this.$route.params.organization_invitation_id;
    },
  },
  mounted() {
    this.isLoading = false;
    this.invitation = null;
    this.loadData();
  },
  methods: {
    loadData() {
      axios
        .get(`/api/v1/user/organization-invitation/${this.invitationId}`, {
          withCredentials: true,
          handleLoading: this.handleLoading,
        })
        .then((response) => {
          this.invitation = response.data;
        });
    },
    handleLoading(isLoading) {
      this.isLoading = isLoading;
    },
    accept() {
      window.location.href = `/admin_unit/create?invitation_id=${this.invitationId}`;
    },
    decline() {
      if (confirm(this.$t("comp.declineConfirmation"))) {
        axios
          .delete(`/api/v1/user/organization-invitation/${this.invitationId}`, {
            withCredentials: true,
          })
          .then(() => {
            this.$root.makeSuccessToast(this.$t("comp.declinedMessage"));
            this.$root.goBack(`/manage/admin_units`);
          });
      }
    },
  },
};
