"""
Privacy Policy Page for CashFlow Engine.
GDPR-compliant privacy policy.
"""
import streamlit as st


def show_privacy_page():
    """
    Display the Privacy Policy page.
    Accessible without authentication for legal compliance.
    """

    # Custom styles for privacy page
    st.markdown("""
    <style>
        .privacy-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
        }

        .privacy-header {
            font-family: 'Exo 2', sans-serif;
            font-size: 32px;
            font-weight: 800;
            color: #302BFF;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 10px;
        }

        .privacy-subtitle {
            font-family: 'Poppins', sans-serif;
            font-size: 14px;
            color: #6B7280;
            margin-bottom: 40px;
        }

        .privacy-section {
            margin-bottom: 30px;
        }

        .privacy-section h2 {
            font-family: 'Exo 2', sans-serif;
            font-size: 18px;
            font-weight: 700;
            color: #4B5563;
            text-transform: uppercase;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #E5E7EB;
        }

        .privacy-section p, .privacy-section li {
            font-family: 'Poppins', sans-serif;
            font-size: 14px;
            color: #4B5563;
            line-height: 1.8;
        }

        .privacy-section ul {
            padding-left: 20px;
        }

        .privacy-section li {
            margin-bottom: 8px;
        }

        .contact-box {
            background-color: #F0F4FF;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }

        .back-button {
            margin-bottom: 30px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Back to Login button
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        if st.button("< Back", type="tertiary", key="back_to_login"):
            st.session_state.navigate_to_page = None
            st.session_state['show_privacy'] = False
            st.rerun()

    # Header
    st.markdown("""
        <div class="privacy-header">Privacy Policy</div>
        <div class="privacy-subtitle">Last updated: January 2026</div>
    """, unsafe_allow_html=True)

    # Section 1: Controller
    st.markdown("""
    <div class="privacy-section">
        <h2>1. Data Controller</h2>
        <p>
            The data controller responsible for your personal data is:<br><br>
            <strong>CashFlow Engine</strong><br>
            [Your Company Name]<br>
            [Your Address]<br>
            [Your City, Postal Code]<br>
            Germany<br><br>
            Email: privacy@cashflowengine.com
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Section 2: Data We Collect
    st.markdown("""
    <div class="privacy-section">
        <h2>2. Data We Collect</h2>
        <p>We collect and process the following personal data:</p>
        <ul>
            <li><strong>Account Data:</strong> Email address (required for authentication)</li>
            <li><strong>Profile Data:</strong> Display name (optional)</li>
            <li><strong>Usage Data:</strong> Your trading analyses and portfolio data that you upload</li>
            <li><strong>Technical Data:</strong> IP address, browser type, device information (for security)</li>
            <li><strong>Authentication Data:</strong> Login timestamps, session information</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Section 3: Purpose and Legal Basis
    st.markdown("""
    <div class="privacy-section">
        <h2>3. Purpose and Legal Basis</h2>
        <p>We process your data for the following purposes:</p>
        <ul>
            <li><strong>Account Management:</strong> To create and manage your user account (Legal basis: Contract performance, Art. 6(1)(b) GDPR)</li>
            <li><strong>Service Provision:</strong> To provide our portfolio analytics services (Legal basis: Contract performance, Art. 6(1)(b) GDPR)</li>
            <li><strong>Security:</strong> To protect our systems and your data (Legal basis: Legitimate interest, Art. 6(1)(f) GDPR)</li>
            <li><strong>Communication:</strong> To send you important service updates (Legal basis: Contract performance, Art. 6(1)(b) GDPR)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Section 4: Data Storage
    st.markdown("""
    <div class="privacy-section">
        <h2>4. Data Storage and Security</h2>
        <p>
            Your data is stored securely on servers located in the <strong>European Union (Frankfurt, Germany)</strong>.
            We use Supabase as our database provider, which is GDPR-compliant and provides:
        </p>
        <ul>
            <li>Encryption at rest (AES-256)</li>
            <li>Encryption in transit (TLS 1.3)</li>
            <li>Regular security audits</li>
            <li>Access controls and authentication</li>
        </ul>
        <p>
            Your trading data is stored exclusively in your personal account and is not shared with other users.
            Row-Level Security (RLS) ensures complete data isolation.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Section 5: Data Retention
    st.markdown("""
    <div class="privacy-section">
        <h2>5. Data Retention</h2>
        <p>We retain your personal data for as long as your account is active. Specifically:</p>
        <ul>
            <li><strong>Account Data:</strong> Until account deletion</li>
            <li><strong>Analysis Data:</strong> Until you delete it or close your account</li>
            <li><strong>Technical Logs:</strong> 90 days for security purposes</li>
        </ul>
        <p>
            When you delete your account, all your personal data will be permanently removed within 30 days,
            except where we are legally required to retain it.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Section 6: Your Rights
    st.markdown("""
    <div class="privacy-section">
        <h2>6. Your Rights (GDPR)</h2>
        <p>Under the GDPR, you have the following rights:</p>
        <ul>
            <li><strong>Right of Access (Art. 15):</strong> Request a copy of your personal data</li>
            <li><strong>Right to Rectification (Art. 16):</strong> Correct inaccurate data</li>
            <li><strong>Right to Erasure (Art. 17):</strong> Request deletion of your data ("Right to be forgotten")</li>
            <li><strong>Right to Restriction (Art. 18):</strong> Limit how we process your data</li>
            <li><strong>Right to Data Portability (Art. 20):</strong> Export your data in a machine-readable format</li>
            <li><strong>Right to Object (Art. 21):</strong> Object to processing based on legitimate interests</li>
            <li><strong>Right to Withdraw Consent:</strong> Withdraw consent at any time</li>
        </ul>
        <p>
            To exercise any of these rights, please contact us at <strong>privacy@cashflowengine.com</strong>.
            We will respond within 30 days.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Section 7: Third Parties
    st.markdown("""
    <div class="privacy-section">
        <h2>7. Third-Party Services</h2>
        <p>We use the following third-party services that may process your data:</p>
        <ul>
            <li>
                <strong>Supabase (Database & Authentication)</strong><br>
                Location: EU (Frankfurt)<br>
                Purpose: Data storage, user authentication<br>
                Privacy Policy: <a href="https://supabase.com/privacy" target="_blank">supabase.com/privacy</a>
            </li>
            <li>
                <strong>Google (OAuth Authentication)</strong><br>
                Location: EU/US (Standard Contractual Clauses)<br>
                Purpose: Optional Google Sign-In<br>
                Privacy Policy: <a href="https://policies.google.com/privacy" target="_blank">policies.google.com/privacy</a>
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Section 8: Cookies
    st.markdown("""
    <div class="privacy-section">
        <h2>8. Cookies and Local Storage</h2>
        <p>We use minimal cookies and local storage:</p>
        <ul>
            <li><strong>Authentication Cookies:</strong> Essential for keeping you logged in (Session cookie)</li>
            <li><strong>Session Storage:</strong> Temporary data for your current session</li>
        </ul>
        <p>
            We do not use tracking cookies, advertising cookies, or third-party analytics cookies.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Section 9: Data Breach
    st.markdown("""
    <div class="privacy-section">
        <h2>9. Data Breach Notification</h2>
        <p>
            In the event of a personal data breach that poses a risk to your rights and freedoms,
            we will notify you and the relevant supervisory authority within 72 hours of becoming aware of the breach,
            as required by Art. 33 and Art. 34 GDPR.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Section 10: Contact
    st.markdown("""
    <div class="privacy-section">
        <h2>10. Contact & Complaints</h2>
        <div class="contact-box">
            <p>
                <strong>For privacy-related inquiries:</strong><br>
                Email: privacy@cashflowengine.com<br><br>

                <strong>Supervisory Authority:</strong><br>
                If you believe we have not adequately addressed your concerns, you have the right to lodge a complaint
                with a data protection supervisory authority. In Germany, this is typically the data protection authority
                of your federal state (Landesdatenschutzbeauftragter).
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Section 11: Changes
    st.markdown("""
    <div class="privacy-section">
        <h2>11. Changes to This Policy</h2>
        <p>
            We may update this Privacy Policy from time to time. We will notify you of any material changes
            by email or through a notice on our website. The date of the last update is shown at the top of this page.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Footer spacing
    st.write("")
    st.write("")
    st.markdown("---")
    st.caption("CashFlow Engine | Advanced Portfolio Analytics for Option Traders")
