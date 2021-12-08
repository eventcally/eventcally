const EventListUpdate = {
  template: `
    <div>
      <h1>{{ $t("comp.title") }}</h1>
      <b-overlay :show="isLoading">
        <div v-if="eventList">
          <ValidationObserver v-slot="{ handleSubmit }">
            <b-form @submit.stop.prevent="handleSubmit(submitForm)">
              <validated-input
                :label="$t('shared.models.eventList.name')"
                name="name"
                v-model="form.name"
                rules="required|min:3" />
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
          title: "Update list",
          successMessage: "List successfully updated",
        },
      },
      de: {
        comp: {
          title: "Liste aktualisieren",
          successMessage: "Liste erfolgreich aktualisiert",
        },
      },
    },
  },
  data: () => ({
    isLoading: false,
    isSubmitting: false,
    eventList: null,
    form: {
      name: null,
    },
  }),
  computed: {
    adminUnitId() {
      return this.$route.params.admin_unit_id;
    },
    eventListId() {
      return this.$route.params.event_list_id;
    },
  },
  mounted() {
    this.isLoading = false;
    this.eventList = null;
    this.form = {
      name: null,
    };
    this.loadFormData();
  },
  methods: {
    loadFormData() {
      axios
        .get(`/api/v1/event-lists/${this.eventListId}`, {
          withCredentials: true,
          handleLoading: this.handleLoading,
        })
        .then((response) => {
          this.eventList = response.data;
          this.form = {
            name: response.data.name,
          };
        });
    },
    handleLoading(isLoading) {
      this.isLoading = isLoading;
    },
    submitForm() {
      let data = {
          'name': this.form.name,
      };

      axios
        .put(`/api/v1/event-lists/${this.eventListId}`, data, {
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
      this.$root.goBack(`/manage/admin_unit/${this.adminUnitId}/event-lists`);
    },
  },
};
