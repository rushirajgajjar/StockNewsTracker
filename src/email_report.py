"""HTML email composition and SES delivery."""

import logging
from datetime import datetime

import boto3
import jinja2
from botocore.exceptions import ClientError

from .analyzer import TickerAnalysis
from .edgar import Filing
from .pricing import PriceData

logger = logging.getLogger(__name__)


def compose_report(
    analyses: dict[str, TickerAnalysis],
    prices: dict[str, PriceData],
    filings: dict[str, list[Filing]],
    template_path: str = "templates/email.html",
) -> str:
    """Compose HTML email report from analysis results."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader("."),
        autoescape=jinja2.select_autoescape(["html"]),
    )
    template = env.get_template(template_path)

    html = template.render(
        report_date=datetime.now().strftime("%Y-%m-%d"),
        analyses=analyses,
        prices=prices,
        filings=filings,
    )
    return html


def send_email(
    html_body: str,
    to_address: str,
    from_address: str,
    subject: str | None = None,
) -> bool:
    """Send HTML email via AWS SES."""
    if subject is None:
        subject = f"Stock Briefing - {datetime.now().strftime('%Y-%m-%d')}"

    ses = boto3.client("ses")

    try:
        ses.send_email(
            Source=from_address,
            Destination={"ToAddresses": [to_address]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Html": {"Data": html_body, "Charset": "UTF-8"}},
            },
        )
        logger.info(f"Email sent to {to_address}")
        return True
    except ClientError as e:
        error_msg = e.response["Error"]["Message"]
        logger.error(f"SES send failed: {error_msg}")
        raise
