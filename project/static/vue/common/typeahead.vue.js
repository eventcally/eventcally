const CustomTypeahead = {
  template: `
    <div>
        <validation-provider
            :name="label"
            :detectInput="false"
            ref="validationProvider"
            rules="required"
            v-slot="validationContext">
          <b-form-group :label="label">
            <vue-typeahead-bootstrap
              v-model="query"
              :data="suggestions"
              :minMatchingChars="1"
              :disableSort="true"
              :showAllResults="true"
              :placeholder="$t('shared.autocomplete.instruction')"
              :inputClass="getInputClass(validationContext)"
              @hit="selected = $event"
              @input="onInput"
              v-bind="$attrs" />
            <b-form-invalid-feedback
              :state="getValidationState(validationContext)">
              {{ validationContext.errors[0] }}
            </b-form-invalid-feedback>
          </b-form-group>
      </validation-provider>
    </div>
    `,
  props: {
    value: {
      type: null
    },
    fetchURL: {
      type: String
    },
    labelKey: {
      type: String
    },
  },
  data: () => ({
    query: '',
    suggestions: [],
    selected: null,
  }),
  computed: {
    label() {
      return this.$t(this.labelKey)
    },
  },
  methods: {
    getValidationState({ dirty, validated, valid = null }) {
      return dirty || validated ? valid : null;
    },
    getInputClass({ dirty, validated, valid = null }) {
      if (dirty || !validated) {
        return "";
      }

      return valid ? "is-valid" : "is-invalid";
    },
    fetchData(query) {
      const vm = this
      axios
          .get(this.fetchURL.replace('{query}', escape(query)))
          .then(response => {
              vm.suggestions = response.data.items
          })
    },
    fetchDataDebounced: _.debounce(function(query) { this.fetchData(query) }, 1000),
    onInput() {
      this.selected = null;
      this.fetchDataDebounced(this.query)
    },
  },
  mounted() {
    this.$refs.validationProvider.syncValue(this.selected)
  },
  watch: {
    selected(newVal) {
      this.$emit("input", newVal)
      this.$refs.validationProvider.syncValue(newVal)
      this.$refs.validationProvider.validate()
    }
  }
};
