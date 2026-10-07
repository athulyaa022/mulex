import { useState } from "react";
import {
  ShieldCheck,
  LockKeyhole,
  Mail,
  ArrowRight,
  UserRound,
} from "lucide-react";

function CitizenLogin({ onSwitchToSignup, onSwitchToInvestigator }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = (e) => {
    e.preventDefault();

    // Temporary demo citizen credentials
    const demoEmail = "citizen@mulex.com";
    const demoPassword = "citizen123";

    if (email === demoEmail && password === demoPassword) {
      localStorage.setItem(
        "mulex_citizen",
        JSON.stringify({
          name: "MULEX Citizen",
          email: demoEmail,
          role: "Citizen",
        })
      );

      window.location.reload();
    } else {
      alert("Invalid email or password.");
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        {/* BRAND */}
        <div className="auth-brand">
          <div className="auth-logo">
            <ShieldCheck size={25} />
          </div>

          <div>
            <h1>MULEX</h1>
            <p>Fraud Intelligence</p>
          </div>
        </div>

        {/* HEADING */}
        <div className="auth-heading">
          <span>CITIZEN PORTAL</span>

          <h2>Sign in to MULEX</h2>

          <p>
            Check suspicious messages, payments and links,
            and keep track of your previous investigations.
          </p>
        </div>

        {/* FORM */}
        <form onSubmit={handleLogin} className="auth-form">
          <label>Email address</label>

          <div className="auth-input">
            <Mail size={18} />

            <input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <label>Password</label>

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

            <button
              type="button"
              className="forgot-password"
            >
              Forgot password?
            </button>
          </div>

          <button type="submit" className="auth-submit">
            Sign in
            <ArrowRight size={18} />
          </button>
        </form>

        {/* SECURITY */}
        <div className="auth-security">
          <LockKeyhole size={16} />
          <span>Your information is kept secure</span>
        </div>

        {/* SIGN UP */}
        <div className="auth-footer">
          <p>
            New to MULEX?

            <button
              type="button"
              onClick={onSwitchToSignup}
            >
              Create an account
            </button>
          </p>
        </div>

        {/* INVESTIGATOR PORTAL */}
        <div className="auth-footer">
          <p>
            Investigator?

            <button
              type="button"
              onClick={onSwitchToInvestigator}
            >
              Use Investigator Portal
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

export default CitizenLogin;