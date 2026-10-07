import { useEffect, useState } from "react";

import {
  Shield,
  Search,
  LayoutDashboard,
  FolderSearch,
  Network,
  Target,
  FileText,
  Settings,
  Bell,
  ChevronRight,
  CheckCircle2,
  Clock3,
  AlertTriangle,
  Phone,
  Link2,
  CreditCard,
  Users,
  ArrowLeft,
  Eye,
  Download,
  LogOut,
} from "lucide-react";

import "./App.css";

import InvestigatorLogin from "./pages/InvestigatorLogin";
import CitizenLogin from "./pages/CitizenLogin";
import CitizenDashboard from "./pages/CitizenDashboard";

function App() {
  const [authView, setAuthView] = useState(() => {
    if (localStorage.getItem("mulex_investigator")) return "investigator";
    if (localStorage.getItem("mulex_citizen")) return "citizen";
    return "citizen";
  });

  const [investigatorView, setInvestigatorView] =
    useState("overview");

  const [investigationFilter, setInvestigationFilter] =
    useState("All");

  const [investigationSearch, setInvestigationSearch] =
    useState("");

  const investigator = JSON.parse(
    localStorage.getItem("mulex_investigator") || "{}"
  );

  const citizen = JSON.parse(
    localStorage.getItem("mulex_citizen") || "{}"
  );

  /* --------------------------------------------------
     CITIZEN SESSION
  -------------------------------------------------- */

  if (localStorage.getItem("mulex_citizen")) {
    return (
      <CitizenDashboard
        citizen={citizen}
        onLogout={() => {
          localStorage.removeItem("mulex_citizen");
          localStorage.removeItem("mulex_investigator");
          window.location.reload();
        }}
      />
    );
  }

  /* --------------------------------------------------
     LOGIN
  -------------------------------------------------- */

  if (
    !localStorage.getItem("mulex_investigator") &&
    !localStorage.getItem("mulex_citizen")
  ) {
    if (authView === "investigator") {
      return (
        <InvestigatorLogin
          onSwitchToCitizen={() => setAuthView("citizen")}
        />
      );
    }

    return (
      <CitizenLogin
        onSwitchToSignup={() =>
          alert("Citizen signup coming next!")
        }
        onSwitchToInvestigator={() =>
          setAuthView("investigator")
        }
      />
    );
  }

  /* --------------------------------------------------
     HELPERS
  -------------------------------------------------- */

  const getInitials = (name) => {
    return (name || "Investigator")
      .split(" ")
      .map((word) => word[0])
      .join("")
      .slice(0, 2)
      .toUpperCase();
  };

  const handleLogout = () => {
    localStorage.removeItem("mulex_investigator");
    localStorage.removeItem("mulex_citizen");
    window.location.reload();
  };

  /* --------------------------------------------------
     NAVIGATION
  -------------------------------------------------- */

  const navItems = [
    {
      id: "overview",
      label: "Overview",
      icon: LayoutDashboard,
    },
    {
      id: "investigations",
      label: "Investigations",
      icon: FolderSearch,
    },
    {
      id: "campaigns",
      label: "Campaigns",
      icon: Target,
    },
    {
      id: "network",
      label: "Fraud Network",
      icon: Network,
    },
    {
      id: "evidence",
      label: "Evidence",
      icon: FileText,
    },
  ];

  const pageTitles = {
    overview: "Investigator Overview",
    investigations: "Investigations",
    campaigns: "Campaign Intelligence",
    network: "Fraud Network",
    evidence: "Evidence Review",
    settings: "Settings",
  };

  /* --------------------------------------------------
     INVESTIGATION DATA
  -------------------------------------------------- */

  const investigations = [
    {
      id: "INC-1042",
      type: "KYC impersonation",
      risk: "HIGH",
      score: 91,
      campaign: "CAM-042",
      entity: "+91 98765 43210",
      status: "Active",
    },
    {
      id: "INC-1041",
      type: "UPI fraud",
      risk: "HIGH",
      score: 87,
      campaign: "CAM-042",
      entity: "sbi.kyc.verify@upi",
      status: "Active",
    },
    {
      id: "INC-1038",
      type: "Phishing link",
      risk: "MEDIUM",
      score: 64,
      campaign: "CAM-039",
      entity: "secure-bank-check.com",
      status: "Review",
    },
    {
      id: "INC-1036",
      type: "Prize scam",
      risk: "LOW",
      score: 28,
      campaign: "—",
      entity: "+91 91234 56789",
      status: "Cleared",
    },
  ];

  const filteredInvestigations =
    investigations.filter((item) => {
      const matchesFilter =
        investigationFilter === "All" ||
        (investigationFilter === "High Risk" &&
          item.risk === "HIGH") ||
        (investigationFilter === "Under Review" &&
          item.status === "Review") ||
        (investigationFilter === "Cleared" &&
          item.status === "Cleared");

      const search =
        investigationSearch.toLowerCase().trim();

      const matchesSearch =
        !search ||
        item.id.toLowerCase().includes(search) ||
        item.type.toLowerCase().includes(search) ||
        item.campaign.toLowerCase().includes(search) ||
        item.entity.toLowerCase().includes(search);

      return matchesFilter && matchesSearch;
    });

  /* --------------------------------------------------
     HEADER
  -------------------------------------------------- */

  const Header = () => (
    <header className="topbar">
      <div>
        <span className="breadcrumb">
          MULEX WORKSPACE
        </span>

        <h1>
          {pageTitles[investigatorView]}
        </h1>
      </div>

      <div className="top-actions">
        <button
          className="icon-button"
          type="button"
        >
          <Bell size={19} />

          <span className="notification-dot" />
        </button>

        <div className="top-avatar">
          {getInitials(investigator.name)}
        </div>
      </div>
    </header>
  );

  /* --------------------------------------------------
     OVERVIEW
  -------------------------------------------------- */

  const Overview = () => (
    <>
      <div className="investigator-hero">

        <div>
          <p className="eyebrow">
            FRAUD INTELLIGENCE PLATFORM
          </p>

          <h2>
            Investigate fraud
            <br />
            <span>before it spreads.</span>
          </h2>

          <p className="welcome-text">
            Review suspicious incidents, identify
            related campaigns and trace the financial
            network behind coordinated fraud.
          </p>
        </div>

        <div className="hero-action-card">
          <Search size={22} />

          <strong>
            Start an investigation
          </strong>

          <span>
            Review the latest high-risk incidents
          </span>

          <button
            className="primary-button"
            type="button"
            onClick={() =>
              setInvestigatorView(
                "investigations"
              )
            }
          >
            Open investigations
            <ChevronRight size={17} />
          </button>
        </div>

      </div>


      <div className="stats-grid investigator-stats">

        <div className="stat-card">
          <div className="stat-top">
            <span>
              Active investigations
            </span>

            <div className="stat-icon blue">
              <FolderSearch size={18} />
            </div>
          </div>

          <strong>18</strong>

          <span className="stat-change">
            5 require attention
          </span>
        </div>


        <div className="stat-card">
          <div className="stat-top">
            <span>
              High-risk cases
            </span>

            <div className="stat-icon red">
              <AlertTriangle size={18} />
            </div>
          </div>

          <strong>07</strong>

          <span className="stat-change danger">
            Requires attention
          </span>
        </div>


        <div className="stat-card">
          <div className="stat-top">
            <span>
              Active campaigns
            </span>

            <div className="stat-icon orange">
              <Target size={18} />
            </div>
          </div>

          <strong>03</strong>

          <span className="stat-change warning">
            1 newly detected
          </span>
        </div>


        <div className="stat-card">
          <div className="stat-top">
            <span>
              Connected entities
            </span>

            <div className="stat-icon green">
              <Network size={18} />
            </div>
          </div>

          <strong>42</strong>

          <span className="stat-change">
            Across active campaigns
          </span>
        </div>

      </div>


      <div className="section-heading activity-heading">

        <div>
          <h3>
            Recent investigations
          </h3>

          <p>
            Latest activity across the workspace
          </p>
        </div>

        <button
          className="view-all"
          type="button"
          onClick={() =>
            setInvestigatorView(
              "investigations"
            )
          }
        >
          View all
          <ChevronRight size={16} />
        </button>

      </div>


      <div className="activity-card">

        {investigations
          .slice(0, 3)
          .map((item) => (

            <div
              className="activity-row"
              key={item.id}
            >

              <div className="activity-main">

                <div
                  className={`activity-icon ${
                    item.risk === "HIGH"
                      ? "danger-bg"
                      : item.risk === "MEDIUM"
                      ? "warning-bg"
                      : "success-bg"
                  }`}
                >
                  {item.risk === "HIGH" ? (
                    <AlertTriangle size={18} />
                  ) : item.risk === "MEDIUM" ? (
                    <Clock3 size={18} />
                  ) : (
                    <CheckCircle2
                      size={18}
                    />
                  )}
                </div>

                <div>
                  <strong>
                    {item.id} • {item.type}
                  </strong>

                  <span>
                    Campaign{" "}
                    {item.campaign} • Entity{" "}
                    {item.entity}
                  </span>
                </div>

              </div>


              <span
                className={`risk-badge ${
                  item.risk === "HIGH"
                    ? "high"
                    : item.risk === "MEDIUM"
                    ? "medium"
                    : "safe"
                }`}
              >
                {item.risk === "HIGH"
                  ? "High Risk"
                  : item.risk === "MEDIUM"
                  ? "Under Review"
                  : "Cleared"}
              </span>

            </div>

          ))}

      </div>
    </>
  );

  /* --------------------------------------------------
     INVESTIGATIONS
  -------------------------------------------------- */

  const Investigations = () => (
    <>
      <div className="investigator-page-heading">

        <div>

          <p className="eyebrow">
            CASE WORKSPACE
          </p>

          <h2>
            Investigations
          </h2>

          <p>
            Review incidents, evidence and
            related fraud intelligence.
          </p>

        </div>


        <div className="investigator-search">

          <Search size={17} />

          <input
            type="search"
            value={investigationSearch}
            onChange={(e) =>
              setInvestigationSearch(
                e.target.value
              )
            }
            placeholder="Search incident, entity or campaign..."
          />

        </div>

      </div>


      <div className="investigation-filters">

        {[
          "All",
          "High Risk",
          "Under Review",
          "Cleared",
        ].map((filter) => (

          <button
            key={filter}
            className={`filter-pill ${
              investigationFilter === filter
                ? "active"
                : ""
            }`}
            type="button"
            onClick={() =>
              setInvestigationFilter(filter)
            }
          >
            {filter}
          </button>

        ))}

      </div>


      <div className="investigation-table-card">

        <div className="investigation-table-header">
          <span>Incident</span>
          <span>Type</span>
          <span>Risk</span>
          <span>Campaign</span>
          <span>Entity</span>
          <span>Status</span>
          <span />
        </div>


        {filteredInvestigations.length > 0 ? (

          filteredInvestigations.map(
            (item) => (

              <div
                className="investigation-table-row"
                key={item.id}
              >

                <strong>
                  {item.id}
                </strong>

                <span>
                  {item.type}
                </span>


                <span
                  className={`table-risk ${
                    item.risk === "HIGH"
                      ? "high"
                      : item.risk === "MEDIUM"
                      ? "medium"
                      : "safe"
                  }`}
                >
                  {item.score}/100
                </span>


                <span>
                  {item.campaign}
                </span>


                <span>
                  {item.entity}
                </span>


                <span>
                  {item.status}
                </span>


                <button
                  className="row-action"
                  type="button"
                  onClick={() =>
                    setInvestigatorView(
                      "evidence"
                    )
                  }
                >
                  <Eye size={15} />
                  Review
                </button>

              </div>

            )
          )

        ) : (

          <div className="investigation-empty-state">

            <Search size={22} />

            <strong>
              No investigations found
            </strong>

            <span>
              Try another filter or search term.
            </span>

          </div>

        )}

      </div>
    </>
  );

  /* --------------------------------------------------
     CAMPAIGNS
  -------------------------------------------------- */

  const Campaigns = () => (
    <>
      <div className="investigator-page-heading">

        <div>

          <p className="eyebrow">
            CAMPAIGN INTELLIGENCE
          </p>

          <h2>
            Fraud campaigns
          </h2>

          <p>
            Grouped incidents connected by
            shared indicators and entities.
          </p>

        </div>

      </div>


      <div className="campaign-detail-card">

        <div className="campaign-title-row">

          <div>

            <span className="eyebrow">
              ACTIVE CAMPAIGN
            </span>

            <h2>
              Campaign #042 —
              KYC Impersonation Network
            </h2>

          </div>


          <span className="campaign-active">
            ACTIVE
          </span>

        </div>


        <div className="campaign-stats">

          <div>

            <small>
              Risk score
            </small>

            <strong className="campaign-high">
              91 <span>/100</span>
            </strong>

          </div>


          <div>

            <small>
              Reports
            </small>

            <strong>
              18
            </strong>

          </div>


          <div>

            <small>
              Victims
            </small>

            <strong>
              13
            </strong>

          </div>


          <div>

            <small>
              Entities
            </small>

            <strong>
              9
            </strong>

          </div>

        </div>


        <div className="campaign-columns">

          <div className="campaign-panel">

            <h3>
              Common indicators
            </h3>


            <div className="indicator-line">
              <AlertTriangle size={16} />
              Same suspicious domain
            </div>


            <div className="indicator-line">
              <AlertTriangle size={16} />
              Repeated KYC impersonation
            </div>


            <div className="indicator-line">
              <AlertTriangle size={16} />
              Shared UPI identifier
            </div>


            <div className="indicator-line">
              <AlertTriangle size={16} />
              Similar scam message pattern
            </div>

          </div>


          <div className="campaign-panel">

            <h3>
              Connected entities
            </h3>


            <div className="entity-mini-grid">

              <div>
                <Phone size={17} />
                <strong>4</strong>
                <span>
                  Phone numbers
                </span>
              </div>


              <div>
                <CreditCard size={17} />
                <strong>3</strong>
                <span>
                  UPI IDs
                </span>
              </div>


              <div>
                <Link2 size={17} />
                <strong>2</strong>
                <span>
                  URLs
                </span>
              </div>


              <div>
                <Users size={17} />
                <strong>2</strong>
                <span>
                  Mule accounts
                </span>
              </div>

            </div>

          </div>

        </div>


        <div className="campaign-actions">

          <button
            className="primary-button"
            type="button"
            onClick={() =>
              setInvestigatorView("network")
            }
          >
            <Network size={17} />
            Explore fraud network
          </button>


          <button
            className="secondary-button"
            type="button"
            onClick={() =>
              setInvestigatorView("evidence")
            }
          >
            <FileText size={17} />
            Review evidence
          </button>


          <button
            className="secondary-button"
            type="button"
            onClick={() =>
              alert(
                "Case package generation will be connected to the backend."
              )
            }
          >
            <Download size={17} />
            Generate case package
          </button>

        </div>

      </div>
    </>
  );

  /* --------------------------------------------------
     NETWORK
  -------------------------------------------------- */

  const NetworkView = () => {

    const [networkData, setNetworkData] =
      useState(null);

    const [networkError, setNetworkError] =
      useState("");

    useEffect(() => {

      fetch("/mulex_data.json")

        .then((response) => {

          if (!response.ok) {
            throw new Error(
              "Unable to load MULEX graph data."
            );
          }

          return response.json();

        })

        .then((data) => {

          const campaignId = "CAMP007";
          const accountId = "ACC0905";


          const campaign =
            data.campaigns?.find(
              (item) =>
                item.id === campaignId
            ) || null;


          const incidents =
            data.incidents?.filter(
              (item) =>
                item.campaign_id ===
                campaignId
            ) || [];


          const accountTransactions =
            data.transactions?.filter(
              (item) =>
                item.sender ===
                  accountId ||
                item.receiver ===
                  accountId
            ) || [];


          const connectedAccounts = [
            ...new Set(
              accountTransactions.map(
                (transaction) =>
                  transaction.sender ===
                  accountId
                    ? transaction.receiver
                    : transaction.sender
              )
            ),
          ];


          const muleAccount =
            data.mule_accounts?.includes(
              accountId
            );


          setNetworkData({
            campaign,
            incidents,
            accountTransactions,
            connectedAccounts,
            muleAccount,
          });

        })

        .catch((error) => {

          console.error(error);

          setNetworkError(
            error.message
          );

        });

    }, []);


    if (networkError) {

      return (
        <div className="investigator-page-heading">

          <div>

            <p className="eyebrow">
              RELATIONSHIP GRAPH
            </p>

            <h2>
              Fraud Network
            </h2>

            <p>
              {networkError}
            </p>

          </div>

        </div>
      );
    }


    if (!networkData) {

      return (
        <div className="investigator-page-heading">

          <div>

            <p className="eyebrow">
              RELATIONSHIP GRAPH
            </p>

            <h2>
              Loading fraud network...
            </h2>

            <p>
              Loading synthetic MULEX
              intelligence data.
            </p>

          </div>

        </div>
      );
    }


    const {
      campaign,
      incidents,
      accountTransactions,
      connectedAccounts,
      muleAccount,
    } = networkData;


    return (
      <>
        <div className="investigator-page-heading">

          <div>

            <p className="eyebrow">
              RELATIONSHIP GRAPH
            </p>

            <h2>
              Fraud Network —{" "}
              {campaign?.id ||
                "CAMP007"}
            </h2>

            <p>
              Incident → Campaign →
              Account → Transactions →
              Connected Accounts
            </p>

          </div>

        </div>


        <div className="network-layout">

          <div className="network-card">

            <div className="network-map">

              {/* INCIDENTS */}

              <div className="network-column victims">

                {incidents
                  .slice(0, 4)
                  .map((incident) => (

                    <div
                      className="network-node incident"
                      key={incident.id}
                    >
                      Incident

                      <span>
                        {incident.id}
                      </span>
                    </div>

                  ))}

              </div>


              {/* CAMPAIGN */}

              <div className="network-column center">

                <div className="network-node campaign-node">

                  {campaign?.id ||
                    "CAMP007"}

                  <span>
                    {campaign?.scam_type ||
                      "Fraud Campaign"}
                  </span>

                </div>

              </div>


              {/* FOCUS ACCOUNT */}

              <div className="network-column">

                <div className="network-node entity-node">

                  Account

                  <span>
                    ACC0905
                  </span>

                </div>


                <div className="network-node entity-node">

                  Transactions

                  <span>
                    {
                      accountTransactions.length
                    }
                  </span>

                </div>

              </div>


              {/* CONNECTED ACCOUNTS */}

              <div className="network-column">

                {connectedAccounts
                  .slice(0, 3)
                  .map((account) => (

                    <div
                      className="network-node mule-node"
                      key={account}
                    >
                      Connected Account

                      <span>
                        {account}
                      </span>

                    </div>

                  ))}

              </div>


              {/* TRANSACTIONS */}

              <div className="network-column">

                {accountTransactions
                  .slice(0, 3)
                  .map((transaction) => (

                    <div
                      className="network-node beneficiary-node"
                      key={transaction.id}
                    >
                      Transaction

                      <span>
                        {transaction.id}
                      </span>

                    </div>

                  ))}

              </div>

            </div>


            {/* SUMMARY */}

            <div className="network-summary">

              <span>
                {incidents.length} Campaign
                Incidents
              </span>

              <span>
                {
                  accountTransactions.length
                } Transactions
              </span>

              <span>
                {
                  connectedAccounts.length
                } Connected Accounts
              </span>

              <span>
                Focus Account: ACC0905
              </span>

              {muleAccount && (
                <span>
                  Mule Account Detected
                </span>
              )}

            </div>

          </div>


          {/* SELECTED ENTITY */}

          <aside className="selected-node-card">

            <span className="eyebrow">
              SELECTED ENTITY
            </span>

            <h3>
              Account: ACC0905
            </h3>


            <div className="node-stat">

              <span>
                Campaign
              </span>

              <strong>
                {campaign?.id ||
                  "CAMP007"}
              </strong>

            </div>


            <div className="node-stat">

              <span>
                Scam type
              </span>

              <strong>
                {campaign?.scam_type ||
                  "Loan Scam"}
              </strong>

            </div>


            <div className="node-stat">

              <span>
                Transactions
              </span>

              <strong>
                {
                  accountTransactions.length
                }
              </strong>

            </div>


            <div className="node-stat">

              <span>
                Connected accounts
              </span>

              <strong>
                {
                  connectedAccounts.length
                }
              </strong>

            </div>


            <div className="node-stat">

              <span>
                Mule status
              </span>

              <strong
                className={
                  muleAccount
                    ? "high-text"
                    : ""
                }
              >
                {muleAccount
                  ? "MULE"
                  : "NORMAL"}
              </strong>

            </div>


            <button
              className="secondary-button full-button"
              type="button"
              onClick={() =>
                setInvestigatorView(
                  "evidence"
                )
              }
            >
              <FileText size={17} />
              Review evidence
            </button>

          </aside>

        </div>
      </>
    );
  };

  /* --------------------------------------------------
     EVIDENCE
  -------------------------------------------------- */

  const Evidence = () => (
    <>
      <div className="investigator-page-heading">

        <div>

          <p className="eyebrow">
            CASE EVIDENCE
          </p>

          <h2>
            Evidence Review —
            Campaign #042
          </h2>

          <p>
            Review the evidence and signals
            supporting the campaign assessment.
          </p>

        </div>

      </div>


      <div className="evidence-stack">

        <section className="evidence-card">

          <span className="eyebrow">
            INCIDENT REPORTS
          </span>

          <h3>
            18 linked reports
          </h3>

          <div className="evidence-list">

            <span>
              First observed:
              05 Oct 2026
            </span>

            <span>
              Latest report:
              06 Oct 2026
            </span>

            <span>
              13 affected victims
            </span>

          </div>

        </section>


        <section className="evidence-card">

          <span className="eyebrow">
            DIGITAL EVIDENCE
          </span>

          <div className="evidence-list">

            <span>
              <CheckCircle2 size={15} />
              Screenshot of scam message
            </span>

            <span>
              <Link2 size={15} />
              Suspicious URL:
              sbi-verify-kyc.com
            </span>

            <span>
              <Phone size={15} />
              Phone number:
              +91 98765 43210
            </span>

            <span>
              <CreditCard size={15} />
              UPI:
              sbi.kyc.verify@upi
            </span>

            <span>
              <FileText size={15} />
              Original message text
            </span>

          </div>

        </section>


        <section className="evidence-card">

          <span className="eyebrow">
            AI FINDINGS
          </span>

          <div className="finding-tags">

            <span>
              Bank impersonation
            </span>

            <span>
              KYC scam pattern
            </span>

            <span>
              Urgency language
            </span>

            <span>
              Repeated URL
            </span>

          </div>

        </section>


        <section className="evidence-card">

          <span className="eyebrow">
            NETWORK EVIDENCE
          </span>

          <p className="network-evidence-text">
            Victims → Incidents →
            Campaign → Mule Accounts →
            Transactions → Beneficiary
          </p>

        </section>


        <section className="evidence-card">

          <span className="eyebrow">
            TIMELINE
          </span>

          <div className="timeline">

            <div>
              <strong>
                05 Oct 2026
              </strong>

              <span>
                First report filed
              </span>
            </div>


            <div>
              <strong>
                05 Oct 2026
              </strong>

              <span>
                Domain linked across
                multiple reports
              </span>
            </div>


            <div>
              <strong>
                06 Oct 2026
              </strong>

              <span>
                Campaign escalated to HIGH
              </span>
            </div>


            <div>
              <strong>
                06 Oct 2026
              </strong>

              <span>
                Mule account linkage identified
              </span>
            </div>

          </div>

        </section>


        <div className="campaign-actions">

          <button
            className="secondary-button"
            type="button"
            onClick={() =>
              setInvestigatorView(
                "campaigns"
              )
            }
          >
            <ArrowLeft size={17} />
            Back to campaign
          </button>


          <button
            className="primary-button"
            type="button"
            onClick={() =>
              alert(
                "Evidence package generation will be connected to the backend."
              )
            }
          >
            <Download size={17} />
            Generate evidence package
          </button>

        </div>

      </div>
    </>
  );

  /* --------------------------------------------------
     SETTINGS
  -------------------------------------------------- */

  const SettingsView = () => (
    <div className="investigator-page-heading">

      <div>

        <p className="eyebrow">
          ACCOUNT
        </p>

        <h2>
          Settings
        </h2>

        <p>
          Investigator account and
          workspace preferences.
        </p>

      </div>

    </div>
  );

  /* --------------------------------------------------
     PAGE SWITCH
  -------------------------------------------------- */

  const renderPage = () => {

    if (investigatorView === "overview") {
      return <Overview />;
    }

    if (
      investigatorView ===
      "investigations"
    ) {
      return <Investigations />;
    }

    if (investigatorView === "campaigns") {
      return <Campaigns />;
    }

    if (investigatorView === "network") {
      return <NetworkView />;
    }

    if (investigatorView === "evidence") {
      return <Evidence />;
    }

    return <SettingsView />;
  };

  /* --------------------------------------------------
     INVESTIGATOR APP
  -------------------------------------------------- */

  return (
    <div className="app">

      <aside className="sidebar">

        <div className="brand">

          <div className="brand-icon">
            <Shield size={21} />
          </div>

          <div>
            <h2>MULEX</h2>
            <span>
              Fraud Intelligence
            </span>
          </div>

        </div>


        <nav className="navigation">

          {navItems.map((item) => {

            const Icon = item.icon;

            return (
              <button
                key={item.id}
                type="button"
                className={`nav-item ${
                  investigatorView ===
                  item.id
                    ? "active"
                    : ""
                }`}
                onClick={() =>
                  setInvestigatorView(
                    item.id
                  )
                }
              >
                <Icon size={18} />
                {item.label}
              </button>
            );

          })}


          <button
            type="button"
            className={`nav-item ${
              investigatorView ===
              "settings"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setInvestigatorView(
                "settings"
              )
            }
          >
            <Settings size={18} />
            Settings
          </button>

        </nav>


        <div className="sidebar-bottom">

          <div className="security-status">

            <div className="status-dot" />

            <div>

              <strong>
                Investigator access
              </strong>

              <span>
                Protected workspace
              </span>

            </div>

          </div>


          <div className="user-profile">

            <div className="avatar">
              {getInitials(
                investigator.name
              )}
            </div>


            <div className="user-info">

              <strong>
                {investigator.name ||
                  "Investigator"}
              </strong>

              <span>
                {investigator.role ||
                  "Investigator account"}
              </span>

            </div>


            <button
              className="logout-button"
              onClick={handleLogout}
              type="button"
            >
              <LogOut size={15} />
            </button>

          </div>

        </div>

      </aside>


      <main className="main">

        <Header />

        <section className="content">
          {renderPage()}
        </section>

      </main>

    </div>
  );
}

export default App;