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
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState("");

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
    setAnalysisResult(null);
    setAnalysisError("");
    setIsAnalyzing(false);
  };

  const closeCheck = () => {
    setCheckType(null);
    setShowResult(false);
    setAnalysisResult(null);
    setAnalysisError("");
    setIsAnalyzing(false);
  };

  const handleEvidence = (e) => {
    const file = e.target.files?.[0];

    if (file) {
      setEvidenceName(file.name);
    }
  };

  /*
   * Send the citizen's information to the MULEX backend.
   *
   * Backend endpoint:
   * POST http://127.0.0.1:8000/api/v1/analyze
   */
  const handleAnalyze = async (e) => {
    e.preventDefault();

    if (!inputValue.trim() && !description.trim()) {
      alert(
        "Please enter the suspicious information before continuing."
      );
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError("");
    setAnalysisResult(null);
    setShowResult(false);

    /*
     * Combine the information entered by the citizen into
     * one piece of text for the analysis engine.
     */
    const parts = [];

    if (inputValue.trim()) {
      parts.push(`Suspicious content: ${inputValue.trim()}`);
    }

    if (senderPhone.trim()) {
      parts.push(`Sender phone: ${senderPhone.trim()}`);
    }

    if (senderEmail.trim()) {
      parts.push(`Sender email: ${senderEmail.trim()}`);
    }

    if (source.trim()) {
      parts.push(`Source: ${source.trim()}`);
    }

    if (transactionId.trim()) {
      parts.push(`Transaction ID: ${transactionId.trim()}`);
    }

    if (amount.trim()) {
      parts.push(`Amount: ${amount.trim()}`);
    }

    if (description.trim()) {
      parts.push(`Additional details: ${description.trim()}`);
    }

    const analysisText = parts.join("\n");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/v1/analyze",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            text: analysisText,
            source: "citizen",
          }),
        }
      );

      if (!response.ok) {
        let errorMessage = `Analysis failed with status ${response.status}.`;

        try {
          const errorData = await response.json();

          if (errorData?.error?.message) {
            errorMessage = errorData.error.message;
          } else if (errorData?.detail) {
            errorMessage =
              typeof errorData.detail === "string"
                ? errorData.detail
                : "The backend rejected the analysis request.";
          }
        } catch {
          // Keep the default error message.
        }

        throw new Error(errorMessage);
      }

      const data = await response.json();

      setAnalysisResult(data);
      setShowResult(true);
    } catch (error) {
      console.error("MULEX analysis error:", error);

      setAnalysisError(
        error?.message ||
          "Unable to connect to the MULEX analysis service."
      );
    } finally {
      setIsAnalyzing(false);
    }
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

  /*
   * Convert backend scam type such as KYC_SCAM
   * into a readable label.
   */
  const formatScamType = (value) => {
    if (!value) {
      return "Unknown";
    }

    return value
      .replaceAll("_", " ")
      .toLowerCase()
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  };

  /*
   * Convert backend risk level into a CSS class.
   */
  const getRiskClass = (riskLevel) => {
    const level = String(riskLevel || "LOW").toLowerCase();

    if (level === "critical") {
      return "high";
    }

    if (level === "high") {
      return "high";
    }

    if (level === "medium") {
      return "medium";
    }

    return "safe";
  };

  /*
   * Convert confidence such as 0.92 into 92%.
   */
  const formatConfidence = (confidence) => {
    if (confidence === null || confidence === undefined) {
      return "N/A";
    }

    const numericConfidence = Number(confidence);

    if (Number.isNaN(numericConfidence)) {
      return "N/A";
    }

    return `${Math.round(
      numericConfidence <= 1
        ? numericConfidence * 100
        : numericConfidence
    )}%`;
  };

  /*
   * Safely get the indicators returned by the backend.
   */
  const getIndicators = () => {
    if (!analysisResult) {
      return [];
    }

    if (
      Array.isArray(analysisResult.indicators) &&
      analysisResult.indicators.length > 0
    ) {
      return analysisResult.indicators;
    }

    return [];
  };

  /*
   * Safely get entities returned by the backend.
   */
  const getEntities = () => {
    if (!analysisResult) {
      return [];
    }

    if (
      Array.isArray(analysisResult.entities) &&
      analysisResult.entities.length > 0
    ) {
      return analysisResult.entities;
    }

    return [];
  };

  const riskLevel = analysisResult?.risk_level || "LOW";
  const riskScore = analysisResult?.risk_score ?? 0;
  const riskClass = getRiskClass(riskLevel);

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
            {(citizen?.name || "Citizen")
              .split(" ")
              .map((w) => w[0])
              .join("")
              .slice(0, 2)
              .toUpperCase()}
          </div>

          <div className="citizen-user-info">
            <strong>{citizen?.name || "Citizen"}</strong>

            <span>
              {citizen?.email || "Citizen account"}
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

                {/* BACKEND ERROR */}
                {analysisError && (
                  <div
                    style={{
                      marginTop: "16px",
                      padding: "12px 14px",
                      borderRadius: "10px",
                      background: "#fff1f2",
                      color: "#b91c1c",
                      border: "1px solid #fecdd3",
                      fontSize: "14px",
                    }}
                  >
                    {analysisError}
                  </div>
                )}

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
                    disabled={isAnalyzing}
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
                            disabled={isAnalyzing}
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
                            disabled={isAnalyzing}
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
                        disabled={isAnalyzing}
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
                          disabled={isAnalyzing}
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
                          disabled={isAnalyzing}
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
                          disabled={isAnalyzing}
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
                          disabled={isAnalyzing}
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
                        disabled={isAnalyzing}
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
                            <input
                              type="checkbox"
                              disabled={isAnalyzing}
                            />{" "}
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
                    disabled={isAnalyzing}
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
                      disabled={isAnalyzing}
                    />

                  </label>

                  {/* SUBMIT */}
                  <button
                    className="analyze-button"
                    type="submit"
                    disabled={isAnalyzing}
                  >

                    {isAnalyzing
                      ? "Analyzing..."
                      : details.button}

                    {!isAnalyzing && (
                      <ChevronRight size={18} />
                    )}

                  </button>

                </form>
              </>

            ) : (

              /* RESULT */
              <div className="citizen-result">

                <div className="citizen-result-top">

                  <div className="citizen-result-icon">
                    {riskClass === "safe" ? (
                      <CheckCircle2 size={25} />
                    ) : (
                      <AlertTriangle size={25} />
                    )}
                  </div>

                  <span className="demo-result-label">
                    MULEX ASSESSMENT
                  </span>

                </div>

                {/* RISK SCORE */}
                <div className="citizen-risk-banner">

                  <div>

                    <small>
                      RISK ASSESSMENT
                    </small>

                    <strong>
                      {String(riskLevel).toUpperCase()} RISK
                    </strong>

                  </div>

                  <div className="citizen-score">
                    {riskScore}
                    <span>/100</span>
                  </div>

                </div>

                {/* BASIC RESULT */}
                <div className="citizen-result-grid">

                  <div>

                    <small>
                      Likely scam type
                    </small>

                    <strong>
                      {formatScamType(
                        analysisResult?.scam_type
                      )}
                    </strong>

                  </div>

                  <div>

                    <small>
                      Confidence
                    </small>

                    <strong>
                      {formatConfidence(
                        analysisResult?.confidence
                      )}
                    </strong>

                  </div>

                </div>

                {/* INDICATORS */}
                <div className="citizen-result-section">

                  <h3>
                    Why was this flagged?
                  </h3>

                  <ul>

                    {getIndicators().length > 0 ? (
                      getIndicators().map((indicator, index) => (
                        <li key={index}>
                          {typeof indicator === "string"
                            ? indicator
                            : JSON.stringify(indicator)}
                        </li>
                      ))
                    ) : (
                      <>
                        <li>
                          MULEX analyzed the submitted content
                          using its fraud detection pipeline.
                        </li>

                        <li>
                          The result is based on the detected
                          fraud patterns and available identifiers.
                        </li>

                        {getEntities().length > 0 && (
                          <li>
                            Suspicious identifiers were extracted
                            from the submitted information.
                          </li>
                        )}
                      </>
                    )}

                  </ul>

                </div>

                {/* ENTITIES */}
                {getEntities().length > 0 && (
                  <div className="citizen-result-section">

                    <h3>
                      Detected identifiers
                    </h3>

                    <ul>
                      {getEntities().map((entity, index) => (
                        <li key={index}>
                          <strong>
                            {entity?.type ||
                              entity?.entity_type ||
                              "Identifier"}
                            :
                          </strong>{" "}
                          {entity?.value || "Unknown"}
                        </li>
                      ))}
                    </ul>

                  </div>
                )}

                {/* ACTION */}
                <div className="citizen-result-section">

                  <h3>
                    What should you do?
                  </h3>

                  <p className="citizen-action-note">

                    {String(riskLevel).toUpperCase() ===
                    "LOW"
                      ? "No strong fraud signal was detected. Still verify the source before sharing personal or financial information."
                      : "Do not click suspicious links or share OTPs, PINs or banking credentials. If money is involved, verify the recipient independently before paying."}

                  </p>

                </div>

                {/* NETWORK / CAMPAIGN CONNECTION */}
                {(analysisResult?.campaign_id ||
                  analysisResult?.related_incidents?.length >
                    0) && (
                  <div className="citizen-result-section citizen-connection-note">

                    <strong>
                      Possible related activity
                    </strong>

                    <span>

                      MULEX found connections with
                      previously analyzed activity.

                      {analysisResult?.campaign_id && (
                        <>
                          {" "}
                          Campaign:{" "}
                          <strong>
                            {analysisResult.campaign_id}
                          </strong>
                          .
                        </>
                      )}

                      {analysisResult?.related_incidents
                        ?.length > 0 && (
                        <>
                          {" "}
                          Related incidents:{" "}
                          {
                            analysisResult.related_incidents
                              .length
                          }
                          .
                        </>
                      )}

                    </span>

                  </div>
                )}

                {/* INCIDENT ID */}
                {analysisResult?.incident_id && (
                  <div
                    className="citizen-result-section"
                    style={{
                      fontSize: "13px",
                      opacity: 0.8,
                    }}
                  >
                    <strong>
                      Analysis ID:
                    </strong>{" "}
                    {analysisResult.incident_id}
                  </div>
                )}

                {/* ACTION BUTTONS */}
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
                    onClick={() => {
                      alert(
                        analysisResult?.incident_id
                          ? `Investigation ${analysisResult.incident_id} has been recorded.`
                          : "Investigation details are available in the MULEX system."
                      );
                    }}
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