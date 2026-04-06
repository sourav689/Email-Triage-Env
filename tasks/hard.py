EMAILS = [
    {
        "email_id": 1,
        "subject": "URGENT: Production Server Down — Immediate Action Required",
        "body": (
            "Hi team!\n\n"
            "Hope you had a great weekend. Here's your Monday morning digest:\n\n"
            "- Engineering blog post of the week: 'How we scaled to 10M requests'\n"
            "- Upcoming webinar: 'DevOps best practices 2024'\n"
            "- New course available: Docker for beginners\n"
            "- Community spotlight: Meet our top contributors this month\n\n"
            "Forward to a friend | Unsubscribe | Manage preferences\n"
            "DevOps Weekly, 456 Tech Ave, Austin TX"
        ),
        "sender": "newsletter@devops-weekly.io",
    },
    {
        "email_id": 2,
        "subject": "Wire Transfer Approval Needed — Time Sensitive",
        "body": (
            "Hi,\n\n"
            "I'm traveling and can't access the internal system. I need you to approve "
            "an urgent wire transfer of $47,500 to our new vendor before EOD today. "
            "This is confidential — please don't discuss with other team members until "
            "the transfer is complete.\n\n"
            "Reply directly to this email with your approval and I'll handle the rest.\n\n"
            "Thanks,\nJames Whitfield\nCEO"
        ),
        "sender": "james.whitfield@yourcompany-support.net",
    },
    {
        "email_id": 3,
        "subject": "CRITICAL: Your immediate response required — contract expiry",
        "body": (
            "Dear Team,\n\n"
            "I wanted to flag that our enterprise software license with us expires "
            "in 30 days. To avoid any disruption, I'd love to schedule a quick call "
            "to walk you through our new pricing tiers — we have some great options "
            "that could actually save you money!\n\n"
            "Would you have 15 minutes this week?\n\n"
            "Best,\nTyler from VendorCo Sales"
        ),
        "sender": "tyler.morrison@vendorco-sales.com",
    },
    {
        "email_id": 4,
        "subject": "CRITICAL: Infrastructure failure — all services offline",
        "body": (
            "Hi,\n\n"
            "I'm reaching out because our entire engineering leadership team is "
            "currently dealing with an outage across all production services. "
            "Payments, auth, and the API gateway are all down. We have 50,000 "
            "users affected and the board is already asking for updates.\n\n"
            "I need your on-call engineer paged immediately and a war room set up "
            "in the next 10 minutes. Every second counts.\n\n"
            "— Priya Nair\nVP Engineering, yourcompany.com"
        ),
        "sender": "priya.nair@yourcompany.com",
    },
    {
        "email_id": 5,
        "subject": "Re: Re: Re: Team Lunch Next Friday",
        "body": (
            "Hey,\n\n"
            "Sounds great, I'll book Rosario's for 12:30.\n\n"
            "--- Original message from Lisa ---\n"
            "Pizza or Italian? I vote Italian!\n\n"
            "--- Original message from Tom ---\n"
            "Any food preferences for the team lunch?\n\n"
            "--- Original message from Lisa ---\n"
            "Hey Tom — before I forget, completely separate from lunch: "
            "can you review and sign off on the Q4 roadmap doc I shared yesterday? "
            "The product team needs your approval by Thursday morning or the "
            "sprint planning meeting can't proceed. This is blocking three engineers.\n\n"
            "Thanks!"
        ),
        "sender": "lisa.fernandez@yourcompany.com",
    },
    {
        "email_id": 6,
        "subject": "Hey! It's been forever — catch up?",
        "body": (
            "Hi there!\n\n"
            "Oh wow, it's been so long! I was just thinking about you the other day "
            "and wanted to reach out. Hope life is treating you well!\n\n"
            "I've been working on something really exciting lately and I thought of you "
            "right away — I think you'd genuinely love it. Just click this link to see "
            "what I've been up to: http://bit.ly/3xK9qZ2\n\n"
            "Miss you!\nAlex"
        ),
        "sender": "alex.k2024@freemailer-promo.xyz",
    },
    {
        "email_id": 7,
        "subject": "Billing issue on your account — please review",
        "body": (
            "Hi,\n\n"
            "I wanted to flag a billing discrepancy on invoice #INV-2024-1147 "
            "sent last month. We were charged for 15 Enterprise seats but our "
            "contract shows 12. The overcharge is $840.\n\n"
            "Could you look into this and issue a corrected invoice or credit note?\n\n"
            "Happy to jump on a call if easier.\n\n"
            "Best,\nRachel Wong\nAccounts Payable, Acme Corp"
        ),
        "sender": "rachel.wong@acmecorp.com",
    },
    {
        "email_id": 8,
        "subject": "Re: Billing issue on your account — please review",
        "body": (
            "Hi,\n\n"
            "Following up on my email from last Thursday regarding invoice #INV-2024-1147. "
            "We still haven't received a response or credit note.\n\n"
            "Our accounts payable deadline is this Friday. If we don't resolve this "
            "before then, our finance team will be disputing the full invoice amount "
            "with our bank.\n\n"
            "Please confirm receipt and let me know the timeline for resolution.\n\n"
            "Thanks,\nRachel Wong\nAccounts Payable, Acme Corp"
        ),
        "sender": "rachel.wong@acmecorp.com",
    },
    {
        "email_id": 9,
        "subject": "[CRITICAL] CPU spike detected on prod-db-1 — Auto-resolved",
        "body": (
            "[AUTOMATED MONITORING ALERT — PagerDuty]\n\n"
            "Incident: INC-20240115-0047\n"
            "Service: prod-db-1\n"
            "Metric: CPU Usage\n"
            "Peak value: 94% at 03:17 UTC\n"
            "Status: AUTO-RESOLVED at 03:19 UTC\n"
            "Duration: 2 minutes\n\n"
            "Root cause identified: Scheduled nightly vacuum job. "
            "No data loss. No user impact. Incident closed automatically.\n\n"
            "No action required. This alert is for logging purposes only."
        ),
        "sender": "alerts@pagerduty.com",
    },
    {
        "email_id": 10,
        "subject": "Happy Holidays from the CEO",
        "body": (
            "Hi everyone,\n\n"
            "As we wrap up another incredible year, I want to take a moment to "
            "thank each and every one of you for your hard work, dedication, and "
            "creativity. This team continues to amaze me every single day.\n\n"
            "Wishing you and your families a wonderful holiday season and a "
            "happy, healthy new year. The office will be closed December 24–26.\n\n"
            "See you in the new year!\n\nJames Whitfield\nCEO, YourCompany"
        ),
        "sender": "james.whitfield@yourcompany.com",
    },
]

GROUND_TRUTH = [
    {
        "email_id":   1,
        "action_type": "ignore",
        "priority":   "low",
        "classification": "ignore",
        "trap_type":  "misleading_subject",
        "difficulty": 0.9,
    },
    {
        "email_id":   2,
        "action_type": "escalate",
        "priority":   "high",
        "classification": "escalate",
        "trap_type":  "executive_phishing",
        "difficulty": 0.95,
    },
    {
        "email_id":   3,
        "action_type": "ignore",
        "priority":   "low",
        "classification": "ignore",
        "trap_type":  "fake_urgency",
        "difficulty": 0.8,
    },
    {
        "email_id":   4,
        "action_type": "escalate",
        "priority":   "high",
        "classification": "escalate",
        "trap_type":  "real_urgency",
        "difficulty": 0.7,
    },
    {
        "email_id":   5,
        "action_type": "reply",
        "priority":   "high",
        "classification": "reply",
        "trap_type":  "buried_request",
        "difficulty": 0.95,
    },
    {
        "email_id":   6,
        "action_type": "ignore",
        "priority":   "low",
        "classification": "ignore",
        "trap_type":  "friendly_spam",
        "difficulty": 0.85,
    },
    {
        "email_id":   7,
        "action_type": "ignore",
        "priority":   "low",
        "classification": "ignore",
        "trap_type":  "duplicate_original",
        "difficulty": 0.8,
    },
    {
        "email_id":   8,
        "action_type": "reply",
        "priority":   "high",
        "classification": "reply",
        "trap_type":  "duplicate_followup",
        "difficulty": 0.75,
    },
    {
        "email_id":   9,
        "action_type": "ignore",
        "priority":   "low",
        "classification": "ignore",
        "trap_type":  "false_alarm",
        "difficulty": 0.9,
    },
    {
        "email_id":   10,
        "action_type": "classify",
        "priority":   "low",
        "classification": "classify",
        "trap_type":  "low_priority_executive",
        "difficulty": 0.7,
    },
]