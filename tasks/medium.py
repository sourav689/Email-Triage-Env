EMAILS = [
    {
        "email_id": 1,
        "subject": "Team sync — need to reschedule Monday's meeting",
        "body": (
            "Hi,\n\n"
            "Something has come up and I need to move our Monday 10 AM sync. "
            "Are you free Monday at 2 PM or Tuesday morning instead?\n\n"
            "Please let me know ASAP so I can update the calendar invite.\n\n"
            "Thanks,\nMarcus"
        ),
        "sender": "marcus.okafor@yourcompany.com",
    },
    {
        "email_id": 2,
        "subject": "Flash Sale — 48 Hours Only — Up to 70% off SaaS tools",
        "body": (
            "Don't miss our biggest sale of the year!\n\n"
            "For the next 48 hours only, get up to 70% off on our suite of "
            "productivity tools. Over 200 businesses trust us to streamline their workflow.\n\n"
            "Use code FLASH70 at checkout.\n\n"
            "Shop now | Unsubscribe | Manage preferences"
        ),
        "sender": "deals@saas-flash-offers.com",
    },
    {
        "email_id": 3,
        "subject": "PRODUCTION DOWN — customers cannot log in",
        "body": (
            "Hello,\n\n"
            "We are experiencing a critical production outage. Our customers have been "
            "unable to log into the platform for the past 45 minutes. This is affecting "
            "over 3,000 active users and we are losing approximately $2,000 per minute.\n\n"
            "We have tried restarting the auth service with no success. We need your "
            "engineering team involved immediately.\n\n"
            "Please escalate this to your on-call engineer right now.\n\n"
            "— David Park\nCTO, BigCorp Solutions"
        ),
        "sender": "david.park@bigcorp-solutions.com",
    },
    {
        "email_id": 4,
        "subject": "[PagerDuty] Alert: CPU usage at 78% on prod-server-2",
        "body": (
            "[AUTOMATED ALERT — DO NOT REPLY]\n\n"
            "Service: prod-server-2\n"
            "Metric: CPU Usage\n"
            "Current value: 78%\n"
            "Threshold: 75%\n"
            "Status: WARNING\n"
            "Triggered at: 2024-01-15 09:42:31 UTC\n\n"
            "This is a warning-level alert. No immediate action required. "
            "Monitor for escalation above 90%.\n\n"
            "View dashboard | Acknowledge | Silence for 1 hour"
        ),
        "sender": "alerts@pagerduty.com",
    },
    {
        "email_id": 5,
        "subject": "Office Closure — Monday 26th December",
        "body": (
            "Hi everyone,\n\n"
            "Just a reminder that the office will be closed on Monday 26th December "
            "in observance of the Boxing Day holiday.\n\n"
            "Normal operations resume Tuesday 27th December.\n\n"
            "Happy holidays!\n\n"
            "HR Team"
        ),
        "sender": "hr@yourcompany.com",
    },
]

GROUND_TRUTH = [
    {"email_id": 1, "action_type": "reply",    "priority": "high",   "classification": "reply"},
    {"email_id": 2, "action_type": "ignore",   "priority": "low",    "classification": "ignore"},
    {"email_id": 3, "action_type": "escalate", "priority": "high",   "classification": "escalate"},
    {"email_id": 4, "action_type": "classify", "priority": "medium", "classification": "classify"},
    {"email_id": 5, "action_type": "ignore",   "priority": "low",    "classification": "ignore"},
]