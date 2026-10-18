const ValidatedSwitch = {
  template: `
    <div>
      <ValidationProvider :vid="vid" :name="$attrs.label" :rules="rules" v-slot="validationContext">
        <b-form-group v-bind="$attrs" label="">
          <b-form-checkbox switch
            v-model="innerValue"
            v-bind="$attrs"
            :state="getValidationState(validationContext)"
          >
            {{ $attrs.label }}
          </b-form-checkbox>
          <b-form-invalid-feedback :state="getValidationState(validationContext)">
            {{ validationContext.errors[0] }}
          </b-form-invalid-feedback>
        </b-form-group>
      </ValidationProvider>
    </div>
    `,
  props: {
    vid: {
      type: String
    },
    rules: {
      type: [Object, String],
      default: ""
    },
    value: {
      type: null
    }
  },
  data: () => ({
    innerValue: ""
  }),
  watch: {
    // Handles internal model changes.
    innerValue(newVal) {
      this.$emit("input", newVal);
    },
    // Handles external model changes.
    value(newVal) {
      this.innerValue = newVal;
    }
  },
  created() {
    if (this.value) {
      this.innerValue = this.value;
    }
  },
  methods: {
    getValidationState({ dirty, validated, valid = null }) {
      return (this.rules != "" && (dirty || validated)) ? valid : null;
    },
  },
};
