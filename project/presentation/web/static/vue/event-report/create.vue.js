const EventReportCreate = {
  template: `
    <div>
      <h1>{{ $t("comp.title") }}</h1>
      <b-overlay :show="isLoading">
        <div>
          <h2 v-if="event"><b-link :href="eventUrl">{{ event.name }}</b-link></h2>
          <ValidationObserver v-slot="{ handleSubmit }" v-if="!isSubmitted">
            <b-form @submit.stop.prevent="handleSubmit(submitForm)">
              <validated-input
                :label="$t('shared.models.eventReport.contactName')"
                :description="$t('shared.models.eventReport.contactNameDescription')"
                name="contactName"
                v-model="form.contactName"
                rules="required|min:5" />
              <validated-input
                :label="$t('shared.models.eventReport.contactEmail')"
                name="contactEmail"
                v-model="form.contactEmail"
                rules="required|email" />
              <validated-textarea
                :label="$t('shared.models.eventReport.message')"
                :description="$t('shared.models.eventReport.messageDescription')"
                name="message"
                v-model="form.message"
                rules="required|min:20" />
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
          title: "Report event",
          successMessage: "Event successfully reported",
        },
      },
      de: {
        comp: {
          title: "Veranstaltung melden",
          successMessage: "Veranstaltung erfolgreich gemeldet",
        },
      },
    },
  },
  data: () => ({
    isLoading: false,
    isSubmitting: false,
    isSubmitted: false,
    event: null,
    form: {
      contactName: "",
      contactEmail: "",
      message: "",
    },
  }),
  computed: {
    eventId() {
      return this.$route.params.event_id;
    },
    eventUrl() {
      return `/event/${this.eventId}`;
    }
  },
  mounted() {
    this.isLoading = false;
    this.event = null;
    this.form = {
      contactName: "",
      contactEmail: "",
      message: "",
    };
    this.isSubmitted = false;
    this.loadFormData();
  },
  methods: {
    loadFormData() {
      axios
        .get(`/api/v1/events/${this.eventId}`, {
          handleLoading: this.handleLoading,
        })
        .then((response) => {
          this.event = response.data;
        });
    },
    handleLoading(isLoading) {
      this.isLoading = isLoading;
    },
    getValidationState({ dirty, validated, valid = null }) {
      return dirty || validated ? valid : null;
    },
    submitForm() {
      const data = {
        contact_name: this.form.contactName,
        contact_email: this.form.contactEmail,
        message: this.form.message,
      };
      axios
        .post(`/api/v1/events/${this.eventId}/reports`, data, {
          handleLoading: this.handleSubmitting,
        })
        .then(() => {
          this.$root.makeSuccessToast(this.$t("comp.successMessage"));
          this.isSubmitted = true;
        });
    },
    handleSubmitting(isLoading) {
      this.isSubmitting = isLoading;
    },
  },
};
