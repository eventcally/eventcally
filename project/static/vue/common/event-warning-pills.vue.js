const EventWarningPills = {
  template: `
    <span>
      <span v-if="event.status" class="badge badge-pill badge-warning">
          <template v-if="event.status == 'cancelled'">Abgesagt</template>
          <template v-else-if="event.status == 'movedOnline'">Online verschoben</template>
          <template v-else-if="event.status == 'postponed'">Verschoben</template>
          <template v-else-if="event.status == 'rescheduled'">Neu angesetzt</template>
      </span>
      <span v-if="event.booked_up" class="badge badge-pill badge-warning">Ausgebucht</span>
      <span v-if="event.attendance_mode" class="badge badge-pill badge-info">
          <template v-if="event.attendance_mode == 'online'">Online</template>
          <template v-else-if="event.attendance_mode == 'mixed'">Präsenzveranstaltung und online</template>
      </span>
  </span>
    `,
  props: {
    event: {
      type: null
    },
  },
};
