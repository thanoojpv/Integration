import React, { useEffect, useState } from "react";
import DashboardLayout from "../components/DashboardLayout";
import { apiRequest } from "../services/api";

export default function TrainerCalendar() {
  const [events, setEvents] = useState([]);
  const [courses, setCourses] = useState([]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    course_id: "",
    title: "",
    description: "",
    event_type: "live_class",
    start_at: "",
    end_at: "",
    meeting_url: "",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      setError("");

      const [eventsResponse, coursesResponse] = await Promise.all([
        apiRequest("/trainer/calendar/events"),
        apiRequest("/trainer/courses"),
      ]);

      setEvents(eventsResponse?.events || []);
      setCourses(coursesResponse?.courses || []);
    } catch (err) {
      setError(err.message || "Unable to load calendar.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!form.course_id) {
      setError("Please select a course.");
      return;
    }

    if (!form.title.trim()) {
      setError("Please enter an event title.");
      return;
    }

    if (!form.start_at) {
      setError("Please select a start date and time.");
      return;
    }

    try {
      setSaving(true);
      setError("");

      await apiRequest("/trainer/calendar/events", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          start_at: new Date(form.start_at).toISOString(),
          end_at: form.end_at
            ? new Date(form.end_at).toISOString()
            : null,
        }),
      });

      setForm({
        course_id: "",
        title: "",
        description: "",
        event_type: "live_class",
        start_at: "",
        end_at: "",
        meeting_url: "",
      });

      await loadData();
    } catch (err) {
      setError(err.message || "Unable to create calendar event.");
    } finally {
      setSaving(false);
    }
  };

  const deleteEvent = async (eventId) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this calendar event?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");

      await apiRequest(
        `/trainer/calendar/events/${eventId}`,
        {
          method: "DELETE",
        }
      );

      await loadData();
    } catch (err) {
      setError(err.message || "Unable to delete event.");
    }
  };

  const formatDate = (value) => {
    if (!value) {
      return "No date";
    }

    return new Date(value).toLocaleString();
  };

  return (
    <DashboardLayout role="trainer">
      <div className="trainer-calendar-page">
        <div className="page-heading-row">
          <div>
            <h1>Calendar</h1>
            <p>
              Schedule live classes and other learning events for your courses.
            </p>
          </div>
        </div>

        {error && (
          <div className="state-card error-state">
            {error}
          </div>
        )}

        <div className="calendar-grid">
          <section className="card calendar-form-card">
            <div className="section-heading">
              <div>
                <h2>Create Event</h2>
                <p>
                  Add a live class, exam, assignment deadline, or other event.
                </p>
              </div>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Course</label>

                <select
                  name="course_id"
                  value={form.course_id}
                  onChange={handleChange}
                  required
                >
                  <option value="">
                    Select course
                  </option>

                  {courses.map((course) => (
                    <option
                      key={course.id}
                      value={course.id}
                    >
                      {course.title}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Event Title</label>

                <input
                  type="text"
                  name="title"
                  value={form.title}
                  onChange={handleChange}
                  placeholder="Example: Node.js Live Session"
                  required
                />
              </div>

              <div className="form-group">
                <label>Event Type</label>

                <select
                  name="event_type"
                  value={form.event_type}
                  onChange={handleChange}
                >
                  <option value="live_class">
                    Live Class
                  </option>

                  <option value="exam">
                    Exam
                  </option>

                  <option value="assignment">
                    Assignment
                  </option>

                  <option value="other">
                    Other
                  </option>
                </select>
              </div>

              <div className="form-group">
                <label>Description</label>

                <textarea
                  name="description"
                  value={form.description}
                  onChange={handleChange}
                  placeholder="Describe this event..."
                  rows="4"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Start</label>

                  <input
                    type="datetime-local"
                    name="start_at"
                    value={form.start_at}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>End</label>

                  <input
                    type="datetime-local"
                    name="end_at"
                    value={form.end_at}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Meeting URL</label>

                <input
                  type="url"
                  name="meeting_url"
                  value={form.meeting_url}
                  onChange={handleChange}
                  placeholder="https://meet.google.com/..."
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                disabled={saving}
              >
                {saving
                  ? "Creating..."
                  : "Create Calendar Event"}
              </button>
            </form>
          </section>

          <section className="card calendar-events-card">
            <div className="section-heading">
              <div>
                <h2>Upcoming Events</h2>
                <p>
                  Events scheduled for your courses.
                </p>
              </div>

              <button
                className="btn btn-outline"
                onClick={loadData}
                disabled={loading}
              >
                Refresh
              </button>
            </div>

            {loading ? (
              <div className="state-card">
                Loading calendar...
              </div>
            ) : events.length === 0 ? (
              <div className="state-card">
                No upcoming events yet.
              </div>
            ) : (
              <div className="calendar-event-list">
                {events.map((item) => (
                  <article
                    key={item.id}
                    className="calendar-event"
                  >
                    <div className="event-icon">
                      {item.event_type === "live_class"
                        ? "🎥"
                        : item.event_type === "exam"
                        ? "📝"
                        : item.event_type === "assignment"
                        ? "📚"
                        : "📅"}
                    </div>

                    <div className="event-content">
                      <div className="event-top">
                        <span className="event-type">
                          {item.event_type.replace(
                            "_",
                            " "
                          )}
                        </span>

                        <button
                          className="event-delete"
                          onClick={() =>
                            deleteEvent(item.id)
                          }
                        >
                          Delete
                        </button>
                      </div>

                      <h3>{item.title}</h3>

                      <p className="event-course">
                        {item.course_title}
                      </p>

                      <p className="event-time">
                        {formatDate(item.start_at)}

                        {item.end_at
                          ? ` → ${formatDate(item.end_at)}`
                          : ""}
                      </p>

                      {item.description && (
                        <p className="event-description">
                          {item.description}
                        </p>
                      )}

                      {item.meeting_url && (
                        <a
                          href={item.meeting_url}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-outline"
                        >
                          Open Meeting
                        </a>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </div>

        <style>{`
          .trainer-calendar-page {
            max-width: 1250px;
            margin: 0 auto;
          }

          .calendar-grid {
            display: grid;
            grid-template-columns: minmax(320px, 420px) 1fr;
            gap: 24px;
            align-items: start;
          }

          .calendar-form-card,
          .calendar-events-card {
            padding: 24px;
          }

          .section-heading {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 22px;
          }

          .section-heading h2 {
            margin: 0 0 6px;
          }

          .section-heading p {
            margin: 0;
            opacity: 0.7;
          }

          .form-group {
            margin-bottom: 16px;
          }

          .form-group label {
            display: block;
            margin-bottom: 7px;
            font-weight: 600;
          }

          .form-group input,
          .form-group select,
          .form-group textarea {
            width: 100%;
            box-sizing: border-box;
            padding: 11px 12px;
            border: 1px solid #d8dee8;
            border-radius: 10px;
            background: white;
            font: inherit;
          }

          .form-group textarea {
            resize: vertical;
          }

          .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
          }

          .calendar-event-list {
            display: flex;
            flex-direction: column;
            gap: 14px;
          }

          .calendar-event {
            display: flex;
            gap: 16px;
            padding: 18px;
            border: 1px solid #e3e7ee;
            border-radius: 14px;
          }

          .event-icon {
            width: 46px;
            height: 46px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f1f5f9;
            font-size: 22px;
            flex-shrink: 0;
          }

          .event-content {
            flex: 1;
            min-width: 0;
          }

          .event-top {
            display: flex;
            justify-content: space-between;
            gap: 12px;
          }

          .event-type {
            text-transform: capitalize;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.04em;
          }

          .event-content h3 {
            margin: 7px 0 4px;
          }

          .event-course,
          .event-time,
          .event-description {
            margin: 5px 0;
          }

          .event-course {
            font-weight: 600;
          }

          .event-time {
            opacity: 0.75;
          }

          .event-description {
            opacity: 0.8;
          }

          .event-delete {
            border: none;
            background: transparent;
            cursor: pointer;
            font: inherit;
            font-weight: 600;
          }

          .state-card {
            padding: 24px;
            text-align: center;
          }

          .error-state {
            margin-bottom: 20px;
          }

          @media (max-width: 900px) {
            .calendar-grid {
              grid-template-columns: 1fr;
            }
          }

          @media (max-width: 600px) {
            .form-row {
              grid-template-columns: 1fr;
            }
          }
        `}</style>
      </div>
    </DashboardLayout>
  );
}