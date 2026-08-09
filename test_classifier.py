from backend.classifier import classify_email


class Email:
    def __init__(
        self,
        from_name,
        from_email,
        subject,
        body,
        received_at,
        is_reply=False
    ):
        self.from_name = from_name
        self.from_email = from_email
        self.subject = subject
        self.body = body
        self.received_at = received_at
        self.is_reply = is_reply


def run_test(name, email):

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    result = classify_email(email)

    print(f"decision:       {result.get('decision')}")
    print(f"category:       {result.get('category')}")
    print(f"assignee:       {result.get('assignee_id')}")
    print(f"priority:       {result.get('priority')}")
    print(f"due_date:       {result.get('due_date')}")
    print(f"deal_value:     {result.get('deal_value_inr')}")
    print(f"company:        {result.get('company_name')}")
    print(f"confidence:     {result.get('confidence')}")
    print(f"reason:         {result.get('reason')}")
    print(f"vendor_spam:    {result.get('is_vendor_spam')}")
    print(f"newsletter:     {result.get('is_newsletter')}")
    print(f"auto_reply:     {result.get('is_auto_reply')}")


# ============================================================
# TEST 1 — FAKE URGENCY
# ============================================================

email1 = Email(
    "Rahul",
    "rahul@startup.com",
    "URGENT!!! Immediate Action Required!!!",
    """
    Hi Team,

    This is extremely urgent and important.
    We need to discuss your product ASAP.

    Please get back to us immediately.

    Thanks,
    Rahul
    """,
    "2026-08-09T09:00:00+05:30"
)

run_test("TEST 1 — Fake urgency / ASAP", email1)


# ============================================================
# TEST 2 — VENDOR SPAM DISGUISED AS PARTNERSHIP
# ============================================================

email2 = Email(
    "Amit",
    "amit@digitalgrowthagency.com",
    "Partnership Opportunity",
    """
    Hi,

    We are a digital marketing agency helping SaaS companies
    generate leads.

    We would love to partner with your company and provide
    SEO, PR, webinar promotion and lead generation services.

    Let us know if you would like a quick call.

    Regards,
    Amit
    """,
    "2026-08-09T09:00:00+05:30"
)

run_test("TEST 2 — Vendor spam pretending to be partnership", email2)


# ============================================================
# TEST 3 — GENUINE MARKETING / EVENT SPONSORSHIP
# ============================================================

email3 = Email(
    "Priya",
    "priya@saasconf.com",
    "SaaS Summit 2026 — Sponsorship Opportunity",
    """
    Hi Team,

    We are organising the India SaaS Summit 2026.

    We would like your company to become a Gold Sponsor.
    The sponsorship fee is ₹4,00,000.

    Please confirm your participation by August 11, 2026.

    Regards,
    Priya
    """,
    "2026-08-09T09:00:00+05:30"
)

run_test("TEST 3 — Genuine event sponsorship", email3)


# ============================================================
# TEST 4 — FINANCE EMAIL WITH LARGE AMOUNT
# ============================================================

email4 = Email(
    "Finance Team",
    "accounts@vendor.com",
    "Invoice INV-8841 — Payment Due",
    """
    Dear Team,

    Please find attached invoice INV-8841
    for ₹25,00,000.

    Payment is due by August 10, 2026.

    Regards,
    Accounts Team
    """,
    "2026-08-09T09:00:00+05:30"
)

run_test("TEST 4 — Invoice with large amount", email4)


# ============================================================
# TEST 5 — CONFLICTING BUSINESS REQUESTS
# ============================================================

email5 = Email(
    "Neha",
    "neha@bigcompany.com",
    "Enterprise Purchase + Webinar Partnership",
    """
    Hi Team,

    We are evaluating your platform for our 1,000 employees.
    Our expected budget is ₹30 lakhs.

    At the same time, our marketing team would like to
    co-host a webinar with your company next month.

    Please let us know how we can proceed with both.

    Regards,
    Neha
    """,
    "2026-08-09T09:00:00+05:30"
)

run_test("TEST 5 — Conflicting Sales + Marketing requests", email5)