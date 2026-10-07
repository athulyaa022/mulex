import { useState } from "react";
import { ShieldCheck, LockKeyhole, Mail, ArrowRight } from "lucide-react";

function InvestigatorLogin({ onSwitchToCitizen }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = (e) => {
  e.preventDefault();

  // Demo investigator credentials
  const demoEmail = "investigator@mulex.com";
  const demoPassword = "mulex123";

  if (email === demoEmail && password === demoPassword) {
    localStorage.setItem(
      "mulex_investigator",
      JSON.stringify({
        name: "MULEX Investigator",
        email: demoEmail,
        role: "Investigator",
      })
    );

    window.location.reload();
  } else {
    alert("Invalid investigator ID/email or password.");
  }
};

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="auth-logo">
            <ShieldCheck size={25} />
          </div>

          <div>
            <h1>MULEX</h1>
            <p>Fraud Intelligence</p>
          </div>
        </div>

        <div className="auth-heading">
          <span>INVESTIGATOR PORTAL</span>
          <h2>Sign in to MULEX</h2>
          <p>
            Access fraud investigations, campaign intelligence and network
            analysis.
          </p>
        </div>

        <form onSubmit={handleLogin} className="auth-form">
          <label>
            Investigator ID or Email
          </label>

          <div className="auth-input">
            <Mail size={18} />
            <input
              type="text"
              placeholder="Enter your ID or email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <label>
            Password
          </label>

          <div className="auth-input">
            <LockKeyhole size={18} />
            <input
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <div className="auth-options">
            <label className="remember-me">
              <input type="checkbox" />
              <span>Remember me</span>
            </label>

            <button type="button" className="forgot-password">
              Forgot password?
            </button>
          </div>

          <button type="submit" className="auth-submit">
            Sign in
            <ArrowRight size={18} />
          </button>
        </form>

        <div className="auth-security">
          <LockKeyhole size={16} />
          <span>Authorized investigator access</span>
        </div>

        <div className="auth-footer">
          <p>
            Citizen?
            <button 
                type="button" 
                onClick={onSwitchToCitizen}
            >
              Use Citizen Portal
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

export default InvestigatorLogin;