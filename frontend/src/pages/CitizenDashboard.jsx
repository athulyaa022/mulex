import { useState } from "react";

import {
  ShieldCheck,
  Search,
  History,
  LogOut,
  Link2,
  MessageSquareWarning,
  CreditCard,
  PhoneCall,
  ChevronRight,
  X,
  ArrowLeft,
  Upload,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";

function CitizenDashboard({ citizen, onLogout }) {
  const [checkType, setCheckType] = useState(null);
  const [inputValue, setInputValue] = useState("");
  const [senderPhone, setSenderPhone] = useState("");
  const [senderEmail, setSenderEmail] = useState("");
  const [source, setSource] = useState("");
  const [transactionId, setTransactionId] = useState("");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [evidenceName, setEvidenceName] = useState("");
  const [showResult, setShowResult] = useState(false);

  const openCheck = (type) => {
    setCheckType(type);
    setInputValue("");
    setSenderPhone("");
    setSenderEmail("");
    setSource("");
    setTransactionId("");
    setAmount("");
    setDescription("");
    setEvidenceName("");
    setShowResult(false);
  };

  const closeCheck = () => {
    setCheckType(null);
    setShowResult(false);
  };

  const handleEvidence = (e) => {
    const file = e.target.files?.[0];

    if (file) {
      setEvidenceName(file.name);
    }
  };

  const handleAnalyze = (e) => {
    e.preventDefault();

    if (!inputValue.trim() && !description.trim()) {
      alert(
        "Please enter the suspicious information before continuing."
      );
      return;
    }

    setShowResult(true);
  };

  const getDetails = () => {
    if (checkType === "message") {
      return {
        icon: <MessageSquareWarning size={22} />,
        title: "Check a suspicious message",
        description:
          "Paste the message and add the sender details you have. This helps MULEX connect related reports.",
        label: "Message content",
        placeholder:
          "Paste the SMS, WhatsApp or email message here...",
        button: "Check message",
      };
    }

    if (checkType === "link") {
      return {
        icon: <Link2 size={22} />,
        title: "Check a suspicious link",
        description:
          "Enter the URL and, if available, tell us where you received it.",
        label: "Suspicious URL",
        placeholder: "https://example.com",
        button: "Check link",
      };
    }

    if (checkType === "call") {
      return {
        icon: <PhoneCall size={22} />,
        title: "Check a suspicious call",
        description:
          "Tell us who called and what they asked you to do.",
        label: "What did the caller say?",
        placeholder:
          "Example: Caller claimed to be from my bank and asked for an OTP...",
        button: "Check call",
      };
    }

    return {
      icon: <CreditCard size={22} />,
      title: "Check a payment or UPI ID",
      description:
        "Enter the UPI ID or phone number. Add transaction details if you have them.",
      label: "UPI ID / phone number",
      placeholder: "example@upi or +91 XXXXX XXXXX",
      button: "Check payment",
    };
  };

  const details = checkType ? getDetails() : null;

  return (
    <div className="citizen-page">

      {/* HEADER */}
      <header className="citizen-header">

        <div className="citizen-brand">

          <div className="citizen-logo">
            <ShieldCheck size={22} />
          </div>

          <div>
            <h2>MULEX</h2>
            <span>Fraud Intelligence</span>
          </div>

        </div>

        <div className="citizen-user">

          <div className="citizen-avatar">
            {(citizen.name || "Citizen")
              .split(" ")
              .map((w) => w[0])
              .join("")
              .slice(0, 2)
              .toUpperCase()}
          </div>

          <div className="citizen-user-info">
            <strong>{citizen.name || "Citizen"}</strong>
            <span>
              {citizen.email || "Citizen account"}
            </span>
          </div>

          <button
            className="citizen-logout"
            onClick={onLogout}
            type="button"
          >
            <LogOut size={16} />
            Logout
          </button>

        </div>

      </header>


      {/* MAIN */}
      <main className="citizen-main">

        {/* WELCOME */}
        <section className="citizen-welcome">

          <p className="citizen-eyebrow">
            CITIZEN SAFETY PORTAL
          </p>

          <h1>
            Check before you
            <br />
            <span>trust or pay.</span>
          </h1>

          <p>
            Received something suspicious? Check it with
            MULEX before clicking, paying or sharing
            personal information.
          </p>

        </section>


        {/* CHECK CARD */}
        <section className="citizen-check-card">

          <div className="citizen-check-icon">
            <Search size={25} />
          </div>

          <div>
            <h2>What would you like to check?</h2>

            <p>
              Choose what you received. We'll guide you
              through the right details.
            </p>
          </div>


          <div className="citizen-check-options">

            {/* MESSAGE */}
            <button
              type="button"
              onClick={() => openCheck("message")}
            >
              <MessageSquareWarning size={20} />

              <span>
                <strong>Suspicious Message</strong>
                <small>
                  SMS, WhatsApp or email
                </small>
              </span>

              <ChevronRight size={18} />
            </button>


            {/* LINK */}
            <button
              type="button"
              onClick={() => openCheck("link")}
            >
              <Link2 size={20} />

              <span>
                <strong>Suspicious Link</strong>
                <small>
                  Website or URL
                </small>
              </span>

              <ChevronRight size={18} />
            </button>


            {/* PAYMENT */}
            <button
              type="button"
              onClick={() => openCheck("payment")}
            >
              <CreditCard size={20} />

              <span>
                <strong>Payment / UPI</strong>
                <small>
                  UPI ID or payment request
                </small>
              </span>

              <ChevronRight size={18} />
            </button>


            {/* CALL */}
            <button
              type="button"
              onClick={() => openCheck("call")}
            >
              <PhoneCall size={20} />

              <span>
                <strong>Suspicious Call</strong>
                <small>
                  Unknown or fraudulent caller
                </small>
              </span>

              <ChevronRight size={18} />
            </button>

          </div>

        </section>


        {/* SAFETY TIP */}
        <section className="citizen-help-card">

          <div className="citizen-help-icon">
            <ShieldAlert size={20} />
          </div>

          <div>
            <strong>Stay safe while checking</strong>

            <p>
              Never share OTPs, PINs, passwords or full
              banking credentials with anyone.
            </p>
          </div>

        </section>


        {/* HISTORY */}
        <section className="citizen-history">

          <div className="citizen-section-heading">

            <div>
              <h2>Recent checks</h2>

              <p>
                Your previous fraud investigations
              </p>
            </div>

            <button type="button">
              <History size={16} />
              View history
              <ChevronRight size={16} />
            </button>

          </div>


          <div className="citizen-history-card">

            <div className="citizen-history-row">

              <div className="citizen-history-icon danger">
                <MessageSquareWarning size={18} />
              </div>

              <div>
                <strong>
                  KYC verification message
                </strong>

                <span>
                  Checked today • High risk
                </span>
              </div>

              <span className="citizen-risk high">
                High Risk
              </span>

            </div>


            <div className="citizen-history-row">

              <div className="citizen-history-icon warning">
                <CreditCard size={18} />
              </div>

              <div>
                <strong>
                  Unknown UPI identifier
                </strong>

                <span>
                  Checked yesterday • Under review
                </span>
              </div>

              <span className="citizen-risk medium">
                Under Review
              </span>

            </div>


            <div className="citizen-history-row">

              <div className="citizen-history-icon safe">
                <CheckCircle2 size={18} />
              </div>

              <div>
                <strong>
                  Website verification
                </strong>

                <span>
                  Checked recently • No threat detected
                </span>
              </div>

              <span className="citizen-risk safe">
                Low Risk
              </span>

            </div>

          </div>

        </section>

      </main>


      {/* INVESTIGATION MODAL */}
      {checkType && (

        <div
          className="modal-overlay"
          onClick={closeCheck}
        >

          <div
            className="report-modal citizen-investigation-modal citizen-pro-modal"
            onClick={(e) => e.stopPropagation()}
          >

            {!showResult ? (

              <>
                <div className="modal-header">

                  <div className="modal-icon">
                    {details.icon}
                  </div>

                  <button
                    className="modal-close"
                    onClick={closeCheck}
                    type="button"
                  >
                    <X size={18} />
                  </button>

                </div>


                <h2>{details.title}</h2>

                <p>
                  {details.description}
                </p>


                <form onSubmit={handleAnalyze}>

                  <label>
                    {details.label}
                  </label>

                  <textarea
                    value={inputValue}
                    onChange={(e) =>
                      setInputValue(e.target.value)
                    }
                    placeholder={details.placeholder}
                    rows={
                      checkType === "message" ||
                      checkType === "call"
                        ? 5
                        : 2
                    }
                  />


                  {/* MESSAGE EXTRA DETAILS */}
                  {checkType === "message" && (
                    <>

                      <div className="citizen-form-grid">

                        <div>

                          <label>
                            Sender phone number
                          </label>

                          <input
                            value={senderPhone}
                            onChange={(e) =>
                              setSenderPhone(e.target.value)
                            }
                            placeholder="+91 XXXXX XXXXX"
                          />

                        </div>


                        <div>

                          <label>
                            Sender email{" "}
                            <span className="optional-label">
                              optional
                            </span>
                          </label>

                          <input
                            value={senderEmail}
                            onChange={(e) =>
                              setSenderEmail(e.target.value)
                            }
                            placeholder="sender@example.com"
                          />

                        </div>

                      </div>


                      <label>
                        Where did you receive it?
                      </label>

                      <select
                        value={source}
                        onChange={(e) =>
                          setSource(e.target.value)
                        }
                      >
                        <option value="">
                          Select source
                        </option>

                        <option>SMS</option>
                        <option>WhatsApp</option>
                        <option>Email</option>
                        <option>Other</option>
                      </select>

                    </>
                  )}


                  {/* LINK EXTRA DETAILS */}
                  {checkType === "link" && (
                    <div className="citizen-form-grid">

                      <div>

                        <label>
                          Sender / contact{" "}
                          <span className="optional-label">
                            optional
                          </span>
                        </label>

                        <input
                          value={senderPhone}
                          onChange={(e) =>
                            setSenderPhone(e.target.value)
                          }
                          placeholder="Phone or email"
                        />

                      </div>


                      <div>

                        <label>
                          Where did you receive it?
                        </label>

                        <select
                          value={source}
                          onChange={(e) =>
                            setSource(e.target.value)
                          }
                        >

                          <option value="">
                            Select source
                          </option>

                          <option>SMS</option>
                          <option>WhatsApp</option>
                          <option>Email</option>
                          <option>Website</option>
                          <option>Other</option>

                        </select>

                      </div>

                    </div>
                  )}


                  {/* PAYMENT EXTRA DETAILS */}
                  {checkType === "payment" && (

                    <div className="citizen-form-grid">

                      <div>

                        <label>
                          Transaction ID{" "}
                          <span className="optional-label">
                            optional
                          </span>
                        </label>

                        <input
                          value={transactionId}
                          onChange={(e) =>
                            setTransactionId(e.target.value)
                          }
                          placeholder="Reference number"
                        />

                      </div>


                      <div>

                        <label>
                          Amount{" "}
                          <span className="optional-label">
                            optional
                          </span>
                        </label>

                        <input
                          value={amount}
                          onChange={(e) =>
                            setAmount(e.target.value)
                          }
                          placeholder="₹ Amount"
                        />

                      </div>

                    </div>

                  )}


                  {/* CALL EXTRA DETAILS */}
                  {checkType === "call" && (

                    <>

                      <label>
                        Caller phone number
                      </label>

                      <input
                        value={senderPhone}
                        onChange={(e) =>
                          setSenderPhone(e.target.value)
                        }
                        placeholder="+91 XXXXX XXXXX"
                      />


                      <label>
                        What did they ask for?
                      </label>

                      <div className="citizen-checklist">

                        {[
                          "OTP",
                          "PIN / password",
                          "Bank details",
                          "Money transfer",
                          "Install an app",
                          "Click a link",
                        ].map((item) => (

                          <span key={item}>
                            <input type="checkbox" />
                            {" "}
                            {item}
                          </span>

                        ))}

                      </div>

                    </>

                  )}


                  {/* DESCRIPTION */}
                  <label>
                    Additional details{" "}
                    <span className="optional-label">
                      optional
                    </span>
                  </label>

                  <textarea
                    value={description}
                    onChange={(e) =>
                      setDescription(e.target.value)
                    }
                    placeholder="Anything else that seems suspicious?"
                    rows={3}
                  />


                  {/* EVIDENCE */}
                  <label>
                    Evidence{" "}
                    <span className="optional-label">
                      optional
                    </span>
                  </label>

                  <label className="citizen-upload">

                    <Upload size={18} />

                    <span>
                      {evidenceName ||
                        "Upload a screenshot or image"}
                    </span>

                    <input
                      type="file"
                      accept="image/*,.pdf"
                      onChange={handleEvidence}
                    />

                  </label>


                  {/* SUBMIT */}
                  <button
                    className="analyze-button"
                    type="submit"
                  >
                    {details.button}
                    <ChevronRight size={18} />
                  </button>

                </form>

              </>

            ) : (

              /* RESULT */
              <div className="citizen-result">

                <div className="citizen-result-top">

                  <div className="citizen-result-icon">
                    <AlertTriangle size={25} />
                  </div>

                  <span className="demo-result-label">
                    MULEX ASSESSMENT
                  </span>

                </div>


                <div className="citizen-risk-banner">

                  <div>

                    <small>
                      RISK ASSESSMENT
                    </small>

                    <strong>
                      HIGH RISK
                    </strong>

                  </div>

                  <div className="citizen-score">
                    87
                    <span>/100</span>
                  </div>

                </div>


                <div className="citizen-result-grid">

                  <div>

                    <small>
                      Likely scam type
                    </small>

                    <strong>
                      KYC / impersonation
                    </strong>

                  </div>


                  <div>

                    <small>
                      Confidence
                    </small>

                    <strong>
                      94%
                    </strong>

                  </div>

                </div>


                <div className="citizen-result-section">

                  <h3>
                    Why was this flagged?
                  </h3>

                  <ul>

                    <li>
                      Urgent or threatening language
                    </li>

                    <li>
                      Suspicious sender or identifier
                    </li>

                    <li>
                      Pattern matches previous reports
                    </li>

                  </ul>

                </div>


                <div className="citizen-result-section">

                  <h3>
                    What should you do?
                  </h3>

                  <p className="citizen-action-note">
                    Do not click suspicious links or share
                    OTPs, PINs or banking credentials.
                  </p>

                </div>


                <div className="citizen-result-section citizen-connection-note">

                  <strong>
                    Possible related activity
                  </strong>

                  <span>
                    MULEX can connect shared phone numbers,
                    URLs and payment identifiers across reports.
                  </span>

                </div>


                <div className="citizen-result-actions">

                  <button
                    className="secondary-button"
                    onClick={closeCheck}
                    type="button"
                  >
                    <ArrowLeft size={17} />
                    Back to dashboard
                  </button>


                  <button
                    className="primary-button"
                    onClick={() =>
                      alert(
                        "Investigation details will be available here."
                      )
                    }
                    type="button"
                  >
                    View details
                    <ChevronRight size={17} />
                  </button>

                </div>

              </div>

            )}

          </div>

        </div>

      )}

    </div>
  );
}

export default CitizenDashboard;