const EventImport = {
  template: `
    <div>
      <h1>{{ $t("comp.title") }}</h1>
      <ValidationObserver v-slot="{ handleSubmit }">
        <b-form @submit.stop.prevent="handleSubmit(submitForm)">
          <validated-input
            :label="$t('comp.url')"
            name="url"
            v-model="form.url"
            rules="required|url" />
          <b-form-group v-slot="{ ariaDescribedby }">
            <b-form-radio v-model="form.publicStatus" :aria-describedby="ariaDescribedby" value="draft">{{ $t("comp.draft") }}</b-form-radio>
            <b-form-radio v-model="form.publicStatus" :aria-describedby="ariaDescribedby" value="planned">{{ $t("comp.planned") }}</b-form-radio>
            <b-form-radio v-model="form.publicStatus" :aria-describedby="ariaDescribedby" value="published">{{ $t("comp.published") }}</b-form-radio>
          </b-form-group>
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
          title: "Import event",
          url: "URL",
          published: "Publish event",
          planned: "Save as planned",
          draft: "Save as draft",
          importError: "Unfortunately, no event could be imported from the URL.",
        },
      },
      de: {
        comp: {
          title: "Veranstaltung importieren",
          url: "URL",
          published: "Veranstaltung veröffentlichen",
          planned: "Als geplant speichern",
          draft: "Als Entwurf speichern",
          importError: "Von der URL konnte leider keine Veranstaltung importiert werden."
        },
      },
    },
  },
  data: () => ({
    isSubmitting: false,
    form: {
        name: null,
        publicStatus: "draft",
    },
  }),
  computed: {
    adminUnitId() {
      return this.$route.params.admin_unit_id
    },
  },
  mounted() {
    this.form = {
        url: null,
        publicStatus: "draft",
    }
  },
  methods: {
      submitForm() {
        let data = {
            'url': this.form.url,
            'public_status': this.form.publicStatus,
        };

        axios
          .post(`/api/v1/organizations/${this.adminUnitId}/events/import`,
            data,
            {
              withCredentials: true,
              handler: this,
              handleLoading: this.handleSubmitting,
            })
          .then((response) => {
            window.location.href = `/event/${response.data.id}`;
          })
    },
    handleSubmitting(isLoading) {
        this.isSubmitting = isLoading;
    },
    handleRequestError(error, message) {
      let customMessage = message;

      if (error.response.status == 422) {
        customMessage = this.$t("comp.importError");
      }

      this.$root.makeErrorToast(customMessage);
    }
  }
};
