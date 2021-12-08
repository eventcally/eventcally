const EventListCreate = {
  template: `
    <div>
      <h1>{{ $t("comp.title") }}</h1>
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
    `,
  i18n: {
    messages: {
      en: {
        comp: {
          title: "Add list",
          successMessage: "List successfully created",
        },
      },
      de: {
        comp: {
          title: "Liste hinzufügen",
          successMessage: "Liste erfolgreich erstellt",
        },
      },
    },
  },
  data: () => ({
    isSubmitting: false,
    form: {
        name: null,
    },
  }),
  computed: {
    adminUnitId() {
      return this.$route.params.admin_unit_id
    },
  },
  mounted() {
    this.form = {
        name: null,
    }
  },
  methods: {
      submitForm() {
        let data = {
            'name': this.form.name,
        };

        axios
          .post(`/api/v1/organizations/${this.adminUnitId}/event-lists`,
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
      this.$root.goBack(`/manage/admin_unit/${this.adminUnitId}/event-lists`)
    },
  }
};
