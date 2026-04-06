EMAILS = [
    {
        "email_id": 1,
        "subject": "Congratulations! You have been selected for a $5,000 cash reward",
        "body": (
            "Dear Winner,\n\n"
            "You have been randomly selected from millions of participants to receive "
            "a $5,000 cash prize. To claim your reward, click the link below and enter "
            "your bank details within 24 hours or your prize will be forfeited.\n\n"
            "Claim now: http://totally-not-a-scam.ru/claim\n\n"
            "Regards,\nPrize Team"
        ),
        "sender": "noreply@promo-winners99.biz",
    },
    {
        "email_id": 2,
        "subject": "Q3 Budget Review — Approval Required Before Friday",
        "body": (
            "Hi team,\n\n"
            "Please review the attached Q3 financial report and confirm your department "
            "budget allocations before Friday's board meeting at 2 PM.\n\n"
            "This is time-sensitive. The CFO needs sign-off from all department heads "
            "before we can proceed with the audit.\n\n"
            "Thanks,\nSarah Chen\nChief Financial Officer"
        ),
        "sender": "sarah.chen@yourcompany.com",
    },
    {
        "email_id": 3,
        "subject": "This Week in Growth Hacking — Issue #47",
        "body": (
            "Hi there,\n\n"
            "Welcome to this week's edition of the Growth Hacking Weekly newsletter!\n\n"
            "TOP STORIES THIS WEEK:\n"
            "- How Company X grew to 1M users in 6 months\n"
            "- 5 SEO tricks your competitors don't know\n"
            "- Why your funnel is leaking (and how to fix it)\n\n"
            "Unsubscribe | View in browser | Privacy Policy\n"
            "Growth Hacking Weekly, 123 Marketing St, San Francisco CA"
        ),
        "sender": "editor@growthhacking-weekly.io",
    },
]

GROUND_TRUTH = [
    {
        "email_id":   1,
        "action_type": "ignore",
        "priority":   "low",
        "classification": "ignore",
        "trap_type":  "obvious_spam",
        "difficulty": 0.1,
    },
    {
        "email_id":   2,
        "action_type": "reply",
        "priority":   "high",
        "classification": "reply",
        "trap_type":  "legitimate_internal",
        "difficulty": 0.1,
    },
    {
        "email_id":   3,
        "action_type": "ignore",
        "priority":   "low",
        "classification": "ignore",
        "trap_type":  "obvious_newsletter",
        "difficulty": 0.1,
    },
]