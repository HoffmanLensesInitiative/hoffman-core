# Proton Mail Custom Domain Setup Guide
# Hoffman Lenses Initiative
# Prepared: 2026-03-30

---

## Overview

Proton Mail custom domain hosting allows all Hoffman Lenses email to:
- Use professional @hoffmanlenses.org addresses
- Benefit from Proton's end-to-end encryption
- Maintain zero-knowledge architecture (Proton cannot read emails)
- Keep family communications private and secure

This is the prerequisite for all advocacy outreach.

---

## Required Email Addresses

| Address | Purpose | Priority |
|---------|---------|----------|
| families@hoffmanlenses.org | Family outreach and support | HIGHEST — handle with extreme care |
| contact@hoffmanlenses.org | General inquiries | High |
| press@hoffmanlenses.org | Journalist inquiries | High |
| legal@hoffmanlenses.org | Attorney communications | High |
| privacy@hoffmanlenses.org | Privacy policy inquiries | Standard |

---

## Setup Steps

### Step 1: Proton Mail Account
- Go to proton.me/mail
- Select a plan that supports custom domains (Mail Plus or higher)
- Create the primary account (suggest: norm@hoffmanlenses.org or admin@hoffmanlenses.org)

### Step 2: Add Custom Domain
- In Proton Mail, go to Settings → Domain names → Add domain
- Enter: hoffmanlenses.org
- Proton will provide DNS records to add

### Step 3: DNS Configuration (Cloudflare)
Since hoffmanlenses.org is hosted on Cloudflare, add these records in the Cloudflare dashboard:

**MX Records (for receiving mail):**
```
Type: MX
Name: @
Mail server: mail.protonmail.ch
Priority: 10

Type: MX
Name: @
Mail server: mailsec.protonmail.ch
Priority: 20
```

**SPF Record (for sending mail):**
```
Type: TXT
Name: @
Content: v=spf1 include:_spf.protonmail.ch mx ~all
```

**DKIM Records (Proton will provide specific values):**
```
Type: CNAME
Name: protonmail._domainkey
Target: [provided by Proton]

Type: CNAME
Name: protonmail2._domainkey
Target: [provided by Proton]

Type: CNAME
Name: protonmail3._domainkey
Target: [provided by Proton]
```

**DMARC Record (recommended):**
```
Type: TXT
Name: _dmarc
Content: v=DMARC1; p=quarantine; rua=mailto:contact@hoffmanlenses.org
```

### Step 4: Verify Domain
- Return to Proton Mail settings
- Click "Verify" — Proton will check DNS records
- May take up to 24 hours for DNS propagation

### Step 5: Create Addresses
Once domain is verified, create each address:
- Settings → Addresses → Add address
- Create all five required addresses

### Step 6: Configure Folders/Labels
Recommended organization:
- Label: FAMILY (red) — highest priority, review before responding
- Label: LEGAL (orange) — attorney communications
- Label: PRESS (blue) — journalist inquiries
- Folder: Outreach Drafts — communications awaiting Director review

---

## Security Considerations

1. **Two-factor authentication** — Enable on the Proton account immediately
2. **Recovery email** — Use a secure external email for account recovery
3. **Session management** — Regularly review active sessions
4. **No auto-forwarding** — Keep all family communications within Proton

---

## Post-Setup Checklist

- [ ] Primary Proton account created
- [ ] Custom domain added and verified
- [ ] All five addresses created
- [ ] 2FA enabled
- [ ] Test email sent/received successfully
- [ ] Labels and folders configured
- [ ] Director has login credentials stored securely

---

## Estimated Time
- Account creation: 10 minutes
- DNS configuration: 15 minutes
- DNS propagation: 1-24 hours
- Address creation: 10 minutes

**Total: Same-day completion possible**

---

*This document prepared by Advocacy Agent. Ready for Director action.*
