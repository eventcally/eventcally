const UserFavoriteEventList = {
  template: `
    <div>
        <h1>{{ $t("comp.title") }}</h1>

        <b-overlay :show="isLoading" variant="transparent">
          <div v-if="errorMessage" class="mb-4">
              <b-alert show variant="danger">{{ errorMessage }}</b-alert>
              <button type="button" class="btn btn-outline-secondary" @click="loadData()"><i class="fa fa-sync-alt"></i></button>
          </div>

          <div v-for="event in items">
            <div class="card mb-3">
                <div>
                    <img v-if="event.photo" :src="url_for_image(event.photo, 500)" class="card-img-top" style="object-fit: cover; height: 40vw;" />
                </div>
                <div class="card-body">
                  <h5 class="card-title"><a href="#" @click.stop.prevent="viewItem(event.id)">{{ event.name }}</a> <event-warning-pills :event="event"></event-warning-pills></h5>
                  <h6 class="card-subtitle mb-2 text-body"><i class="fa fa-calendar"></i> {{ $root.render_event_date_instance(event.date_definitions[0].start, event.date_definitions[0].allday) }}</h6>
                  <p class="card-text" v-if="event.description" v-html="event.description.truncate(100, true)"></p>
                  <small class="text-muted mr-2"><i class="fa fa-database"></i> {{ event.organization.name }}</small>
                  <small v-if="event.organizer.name != event.organization.name" class="text-muted mr-2"><i class="fa fa-server"></i> {{ event.organizer.name }}</small>
                  <small class="text-muted"><i class="fa fa-map-marker"></i> {{ event.place.name }}</small>
                </div>
                <div class="card-footer">
                  <a href="#" @click.stop.prevent="removeItem(event.id)" class="card-link">{{ $t("shared.delete") }}&hellip;</a>
                </div>
            </div>
          </div>

          <b-pagination v-if="totalRows > perPage"
            v-model="currentPage"
            :total-rows="totalRows"
            :per-page="perPage"
          ></b-pagination>

      </b-overlay>
    </div>
    `,
  i18n: {
    messages: {
      en: {
        comp: {
          title: "Favorite events",
          removedMessage: "Event successfully removed",
          removeConfirmation: "Do you really want to remove the event?",
        },
      },
      de: {
        comp: {
          title: "Merkzettel",
          removedMessage: "Veranstaltung erfolgreich entfernt",
          removeConfirmation:
            "Möchtest du die Veranstaltung wirklich entfernen?",
        },
      },
    },
  },
  data: () => ({
    errorMessage: null,
    isLoading: false,
    fields: [
      {
        key: "name",
        label: i18n.t("shared.models.event.name"),
      },
    ],
    totalRows: 0,
    currentPage: 1,
    perPage: 10,
    items: [],
  }),
  mounted() {
    this.isLoading = false;
    this.loadData();
  },
  methods: {
    loadData() {
      const vm = this;
      axios
        .get(`/api/v1/user/favorite-events/search`, {
          params: {
            page: vm.currentPage,
            per_page: vm.perPage,
          },
          withCredentials: true,
          handler: this,
          handleLoading: this.handleLoading,
        })
        .then((response) => {
          vm.totalRows = response.data.total;
          vm.items = response.data.items;
        })
        .catch(() => {
          callback([]);
        });
      return null;
    },
    refreshTableData() {
      this.$refs.table.refresh();
    },
    handleLoading(isLoading) {
      this.isLoading = isLoading;
    },
    handleRequestStart() {
      this.errorMessage = null;
    },
    handleRequestError(error, message) {
      this.errorMessage = message;
    },
    viewItem(id) {
      window.location.href = `/event/${id}`;
    },
    removeItem(id) {
      if (confirm(this.$t("comp.removeConfirmation"))) {
        axios
          .delete(`/api/v1/user/favorite-events/${id}`, {
            withCredentials: true,
          })
          .then(() => {
            this.$root.makeSuccessToast(this.$t("comp.removedMessage"));
            this.loadData();
          });
      }
    },
  },
};
