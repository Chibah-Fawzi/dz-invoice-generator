import json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet

TEMPLATE_PATH = "template.json"
OUTPUT_PDF = "devis.pdf"

# Mise en page (origine en bas à gauche, y en mm depuis le bas)
MARGIN_X = 20 * mm
MARGIN_RIGHT = 20 * mm
PAGE_W, PAGE_H = A4
CONTENT_RIGHT = PAGE_W - MARGIN_RIGHT

# Espacements verticaux
GAP_AFTER_HEADER = 10 * mm
GAP_AFTER_CLIENT_TITLE = 5 * mm
LINE_SPACING_BODY = 5.5 * mm
GAP_BEFORE_TABLE = 12 * mm
TEXT_DESCENT = 3 * mm  # espace sous la dernière ligne avant le tableau
GAP_AFTER_TABLE = 10 * mm
LINE_SPACING_TOTALS = 7 * mm
FOOTER_Y = 14 * mm

styles = getSampleStyleSheet()
style_normal = styles["Normal"]
style_normal.fontName = "Helvetica"
style_normal.fontSize = 9
style_normal.leading = 11


def charger_donnees(path=TEMPLATE_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_montant(val):
    return f"{val:,.2f} DZD".replace(",", " ").replace(".", ",")


def calculer_totaux(data):
    lignes = data["lignes"]
    devis = data["devis"]

    total_ht = 0
    for l in lignes:
        l_total = l["quantite"] * l["prix_unitaire_ht"]
        l["total_ht"] = l_total
        total_ht += l_total

    if devis.get("tva_applicable", True):
        tva_applicable = devis.get("tva_applicable", True) and not devis.get("non_assujetti_tva", False)
        taux_tva = devis.get("taux_tva", 19) if tva_applicable else 0
        montant_tva = total_ht * taux_tva / 100
        total_ttc = total_ht + montant_tva
    else:
        montant_tva = 0
        total_ttc = total_ht
        taux_tva = 0

    return {
        "total_ht": total_ht,
        "taux_tva": taux_tva,
        "montant_tva": montant_tva,
        "total_ttc": total_ttc
    }


def _line(c, x1, y1, x2, y2, color=colors.HexColor("#cccccc"), width=0.5):
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x1, y1, x2, y2)
    c.setStrokeColor(colors.black)


def dessiner_entete(c, data):
    entreprise = data["entreprise"]
    devis = data["devis"]

    y_title = PAGE_H - 17 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN_X, y_title, entreprise["raison_sociale"])

    c.setFont("Helvetica", 9)
    y = y_title - 7 * mm
    c.drawString(MARGIN_X, y, entreprise["adresse"])
    y -= LINE_SPACING_BODY
    c.drawString(
        MARGIN_X, y,
        f"Tél : {entreprise.get('telephone', '')}  ·  Email : {entreprise.get('email', '')}"
    )

    c.setFont("Helvetica-Bold", 17)
    c.drawRightString(CONTENT_RIGHT, y_title, "DEVIS")

    c.setFont("Helvetica", 10)
    c.drawRightString(CONTENT_RIGHT, y_title - 8 * mm, f"N° {devis['numero']}")
    c.setFont("Helvetica", 9)
    c.drawRightString(CONTENT_RIGHT, y_title - 15 * mm, f"Date : {devis['date']}")
    if devis.get("validite"):
        c.drawRightString(CONTENT_RIGHT, y_title - 21 * mm, f"Validité : {devis['validite']}")

    sep_y = y - GAP_AFTER_HEADER
    _line(c, MARGIN_X, sep_y, CONTENT_RIGHT, sep_y)


def dessiner_bloc_client(c, data):
    client = data["client"]
    devis = data["devis"]

    y = PAGE_H - 17 * mm - 17 * mm - GAP_AFTER_HEADER - 8 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGIN_X, y, "Facturation / Client")
    y -= GAP_AFTER_CLIENT_TITLE + 1 * mm
    c.setFont("Helvetica", 9)
    c.drawString(MARGIN_X, y, client.get("raison_sociale") or client.get("nom", ""))
    y -= LINE_SPACING_BODY
    c.drawString(MARGIN_X, y, client.get("adresse", ""))
    y -= LINE_SPACING_BODY

    # if devis.get("conditions_paiement"):
    #     y -= LINE_SPACING_BODY + 3 * mm
    #     c.setFont("Helvetica-Bold", 9)
    #     c.drawString(MARGIN_X, y, "Conditions de paiement")
    #     y -= 4.5 * mm
    #     c.setFont("Helvetica", 9)
    #     c.drawString(MARGIN_X, y, devis["conditions_paiement"])

    # dernière baseline du bloc client (pour placer le tableau en dessous)
    return y


def construire_tableau_lignes(data):
    lignes = data["lignes"]
    table_data = [
        [
            Paragraph("<b>Désignation</b>", style_normal),
            Paragraph("<b>Qté</b>", style_normal),
            Paragraph("<b>PU HT</b>", style_normal),
            Paragraph("<b>Total HT</b>", style_normal),
        ]
    ]
    for l in lignes:
        desc = l["description"].replace("\n", "<br/>")
        table_data.append([
            Paragraph(desc, style_normal),
            Paragraph(str(l["quantite"]), style_normal),
            Paragraph(format_montant(l["prix_unitaire_ht"]), style_normal),
            Paragraph(format_montant(l["total_ht"]), style_normal),
        ])

    table = Table(table_data, colWidths=[98 * mm, 16 * mm, 28 * mm, 28 * mm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b8b8b8")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#222222")),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
    ]))
    return table


def dessiner_tableau_et_totaux(c, data, totaux, y_derniere_ligne_client):
    table = construire_tableau_lignes(data)
    _w, th = table.wrapOn(c, PAGE_W - 2 * MARGIN_X, PAGE_H)

    # Bas du tableau : sous le texte client, avec écart fixe ; le haut du tableau est à bottom + th
    table_bottom = (
        y_derniere_ligne_client
        - TEXT_DESCENT
        - GAP_BEFORE_TABLE
        - th
    )
    min_bottom = FOOTER_Y + 28 * mm
    if table_bottom < min_bottom:
        table_bottom = min_bottom

    table.drawOn(c, MARGIN_X, table_bottom)

    x_label = CONTENT_RIGHT - 62 * mm
    y = table_bottom - GAP_AFTER_TABLE

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)
    c.drawRightString(x_label, y, "Total HT :")
    c.drawRightString(CONTENT_RIGHT, y, format_montant(totaux["total_ht"]))

    y -= LINE_SPACING_TOTALS
    if totaux["taux_tva"] > 0:
        c.drawRightString(x_label, y, f"TVA {totaux['taux_tva']}% :")


    y -= LINE_SPACING_TOTALS
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(x_label, y, "Total TTC :")
    c.drawRightString(CONTENT_RIGHT, y, format_montant(totaux["total_ttc"]))


def generer_devis_pdf():
    data = charger_donnees()
    totaux = calculer_totaux(data)

    c = canvas.Canvas(OUTPUT_PDF, pagesize=A4)
    c.setTitle(f"Devis {data['devis']['numero']}")

    dessiner_entete(c, data)
    y_client = dessiner_bloc_client(c, data)
    dessiner_tableau_et_totaux(c, data, totaux, y_client)

    c.setFont("Helvetica", 7)
    c.setFillColor(colors.HexColor("#666666"))
    today = datetime.today().strftime("%d/%m/%Y")
    c.drawString(MARGIN_X, FOOTER_Y, f"Devis généré le {today}")
    c.save()
    print(f"Devis généré : {OUTPUT_PDF}")


if __name__ == "__main__":
    generer_devis_pdf()
