const TotalPagination = {
  template: `
    <nav aria-label="Page navigation" v-if="totalRows > 0">
      <ul class="pagination">
        <li class="page-item" :class="{ disabled: this.innerValue == 1 }"> <a class="page-link" href="#" @click.prevent="first" :title="$t('shared.pagination.first')"><i class="fa fa-angle-double-left"></i></a></li>
        <li class="page-item" :class="{ disabled: this.innerValue == 1 }"> <a class="page-link" href="#" @click.prevent="previous" :title="$t('shared.pagination.previous')"><i class="fa fa-angle-left"></i></a></li>
        <li class="page-item disabled d-none d-sm-inline"><span class="page-link">{{ label }}</span></li>
        <li class="page-item" :class="{ disabled: this.innerValue >= this.totalPages }"> <a class="page-link" href="#" @click.prevent="next" :title="$t('shared.pagination.next')"><i class="fa fa-angle-right"></i></a></li>
        <li class="page-item" :class="{ disabled: this.innerValue >= this.totalPages }"> <a class="page-link" href="#" @click.prevent="last" :title="$t('shared.pagination.last')"><i class="fa fa-angle-double-right"></i></a></li>
      </ul>
    </nav>
    `,
    props: {
      perPage: {
        type: Number
      },
      totalPages: {
        type: Number
      },
      totalRows: {
        type: Number
      },
      value: {
        type: Number
      }
    },
    data: () => ({
      innerValue: 1
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
    computed: {
      label() {
        return this.$t("shared.pagination.info", {
          page: this.innerValue,
          pages: this.totalPages,
          total: this.totalRows
        });
      },
    },
    methods: {
      first() {
        this.innerValue = 1;
      },
      previous() {
        this.innerValue--;
      },
      next() {
        this.innerValue++;
      },
      last() {
        this.innerValue = this.totalPages;
      }
    }
};
