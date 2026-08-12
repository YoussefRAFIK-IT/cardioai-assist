import json
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_prediction_pdf(prediction, notice: str) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=9, leading=12))
    details = json.loads(prediction.details_json or "{}")
    quality = details.get("quality", {})

    story = [Paragraph("CardioAI Assist — Rapport d'analyse ECG", styles["Title"]), Spacer(1, 0.5*cm)]
    data = [
        ["Référence", prediction.ecg_record.public_ref],
        ["Fichier", prediction.ecg_record.original_filename],
        ["Mode", prediction.inference_mode],
        ["Version", prediction.model_version],
        ["Empreinte bundle", details.get("bundle_fingerprint") or "-"],
        ["Probabilité MI", f"{prediction.probability:.4f}"],
        ["Seuil de recherche verrouillé", f"{prediction.threshold:.2f}"],
        ["Classe expérimentale", "MI" if prediction.predicted_class else "NORM"],
        ["Latence", f"{prediction.latency_ms:.1f} ms"],
        ["Segments", str(prediction.ecg_record.segment_count)],
    ]
    table = Table(data, colWidths=[5.5*cm, 9.5*cm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8F1F8")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([table, Spacer(1, 0.4*cm)])

    if quality:
        qrows = [
            ["Valeurs manquantes", f"{100*quality.get('missing_fraction', 0):.2f} %"],
            ["Amplitude max. absolue", f"{quality.get('max_abs_amplitude', 0):.4f}"],
            ["Points après conversion", str(quality.get('points_after_resampling', '-'))],
            ["Dérivations plates", ", ".join(quality.get('flat_leads', [])) or "Aucune détectée"],
        ]
        qt = Table(qrows, colWidths=[6*cm, 8*cm])
        qt.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey), ("PADDING", (0, 0), (-1, -1), 5)]))
        story.extend([Paragraph("Contrôles techniques du signal", styles["Heading2"]), qt, Spacer(1, 0.4*cm)])

    if prediction.explanation:
        leads = json.loads(prediction.explanation.lead_importance_json or "[]")[:5]
        rows = [["Dérivation", "Importance absolue"]] + [[r["lead"], f"{r['abs_importance']:.5f}"] for r in leads]
        xt = Table(rows, colWidths=[7*cm, 6*cm])
        xt.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAD3")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.extend([Paragraph("Sensibilité par dérivation", styles["Heading2"]), xt, Spacer(1, 0.4*cm)])

    story.extend([
        Paragraph("Limite du seuil", styles["Heading2"]),
        Paragraph(
            "Le seuil 0,72 est issu du développement interne PTB-XL. Sur l'évaluation externe PTBDB du pipeline exact de l'application, "
            "la ROC-AUC patient était d'environ 0,946 mais la sensibilité à ce seuil d'environ 0,541. Cette classe ne doit pas être interprétée comme un diagnostic.",
            styles["Small"],
        ),
        Paragraph("Avertissement", styles["Heading2"]),
        Paragraph(notice, styles["Small"]),
        Paragraph("Aucune donnée d'identité patient n'est nécessaire. Le fichier brut n'est pas conservé par l'application.", styles["Small"]),
    ])
    doc.build(story)
    return buffer.getvalue()
