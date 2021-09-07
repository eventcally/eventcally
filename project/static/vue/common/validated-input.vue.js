const ValidatedInput = {
  template: `
    <div>
      <ValidationProvider :vid="vid" :name="$attrs.label" :rules="rules" v-slot="validationContext">
        <b-form-group v-bind="$attrs">
          <b-form-input
            v-model="innerValue"
            v-bind="$attrs"
            :state="getValidationState(validationContext)"
          ></b-form-input>
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
      return dirty || validated ? valid : null;
    },
  },
};
