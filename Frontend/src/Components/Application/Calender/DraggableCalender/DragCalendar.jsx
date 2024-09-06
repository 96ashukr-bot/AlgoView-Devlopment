import React, { Component, Fragment } from "react";
import { Col } from "reactstrap";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin, { Draggable } from "@fullcalendar/interaction";
import Swal from "sweetalert2/dist/sweetalert2.js";
import { H4 } from "../../../../AbstractElements";
import moment from "moment";
import uuid from "react-uuid";

class DragCalendar extends Component {
  state = {
    calendarEvents: [
      {
        title: "Atlanta Monster",
        start: new Date("2019-04-04 00:00"),
        id: "1001",
      },
      {
        title: "My Favorite Murder",
        start: new Date("2019-04-05 00:00"),
        id: "1002",
      },
    ],
    events: [
      { title: "Birthday Party", id: "1", icon: "birthday-cake" },
      { title: "Meeting With Team.", id: "2", icon: "user" },
      { title: "Tour & Picnic", id: "3", icon: "plane" },
      { title: "Reporting Schedule", id: "4", icon: "file-text" },
      { title: "Lunch & Break", id: "5", icon: "briefcase" },
    ],
  };

  /**
   * adding dragable properties to external events through javascript
   */
  componentDidMount() {
    let draggableEl = document.getElementById("external-events");
    new Draggable(draggableEl, {
      itemSelector: ".fc-event",
      eventData: function (eventEl) {
        let title = eventEl.getAttribute("title");
        let id = eventEl.getAttribute("data");
        return {
          title: title,
          id: id,
        };
      },
    });
  }

  /**
   * when we click on event we are displaying event details
   */
  eventClick = (eventClick) => {
    Swal.fire({
      title: eventClick.event.title,
      html:
        `<div class="table-responsive">
      <table class="table">
      <tbody>
      <tr >
      <td>Title</td>
      <td><strong>` +
        eventClick.event.title +
        `</strong></td>
      </tr>
      <tr >
      <td>Start Time</td>
      <td><strong>
      ` +
        eventClick.event.start +
        `
      </strong></td>
      </tr>
      </tbody>
      </table>
      </div>`,

      showCancelButton: true,
      confirmButtonColor: "#d33",
      cancelButtonColor: "#3085d6",
      confirmButtonText: "Remove Event",
      cancelButtonText: "Close",
    }).then((result) => {
      if (result.value) {
        eventClick.event.remove(); // It will remove event from the calendar
        Swal.fire("Deleted!", "Your Event has been deleted.", "success");
      }
    });
  };

  handleeventRecieve = (info) => {
    console.log("info 95", info.draggedEl.getAttribute("id"));
    const id = uuid();
    const newEvent = {
      title: info.draggedEl.getAttribute("title"),
      start: info.date,
      end: new Date(moment(info.date).add(1, "hour").valueOf()),
      id: id,
    };
    this.setState({
      calendarEvents: this.state.calendarEvents.concat(newEvent),
    });
  };

  render() {
    console.log("event state", this.state.calendarEvents);
    return (
      <Fragment>
        <Col xxl="3" className="box-col-12">
          <div className="md-sidebar">
            <div className={`md-sidebar-aside job-left-aside custom-scrollbar `}>
              <div className="email-sidebar">
                <div className={`email-left-aside`}></div>
                <div id="external-events">
                  <H4>{"Draggable Events"}</H4>
                  {this.state.events.map((event) => (
                    <div className="fc-event fc-h-event fc-daygrid-event fc-daygrid-block-event" title={event.title} data={event.id} icon={event.icon} key={event.id}>
                      <div className="fc-event-main">
                        <i className={`fa fa-${event.icon} me-2`}></i>
                        {event.title}
                      </div>
                    </div>
                  ))}
                  <p>
                    <input className="checkbox_animated" id="drop-remove" type="checkbox" />
                    <label htmlFor="drop-remove" className="m-0">
                      remove after drop
                    </label>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </Col>
        <Col xxl="9" className="box-col-12">
          <div className="demo-app-calendar" id="mycalendartest">
            <FullCalendar
              defaultView="dayGridMonth"
              header={{
                left: "prev,next today",
                center: "title",
                right: "dayGridMonth,timeGridWeek,timeGridDay,listWeek",
              }}
              rerenderDelay={10}
              eventDurationEditable={false}
              editable={true}
              droppable={true}
              plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
              ref={this.state.calendarComponentRef}
              weekends={this.state.calendarWeekends}
              events={this.state.calendarEvents}
              drop={this.handleeventRecieve}
              eventClick={this.eventClick}
              eventOverlap={true}
            />
          </div>
        </Col>
      </Fragment>
    );
  }
}

export default DragCalendar;
