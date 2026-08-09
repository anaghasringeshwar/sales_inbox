import os
import json
import re
import time

from datetime import (
    datetime,
    timedelta
)

from dotenv import load_dotenv
from google import genai


# ============================================================
# 1. LOAD GEMINI
# ============================================================

load_dotenv()

api_key = (
    os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
)

if not api_key:

    raise RuntimeError(
        "GEMINI_API_KEY or GOOGLE_API_KEY "
        "is not set in .env"
    )


client = genai.Client(
    api_key=api_key
)

MODEL_NAME = "gemini-2.5-flash"


# ============================================================
# 2. PARSE GEMINI JSON
# ============================================================

def parse_json_response(text):
    """
    Convert Gemini's response into a Python dictionary.

    Handles:
    - normal JSON
    - ```json ... ```
    - accidental text around JSON
    """

    if not text:

        raise ValueError(
            "Gemini returned an empty response"
        )

    text = text.strip()

    # Remove markdown code fences.

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    try:

        return json.loads(text)

    except json.JSONDecodeError:

        # Try to extract the first JSON object.

        match = re.search(
            r"\{.*\}",
            text,
            re.DOTALL
        )

        if not match:

            raise ValueError(
                "Could not find JSON in Gemini response: "
                f"{text}"
            )

        return json.loads(
            match.group(0)
        )


# ============================================================
# 3. GEMINI CLASSIFIER
# ============================================================

def classify_with_gemini(email):

    prompt = f"""
You are an expert B2B sales inbox routing system.

You must classify ONE inbound email.

The email may contain:

- messy English
- Hinglish
- typos
- informal language
- HTML fragments
- quoted replies
- forwarded messages
- misleading keywords
- multiple business requests

DO NOT classify using keywords alone.

Understand:

1. Who is sending the email?
2. What do they actually want?
3. Who is selling to whom?
4. Whether this is a genuine business request or unsolicited spam.
5. Whether the email contains one clear business intent or multiple conflicting intents.
6. Whether this is a reply and what NEW information it contains.

TEAM:

u_aarti = Aarti Menon
Department: Sales — Enterprise

Handles:

- RFPs
- RFIs
- tenders
- inbound enterprise deals above ₹10,00,000
- government tenders
- PSU tenders


u_rohit = Rohit Sharma
Department: Sales — SMB

Handles:

- product enquiries
- demo requests
- deals at or below ₹10,00,000


u_meera = Meera Iyer
Department: Marketing

Handles:

- webinars
- event sponsorships
- conference sponsorships
- content collaborations
- PR
- media


u_karan = Karan Doshi
Department: Alliances

Handles:

- reseller proposals
- channel partnerships
- technology integration proposals
- alliance opportunities


u_divya = Divya Rao
Department: Finance

Handles:

- invoices
- purchase orders
- payment reminders
- GST
- vendor billing


u_triage = Triage Queue
Department: Operations

Handles:

- genuinely ambiguous requests
- multiple conflicting business asks
- requests that cannot confidently be assigned


DO NOT create a task for:

1. Out-of-office automatic replies.

2. Newsletters.

3. Unsolicited vendor spam.


VENDOR SPAM:

Examples:

- SEO companies offering their services
- marketing agencies selling services
- lead generation companies
- PR agencies pitching themselves
- webinar promotion companies selling services
- unsolicited software/service vendors

A vendor spam email may contain:

"marketing"
"PR"
"webinar"
"SEO"
"content"
"partnership"

Do NOT route it to Marketing or Alliances merely because
those words appear.

Determine the DIRECTION OF INTENT.

Example:

"We are organising a SaaS conference and would like to
sponsor your company."

This is genuine marketing/sponsorship.

But:

"We help SaaS companies organise webinars and would like
to sell our webinar promotion services."

This is vendor spam.


PRIORITY:

HIGH priority ONLY when:

- there is a stated deadline within 72 hours of received_at
OR
- the email clearly describes an already overdue
  action/payment/deadline.

Do NOT make an email high priority merely because it says:

- ASAP
- urgent
- quickly
- important
- immediate attention
- please respond soon

Those words alone are NOT enough.

If a stated deadline is more than 72 hours away:

Do NOT mark it high merely because it is an RFP or
important business opportunity.

Use medium unless there is another strong reason.

If there is no urgency:

Use low or medium depending on the business context.


GOVERNMENT / PSU:

Government and PSU tenders ALWAYS go to:

u_aarti

This overrides the ₹10,00,000 rule.


DEAL VALUE:

Extract deal_value_inr ONLY when an actual commercial/deal
value is explicitly stated.

Examples:

"Rs. 25 lakhs"
=> 2500000

"₹4,00,000"
=> 400000

"1.2 cr"
=> 12000000

"1.2 crore"
=> 12000000

"650000"
=> 650000

DO NOT invent a value.

DO NOT infer a value from:

- number of employees
- number of users
- company size
- estimated revenue
- vague language such as "significant budget"

IMPORTANT:

An invoice amount is NOT deal value.

A payment amount is NOT deal value.

A PO amount is NOT automatically deal value.


COMPANY NAME:

Only provide company_name when it is explicitly identifiable
from the email content.

DO NOT infer the company name from the email domain.

Example:

From:
suresh@meridiansteel.co.in

Body:
"Meridian Steel invites proposals..."

company_name:
"Meridian Steel"

If the body never identifies the company:

company_name:
null


DUE DATE:

Extract due_date only when the email contains an actual
deadline/date.

Examples:

"Submit by 12 August 2026"
=> 2026-08-12

"Deadline is 03-08-2026"
=> 2026-08-03

"Tomorrow EOD"
=> calculate actual date using received_at.

"Next week"
=> null

"Sometime next week"
=> null

"ASAP"
=> null

Do NOT invent a date.


REPLIES:

If this is a reply:

Focus primarily on NEW information in the reply.

Ignore quoted previous messages when determining new values.

Example:

Previous:
Budget = ₹25 lakhs
Deadline = August 12

Reply:
"Correction: budget is now ₹32 lakhs and deadline is
August 11."

Extract:

deal_value_inr = 3200000
due_date = 2026-08-11

Do not simply repeat quoted original information.


MULTIPLE INTENTS:

If one email contains two different business requests owned
by different departments, prefer:

u_triage

Example:

"We want to purchase your platform for our enterprise AND
our CMO wants to co-host a webinar."

This involves Enterprise Sales + Marketing.

Route to:

u_triage


CONFIDENCE:

confidence must be between 0.0 and 1.0.

High confidence:

- clear intent
- clear ownership
- enough information

Medium confidence:

- mostly clear but some uncertainty

Low confidence:

- ambiguous
- conflicting requests
- incomplete information

Do NOT give 0.95 confidence to an ambiguous email.


EXAMPLES:

Example 1:

"Meridian Steel invites proposals for an enterprise DMS.
Budget Rs. 25 lakhs.
Proposals due 12 August 2026."

=> u_aarti
=> enterprise_rfp
=> deal_value_inr = 2500000
=> due_date = 2026-08-12


Example 2:

"Can we get a demo of your product next week?
We are a 30-person startup."

=> u_rohit
=> smb_enquiry
=> deal_value_inr = null
=> due_date = null


Example 3:

"BHEL tender.
Estimated value Rs. 6,50,000.
Last date 03-08-2026."

=> u_aarti

Government/PSU tender overrides value rule.


Example 4:

"We are finalising sponsors for India SaaS Summit.
Gold tier ₹4,00,000.
Please confirm by tomorrow EOD."

=> u_meera
=> marketing
=> high if deadline is within 72 hours.


Example 5:

"Invoice INV-123 for Rs. 1,18,000.
Payment is overdue."

=> u_divya
=> finance
=> deal_value_inr = null


Example 6:

"We would like to resell your platform in MEA."

=> u_karan
=> alliances


Example 7:

"I am out of office until August 14."

=> skip


Example 8:

"We noticed your website isn't ranking on Google.
We offer SEO, PR and webinar promotion services."

=> skip
=> vendor spam


Example 9:

"The B2B Growth Weekly - Issue #212.
Unsubscribe."

=> skip
=> newsletter


Example 10:

"Correction: budget increased from Rs. 25 lakhs to Rs. 32
lakhs. Deadline advanced to August 11."

=> update-compatible classification
=> deal_value_inr = 3200000
=> due_date = 2026-08-11


Example 11:

"We want to evaluate your platform for our 800-person company,
and our CMO also wants to co-host a webinar."

=> u_triage
=> triage
=> low confidence


Example 12:

"Bhai humko product chahiye for 150 users.
Budget approx 1.2 cr allocated hai.
Board review 20th ko hai."

=> u_aarti
=> enterprise_rfp
=> deal_value_inr = 12000000
=> due_date = 2026-08-20
=> company_name = null if company is not stated.


EMAIL:

From name:
{email.from_name}

From email:
{email.from_email}

Subject:
{email.subject}

Received at:
{email.received_at}

Is reply:
{getattr(email, "is_reply", False)}

Body:
{email.body}


Return ONLY valid JSON.

Do not write explanations outside JSON.

Return exactly these fields:

{{
    "decision": "create" or "skip",

    "category":
        "enterprise_rfp"
        or "smb_enquiry"
        or "marketing"
        or "alliances"
        or "finance"
        or "triage",

    "assignee_id":
        "u_aarti"
        or "u_rohit"
        or "u_meera"
        or "u_karan"
        or "u_divya"
        or "u_triage"
        or null,

    "priority":
        "high"
        or "medium"
        or "low"
        or null,

    "due_date": "YYYY-MM-DD" or null,

    "deal_value_inr": integer or null,

    "company_name": string or null,

    "confidence": number,

    "reason": string,

    "is_vendor_spam": boolean,

    "is_newsletter": boolean,

    "is_auto_reply": boolean
}}
"""

    # ========================================================
    # GEMINI CALL WITH RETRIES
    # ========================================================

    last_error = None

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            result = parse_json_response(
                response.text
            )

            return result

        except Exception as e:

            last_error = e

            if attempt < 2:

                time.sleep(
                    2 * (attempt + 1)
                )

            else:

                raise last_error


# ============================================================
# 4. HARD BUSINESS RULES / VALIDATION
# ============================================================

def apply_business_rules(result, email):
    """
    Gemini performs semantic classification.

    Python enforces deterministic business rules.
    """

    if not isinstance(result, dict):

        raise ValueError(
            "Gemini result is not a dictionary"
        )

    subject = (
        getattr(email, "subject", "")
        or ""
    )

    body = (
        getattr(email, "body", "")
        or ""
    )

    text = (
        f"{subject} {body}"
    ).lower()

    # ========================================================
    # VALID ENUMS
    # ========================================================

    valid_categories = {
        "enterprise_rfp",
        "smb_enquiry",
        "marketing",
        "alliances",
        "finance",
        "triage"
    }

    valid_assignees = {
        "u_aarti",
        "u_rohit",
        "u_meera",
        "u_karan",
        "u_divya",
        "u_triage"
    }

    valid_priorities = {
        "high",
        "medium",
        "low"
    }

    if result.get("category") not in valid_categories:

        result["category"] = "triage"

    if result.get("assignee_id") not in valid_assignees:

        result["assignee_id"] = "u_triage"

    if result.get("priority") not in valid_priorities:

        result["priority"] = "medium"

    # ========================================================
    # SKIP: OUT OF OFFICE
    # ========================================================

    if (
        result.get("is_auto_reply") is True
        or "out of office" in text
        or "automatic reply" in text
        or "auto-reply" in text
        or "autoreply" in text
    ):

        result["decision"] = "skip"

        result["reason"] = (
            "Out-of-office / automatic reply"
        )

        return result

    # ========================================================
    # SKIP: NEWSLETTER
    # ========================================================

    if (
        result.get("is_newsletter") is True
        or "unsubscribe" in text
    ):

        result["decision"] = "skip"

        result["reason"] = "Newsletter"

        return result

    # ========================================================
    # SKIP: VENDOR SPAM
    # ========================================================

    if result.get("is_vendor_spam") is True:

        result["decision"] = "skip"

        result["reason"] = (
            "Unsolicited vendor spam"
        )

        return result

    # ========================================================
    # GOVERNMENT / PSU TENDER
    # ========================================================

    government_words = [
        "government",
        "govt",
        "public sector",
        "psu",
        "bhel",
        "bharat heavy electricals",
        "ongc",
        "ntpc",
        "indian railways",
        "railways",
        "lic of india",
        "life insurance corporation"
    ]

    tender_words = [
        "tender",
        "tender notice",
        "bid submission",
        "invites bids",
        "invitation for bids",
        "procurement tender"
    ]

    is_government = any(
        word in text
        for word in government_words
    )

    is_tender = any(
        word in text
        for word in tender_words
    )

    if is_government and is_tender:

        result["decision"] = "create"

        result["assignee_id"] = "u_aarti"

        result["category"] = "enterprise_rfp"

    # ========================================================
    # DEADLINE / PRIORITY
    # ========================================================

    due_date = result.get("due_date")

    if due_date:

        try:

            received_at = (
                email.received_at
                .replace("Z", "+00:00")
            )

            received = datetime.fromisoformat(
                received_at
            )

            deadline_date = datetime.strptime(
                due_date,
                "%Y-%m-%d"
            ).date()

            # Treat date-only deadlines as EOD.

            deadline = datetime.combine(
                deadline_date,
                datetime.max.time()
            )

            deadline = deadline.replace(
                tzinfo=received.tzinfo
            )

            difference = (
                deadline - received
            )

            # Overdue OR within 72 hours.

            if difference <= timedelta(hours=72):

                result["priority"] = "high"

            else:

                # Prevent Gemini from overriding
                # the deterministic rule.

                if result.get("priority") == "high":

                    result["priority"] = "medium"

        except Exception:

            result["due_date"] = None

            if result.get("priority") == "high":

                result["priority"] = "medium"

    # ========================================================
    # DEAL VALUE VALIDATION
    # ========================================================

    value = result.get(
        "deal_value_inr"
    )

    if value is not None:

        try:

            value = int(value)

            if value < 0:

                value = None

            result["deal_value_inr"] = value

        except (
            ValueError,
            TypeError
        ):

            result["deal_value_inr"] = None

    # ========================================================
    # COMPANY NAME
    # ========================================================

    company = result.get(
        "company_name"
    )

    if company is not None:

        if not isinstance(
            company,
            str
        ):

            result["company_name"] = None

        else:

            company = company.strip()

            if not company:

                result["company_name"] = None

            else:

                result["company_name"] = company

    # ========================================================
    # CONFIDENCE
    # ========================================================

    try:

        confidence = float(
            result.get(
                "confidence",
                0.5
            )
        )

        confidence = max(
            0.0,
            min(
                1.0,
                confidence
            )
        )

        result["confidence"] = confidence

    except (
        ValueError,
        TypeError
    ):

        result["confidence"] = 0.5

    # ========================================================
    # LOW CONFIDENCE -> TRIAGE
    # ========================================================

    if result["confidence"] < 0.55:

        result["assignee_id"] = "u_triage"

        result["category"] = "triage"

        if result.get("decision") != "skip":

            result["decision"] = "create"

    # ========================================================
    # FINAL DECISION SAFETY
    # ========================================================

    if result.get("decision") not in {
        "create",
        "skip"
    }:

        result["decision"] = "create"

    return result


# ============================================================
# 5. MAIN CLASSIFIER
# ============================================================

def classify_email(email):
    """
    Main classifier used by ingest.py.

    Flow:

        Email
          ↓
        Gemini
          ↓
        Python validation
          ↓
        Business rules
          ↓
        Final classification
    """

    try:

        # ====================================================
        # GEMINI
        # ====================================================

        result = classify_with_gemini(
            email
        )

        # ====================================================
        # PYTHON RULES
        # ====================================================

        result = apply_business_rules(
            result,
            email
        )

        # ====================================================
        # TASK FIELDS
        # ====================================================

        result["title"] = (
            email.subject
        )

        result["description"] = (
            email.body
        )

        return result

    except Exception as e:

        # ====================================================
        # GEMINI FAILURE
        # ====================================================

        # Never lose the email.
        #
        # Instead create a low-confidence
        # triage task for human review.

        return {

            "decision": "create",

            "title": email.subject,

            "description": email.body,

            "assignee_id": "u_triage",

            "category": "triage",

            "priority": "medium",

            "due_date": None,

            "deal_value_inr": None,

            "company_name": None,

            "confidence": 0.20,

            "reason": (
                "Gemini classification failed: "
                f"{str(e)}"
            ),

            "is_vendor_spam": False,

            "is_newsletter": False,

            "is_auto_reply": False
        }


# ============================================================
# 6. NORMALIZE RESULT FOR INGEST
# ============================================================

def prepare_task_result(result, email):
    """
    Convert classifier output into fields needed
    by the Task API.
    """

    return {

        "title": email.subject,

        "description": email.body,

        "assignee_id": result.get(
            "assignee_id"
        ),

        "category": result.get(
            "category"
        ),

        "priority": result.get(
            "priority"
        ),

        "due_date": result.get(
            "due_date"
        ),

        "deal_value_inr": result.get(
            "deal_value_inr"
        ),

        "company_name": result.get(
            "company_name"
        ),

        "confidence": result.get(
            "confidence"
        ),

        "reason": result.get(
            "reason"
        )
    }