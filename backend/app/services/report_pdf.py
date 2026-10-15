from datetime import datetime, timezone
from io import BytesIO
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.analysis import AnalysisData, StoredAnalysisRecord


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    safe = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )
    return Paragraph(safe, style)


def generate_analysis_pdf(record: StoredAnalysisRecord) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="ResumeFit AI Analysis Report",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        textColor=colors.HexColor("#4338CA"),
        spaceAfter=8,
    )
    h2 = styles["Heading2"]
    body = styles["BodyText"]
    small = ParagraphStyle("Small", parent=body, fontSize=9, textColor=colors.grey)

    data: AnalysisData = record.data
    created = record.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story: List = []

    story.append(_p("ResumeFit AI — Analysis Report", title_style))
    story.append(_p(f"Generated: {created}", small))
    story.append(_p(f"Role: {record.job_title}", body))
    if record.company_name:
        story.append(_p(f"Company: {record.company_name}", body))
    story.append(Spacer(1, 0.15 * inch))

    scoring = data.analysis.scoring
    score_table = Table(
        [
            ["Overall alignment", f"{scoring.overall_alignment:.1f}%"],
            ["Required skill coverage", f"{scoring.required_skill_coverage:.1f}%"],
            ["Preferred skill coverage", f"{scoring.preferred_skill_coverage:.1f}%"],
        ],
        colWidths=[2.8 * inch, 1.5 * inch],
    )
    score_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2FF")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
            ],
        ),
    )
    story.append(score_table)
    story.append(Spacer(1, 0.1 * inch))
    story.append(_p(scoring.disclaimer, small))
    story.append(Spacer(1, 0.2 * inch))

    story.append(_p("Requirement findings", h2))
    for finding in data.analysis.findings[:40]:
        status_label = finding.status.value.replace("_", " ")
        story.append(
            _p(
                f"<b>{finding.label}</b> — {status_label} ({finding.importance.value})",
                body,
            ),
        )
        if finding.notes:
            story.append(_p(finding.notes, small))
        for evidence in finding.evidence[:2]:
            story.append(_p(f"Evidence: “{evidence}”", small))
        story.append(Spacer(1, 0.05 * inch))

    story.append(Spacer(1, 0.15 * inch))
    story.append(_p("Profile alignment highlights", h2))
    profile = data.analysis.resume_profile
    if profile.responsibilities:
        story.append(_p("<b>Experience / responsibilities</b>", body))
        for item in profile.responsibilities[:6]:
            story.append(_p(f"• {item}", small))
    if profile.achievements:
        story.append(_p("<b>Achievements</b>", body))
        for item in profile.achievements[:5]:
            story.append(_p(f"• {item}", small))
    if profile.education:
        story.append(_p("<b>Education</b>", body))
        for item in profile.education[:4]:
            story.append(_p(f"• {item}", small))

    rec = data.recommendations
    if rec.enabled or rec.provider != "disabled":
        story.append(Spacer(1, 0.15 * inch))
        story.append(_p("Recommendations", h2))
        story.append(_p(f"Provider: {rec.provider}", small))
        for gap in rec.gap_explanations[:8]:
            story.append(_p(f"• {gap}", body))
        for topic in rec.learning_topics[:8]:
            story.append(_p(f"Learning topic: {topic}", small))
        for bullet in rec.resume_bullet_suggestions[:6]:
            story.append(_p(bullet, small))

    story.append(Spacer(1, 0.2 * inch))
    story.append(
        _p(
            "This report excludes raw resume files and API secrets. "
            "Evidence snippets are limited to text already used in analysis.",
            small,
        ),
    )

    doc.build(story)
    return buffer.getvalue()


def generate_pdf_from_analysis_data(
    data: AnalysisData,
    *,
    created_at: Optional[datetime] = None,
    resume_filename: Optional[str] = None,
) -> bytes:
    record = StoredAnalysisRecord(
        id="export",
        created_at=created_at or datetime.now(timezone.utc),
        job_title=data.job_title,
        company_name=data.company_name,
        resume_filename=resume_filename,
        data=data,
    )
    return generate_analysis_pdf(record)
