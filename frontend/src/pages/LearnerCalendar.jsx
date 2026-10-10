import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import DashboardLayout from "../components/DashboardLayout";
import { apiRequest } from "../services/api";

export default function LearnerCalendar() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadCalendar = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await apiRequest("/learner/calendar");

      setEvents(data?.events || []);
    } catch (err) {
      setError(
        err.message || "Unable to load your calendar."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCalendar();
  }, []);

  const formatDate = (value) => {
    if (!value) {
      return "Date not available";
    }

    return new Date(value).toLocaleString([], {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  };

  const getEventIcon = (eventType) => {
    if (eventType === "live_class") {
      return "🎥";
    }

    if (eventType === "exam") {
      return "📝";
    }

    if (eventType === "assignment") {
      return "📚";
    }

    return "📅";
  };

  const getEventLabel = (eventType) => {
    if (eventType === "live_class") {
      return "Live Class";
    }

    if (eventType === "exam") {
      return "Exam";
    }

    if (eventType === "assignment") {
      return "Assignment";
    }

    return "Learning Event";
  };

  return (
    <DashboardLayout role="learner">
      <div className="learner-calendar-page">
        <div className="page-heading-row">
          <div>
            <h1>Calendar</h1>

            <p>
              Your upcoming live classes and learning events.
            </p>
          </div>

          <Link
            className="btn btn-outline"
            to="/learner"
          >
            ← Dashboard
          </Link>
        </div>

        {error && (
          <div className="state-card error-state">
            <h3>Unable to load calendar</h3>

            <p>{error}</p>

            <button
              className="btn btn-primary"
              onClick={loadCalendar}
            >
              Try Again
            </button>
          </div>
        )}

        {!error && loading && (
          <div className="state-card">
            <div className="calendar-loading-icon">
              📅
            </div>

            <h3>Loading your calendar...</h3>

            <p>
              Checking your upcoming learning events.
            </p>
          </div>
        )}

        {!error && !loading && events.length === 0 && (
          <div className="state-card">
            <div className="calendar-empty-icon">
              📅
            </div>

            <h2>No upcoming events</h2>

            <p>
              You don't have any upcoming classes or learning
              events at the moment.
            </p>
          </div>
        )}

        {!error && !loading && events.length > 0 && (
          <div className="calendar-event-list">
            {events.map((event) => (
              <article
                key={event.id}
                className="calendar-event-card"
              >
                <div className="event-icon">
                  {getEventIcon(event.event_type)}
                </div>

                <div className="event-main">
                  <div className="event-header">
                    <span className="event-type">
                      {getEventLabel(event.event_type)}
                    </span>
                  </div>

                  <h2>{event.title}</h2>

                  <p className="event-course">
                    {event.course_title}
                  </p>

                  <div className="event-time">
                    <span>🕒</span>

                    <div>
                      <strong>
                        {formatDate(event.start_at)}
                      </strong>

                      {event.end_at && (
                        <span className="event-end-time">
                          Ends at{" "}
                          {new Date(
                            event.end_at
                          ).toLocaleTimeString([], {
                            hour: "numeric",
                            minute: "2-digit",
                          })}
                        </span>
                      )}
                    </div>
                  </div>

                  {event.description && (
                    <p className="event-description">
                      {event.description}
                    </p>
                  )}

                  <div className="event-actions">
                    {event.meeting_url ? (
                      <a
                        href={event.meeting_url}
                        target="_blank"
                        rel="noreferrer"
                        className="btn btn-primary"
                      >
                        🎥 Join Meeting
                      </a>
                    ) : (
                      <span className="meeting-unavailable">
                        Meeting link not available yet
                      </span>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}

        <style>{`
          .learner-calendar-page {
            max-width: 1150px;
            margin: 0 auto;
          }

          .calendar-event-list {
            display: flex;
            flex-direction: column;
            gap: 18px;
          }

          .calendar-event-card {
            display: flex;
            gap: 20px;
            padding: 24px;
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
          }

          .event-icon {
            width: 56px;
            height: 56px;
            min-width: 56px;
            border-radius: 14px;
            background: #eef2ff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 26px;
          }

          .event-main {
            flex: 1;
            min-width: 0;
          }

          .event-header {
            margin-bottom: 6px;
          }

          .event-type {
            display: inline-flex;
            padding: 5px 10px;
            border-radius: 999px;
            background: #f1f5f9;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
          }

          .event-main h2 {
            margin: 8px 0 5px;
            font-size: 22px;
          }

          .event-course {
            margin: 0 0 14px;
            font-weight: 600;
            opacity: 0.75;
          }

          .event-time {
            display: flex;
            align-items: flex-start;
            gap: 9px;
            margin-bottom: 12px;
          }

          .event-time strong {
            display: block;
          }

          .event-end-time {
            display: block;
            margin-top: 3px;
            font-size: 13px;
            opacity: 0.65;
          }

          .event-description {
            margin: 12px 0;
            line-height: 1.6;
            opacity: 0.8;
          }

          .event-actions {
            margin-top: 18px;
          }

          .meeting-unavailable {
            font-size: 14px;
            opacity: 0.65;
          }

          .state-card {
            padding: 50px 30px;
            text-align: center;
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
          }

          .state-card h2,
          .state-card h3 {
            margin: 10px 0;
          }

          .state-card p {
            opacity: 0.7;
          }

          .calendar-empty-icon,
          .calendar-loading-icon {
            font-size: 42px;
          }

          .error-state {
            border-color: #fecaca;
          }

          @media (max-width: 650px) {
            .calendar-event-card {
              flex-direction: column;
            }

            .event-icon {
              width: 50px;
              min-width: 50px;
              height: 50px;
            }
          }
        `}</style>
      </div>
    </DashboardLayout>
  );
}