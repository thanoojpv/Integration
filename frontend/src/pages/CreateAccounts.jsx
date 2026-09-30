import React, { useState } from "react";
import DashboardLayout from "../components/DashboardLayout";
const API_BASE =
  `${import.meta.env.VITE_API_BASE_URL}/api`;

const initialForm = {
  name: "",
  email: "",
  mobile: "",
  password: "",

  // Learner
  education: "",
  batch_id: "",

  // Trainer
  specialization: "",
  experience: "",
  bio: "",
};

export default function CreateAccounts() {
  const [accountType, setAccountType] = useState("learner");

  const [form, setForm] = useState(initialForm);

  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);

  const [successMessage, setSuccessMessage] = useState("");

  const [errorMessage, setErrorMessage] = useState("");

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));

    setSuccessMessage("");
    setErrorMessage("");
  };

  const handleAccountTypeChange = (type) => {
    setAccountType(type);

    setSuccessMessage("");
    setErrorMessage("");

    setForm(initialForm);
    setShowPassword(false);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setLoading(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const token = localStorage.getItem("access_token");

      if (!token) {
        throw new Error(
          "Admin login session not found. Please login again."
        );
      }

      const endpoint =
        accountType === "learner"
          ? `${API_BASE}/admin/learners`
          : `${API_BASE}/admin/trainers`;

      let requestBody;

      if (accountType === "learner") {
        requestBody = {
          name: form.name.trim(),
          email: form.email.trim().toLowerCase(),
          mobile: form.mobile.trim(),
          password: form.password,
          education: form.education.trim(),
          batch_id: form.batch_id
            ? Number(form.batch_id)
            : null,
        };
      } else {
        requestBody = {
          name: form.name.trim(),
          email: form.email.trim().toLowerCase(),
          mobile: form.mobile.trim(),
          password: form.password,
          specialization: form.specialization.trim(),
          experience: Number(form.experience) || 0,
          bio: form.bio.trim(),
        };
      }

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.error ||
            data.message ||
            "Unable to create account."
        );
      }

      setSuccessMessage(
        `${accountType === "learner" ? "Learner" : "Trainer"} account created successfully.`
      );

      setForm(initialForm);
      setShowPassword(false);
    } catch (error) {
      console.error("CREATE ACCOUNT ERROR:", error);

      setErrorMessage(
        error.message || "Something went wrong."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout role="admin">
    <div className="create-accounts-page">
      <div className="create-accounts-header">
        <div>
          <h1>Create Accounts</h1>

          <p>
            Create new learner and trainer accounts from the
            admin portal.
          </p>
        </div>
      </div>

      {/* ACCOUNT TYPE */}

      <div className="account-type-section">
        <button
          type="button"
          className={
            accountType === "learner"
              ? "account-type-button active"
              : "account-type-button"
          }
          onClick={() =>
            handleAccountTypeChange("learner")
          }
        >
          Learner
        </button>

        <button
          type="button"
          className={
            accountType === "trainer"
              ? "account-type-button active"
              : "account-type-button"
          }
          onClick={() =>
            handleAccountTypeChange("trainer")
          }
        >
          Trainer
        </button>
      </div>

      {/* FORM */}

      <form
        className="create-account-card"
        onSubmit={handleSubmit}
      >
        <div className="form-title">
          <h2>
            Create{" "}
            {accountType === "learner"
              ? "Learner"
              : "Trainer"}{" "}
            Account
          </h2>

          <p>
            Enter the details below to create the account.
          </p>
        </div>

        {/* NAME */}

        <div className="form-group">
          <label htmlFor="name">
            Full Name
          </label>

          <input
            id="name"
            type="text"
            name="name"
            value={form.name}
            onChange={handleChange}
            placeholder="Enter full name"
            required
          />
        </div>

        {/* EMAIL */}

        <div className="form-group">
          <label htmlFor="email">
            Email Address
          </label>

          <input
            id="email"
            type="email"
            name="email"
            value={form.email}
            onChange={handleChange}
            placeholder="Enter email address"
            required
          />
        </div>

        {/* MOBILE */}

        <div className="form-group">
          <label htmlFor="mobile">
            Mobile Number
          </label>

          <input
            id="mobile"
            type="tel"
            name="mobile"
            value={form.mobile}
            onChange={handleChange}
            placeholder="Enter mobile number"
          />
        </div>

        {/* PASSWORD */}

        <div className="form-group">
          <label htmlFor="password">
            Password
          </label>

          <div className="password-wrapper">
            <input
              id="password"
              type={
                showPassword
                  ? "text"
                  : "password"
              }
              name="password"
              value={form.password}
              onChange={handleChange}
              placeholder="Minimum 6 characters"
              minLength={6}
              required
            />

            <button
              type="button"
              className="password-toggle"
              onClick={() =>
                setShowPassword(
                  !showPassword
                )
              }
              disabled={loading}
            >
              {showPassword
                ? "Hide"
                : "Show"}
            </button>
          </div>
        </div>

        {/* LEARNER FIELDS */}

        {accountType === "learner" && (
          <>
            <div className="form-group">
              <label htmlFor="education">
                Education
              </label>

              <input
                id="education"
                type="text"
                name="education"
                value={form.education}
                onChange={handleChange}
                placeholder="Example: B.Tech"
              />
            </div>

            <div className="form-group">
              <label htmlFor="batch_id">
                Batch ID
              </label>

              <input
                id="batch_id"
                type="number"
                name="batch_id"
                value={form.batch_id}
                onChange={handleChange}
                placeholder="Enter batch ID"
                min="1"
              />
            </div>
          </>
        )}

        {/* TRAINER FIELDS */}

        {accountType === "trainer" && (
          <>
            <div className="form-group">
              <label htmlFor="specialization">
                Specialization
              </label>

              <input
                id="specialization"
                type="text"
                name="specialization"
                value={form.specialization}
                onChange={handleChange}
                placeholder="Example: Full Stack Development"
              />
            </div>

            <div className="form-group">
              <label htmlFor="experience">
                Experience
              </label>

              <input
                id="experience"
                type="number"
                name="experience"
                value={form.experience}
                onChange={handleChange}
                placeholder="Years of experience"
                min="0"
              />
            </div>

            <div className="form-group">
              <label htmlFor="bio">
                Bio
              </label>

              <textarea
                id="bio"
                name="bio"
                value={form.bio}
                onChange={handleChange}
                placeholder="Enter trainer bio"
                rows="4"
              />
            </div>
          </>
        )}

        {/* SUCCESS */}

        {successMessage && (
          <div className="success-message">
            {successMessage}
          </div>
        )}

        {/* ERROR */}

        {errorMessage && (
          <div className="error-message">
            {errorMessage}
          </div>
        )}

        {/* SUBMIT */}

        <button
          type="submit"
          className="create-account-button"
          disabled={loading}
        >
          {loading
            ? "Creating..."
            : `Create ${
                accountType === "learner"
                  ? "Learner"
                  : "Trainer"
              } Account`}
        </button>
      </form>

      <style>{`
        .create-accounts-page {
          width: 100%;
          max-width: 1000px;
          margin: 0 auto;
          padding: 32px;
          box-sizing: border-box;
        }

        .create-accounts-header {
          margin-bottom: 24px;
        }

        .create-accounts-header h1 {
          margin: 0 0 8px;
          font-size: 30px;
          font-weight: 700;
          color: #172033;
        }

        .create-accounts-header p {
          margin: 0;
          color: #667085;
          font-size: 15px;
        }

        .account-type-section {
          display: flex;
          gap: 12px;
          margin-bottom: 24px;
        }

        .account-type-button {
          min-width: 140px;
          padding: 12px 22px;
          border-radius: 8px;
          border: 1px solid #3764e8;
          background: #ffffff;
          color: #3764e8;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
        }

        .account-type-button.active {
          background: #3764e8;
          color: #ffffff;
        }

        .account-type-button:hover {
          opacity: 0.92;
        }

        .create-account-card {
          background: #ffffff;
          border: 1px solid #e4e7ec;
          border-radius: 14px;
          padding: 30px;
          box-sizing: border-box;
          box-shadow: 0 3px 12px rgba(16, 24, 40, 0.06);
        }

        .form-title {
          margin-bottom: 26px;
        }

        .form-title h2 {
          margin: 0 0 7px;
          color: #172033;
          font-size: 21px;
        }

        .form-title p {
          margin: 0;
          color: #667085;
          font-size: 14px;
        }

        .form-group {
          margin-bottom: 19px;
        }

        .form-group label {
          display: block;
          margin-bottom: 7px;
          color: #344054;
          font-size: 14px;
          font-weight: 600;
        }

        .form-group input,
        .form-group textarea {
          width: 100%;
          box-sizing: border-box;
          padding: 12px 13px;
          border: 1px solid #d0d5dd;
          border-radius: 8px;
          background: #ffffff;
          color: #101828;
          font-size: 14px;
          outline: none;
          font-family: inherit;
        }

        .form-group input:focus,
        .form-group textarea:focus {
          border-color: #3764e8;
          box-shadow: 0 0 0 3px rgba(55, 100, 232, 0.10);
        }

        .form-group textarea {
          resize: vertical;
          min-height: 100px;
        }

        .password-wrapper {
          position: relative;
          width: 100%;
        }

        .password-wrapper input {
          padding-right: 65px;
        }

        .password-toggle {
          position: absolute;
          right: 10px;
          top: 50%;
          transform: translateY(-50%);
          border: none;
          background: transparent;
          color: #3764e8;
          font-size: 13px;
          font-weight: 600;
          cursor: pointer;
          padding: 5px;
        }

        .password-toggle:disabled {
          cursor: not-allowed;
          opacity: 0.6;
        }

        .success-message {
          margin-top: 20px;
          padding: 13px 15px;
          border-radius: 8px;
          background: #ecfdf3;
          border: 1px solid #abefc6;
          color: #067647;
          font-size: 14px;
        }

        .error-message {
          margin-top: 20px;
          padding: 13px 15px;
          border-radius: 8px;
          background: #fef3f2;
          border: 1px solid #fecdca;
          color: #b42318;
          font-size: 14px;
        }

        .create-account-button {
          width: 100%;
          margin-top: 24px;
          padding: 13px 20px;
          border: none;
          border-radius: 8px;
          background: #3764e8;
          color: #ffffff;
          font-size: 15px;
          font-weight: 600;
          cursor: pointer;
        }

        .create-account-button:hover {
          opacity: 0.92;
        }

        .create-account-button:disabled {
          cursor: not-allowed;
          opacity: 0.65;
        }

        @media (max-width: 650px) {
          .create-accounts-page {
            padding: 20px;
          }

          .create-account-card {
            padding: 20px;
          }

          .account-type-section {
            flex-direction: column;
          }

          .account-type-button {
            width: 100%;
          }
        }
      `}</style>
    </div>
    </DashboardLayout>
  );
}