const EventListRead = {
  template: `
    <div>
      <b-overlay :show="isLoading">
        <div v-if="eventList">
          <h1>{{ eventList.name }}</h1>
        </div>
        <h2>{{ $t("shared.models.event.listName") }}</h2>
        <EventListEventList />
      </b-overlay>
    </div>
    `,
  data: () => ({
    isLoading: false,
    eventList: null,
  }),
  computed: {
    eventListId() {
      return this.$route.params.event_list_id;
    },
  },
  mounted() {
    this.isLoading = false;
    this.eventList = null;
    this.loadData();
  },
  methods: {
    loadData() {
      axios
        .get(`/api/v1/event-lists/${this.eventListId}`, {
          withCredentials: true,
          handleLoading: this.handleLoading,
        })
        .then((response) => {
          this.eventList = response.data;
        });
    },
    handleLoading(isLoading) {
      this.isLoading = isLoading;
    },
  },
};
