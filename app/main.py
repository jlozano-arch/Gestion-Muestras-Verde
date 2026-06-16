from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime
from pathlib import Path
import qrcode
import io
from reportlab.lib.pagesizes import letter, A6
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import json
import os
import shutil

from .database import get_db, create_tables
from .models import Sample, Tasting, Shipment, Event, Document, SampleStatus
from .countries import get_country_name, get_country_flag, get_all_countries

# Create tables on startup
create_tables()

# Create FastAPI app
app = FastAPI(
    title="Gestión de Muestras de Café Verde",
    description="Indian Ecotrade - Sistema de gestión de muestras de café verde",
    version="1.0.0"
)

# Mount static files
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
# Mount uploads for served documents
uploads_path = Path.cwd() / "uploads"
uploads_path.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

# Setup templates
templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))


@app.on_event("startup")
async def startup_event():
    """Startup event"""
    # Create necessary directories
    Path("./data").mkdir(exist_ok=True)
    Path("./uploads").mkdir(exist_ok=True)


# ============================================================================
# DASHBOARD AND MAIN VIEWS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Dashboard principal"""
    total_samples = db.query(Sample).count()
    available_samples = db.query(Sample).filter(
        Sample.status == SampleStatus.AVAILABLE
    ).count()
    # total_quantity in grams using available_quantity_g
    total_quantity = db.query(Sample).filter(
        Sample.available_quantity_g > 0
    ).with_entities(func.sum(Sample.available_quantity_g)).scalar() or 0
    
    recent_samples = db.query(Sample).order_by(desc(Sample.created_at)).limit(5).all()
    high_score_samples = db.query(Sample).join(Tasting).order_by(
        desc(Tasting.indian_score)
    ).limit(5).all()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total_samples": total_samples,
        "available_samples": available_samples,
                "total_quantity": total_quantity,
        "recent_samples": recent_samples,
        "high_score_samples": high_score_samples,
    })


# ============================================================================
# SAMPLE MANAGEMENT
# ============================================================================

@app.get("/samples", response_class=HTMLResponse)
async def list_samples(
    request: Request,
    status: str = None,
    country: str = None,
    producer: str = None,
    supplier_reference: str = None,
    purchase_cvc: str = None,
    sales_cvv: str = None,
    quality: str = None,
    commercial_result: str = None,
    indian_min: float = None,
    indian_max: float = None,
    db: Session = Depends(get_db)
):
    """Lista de muestras"""
    query = db.query(Sample)
    
    if status:
        query = query.filter(Sample.status == status)
    if country:
        query = query.filter(Sample.country_code == country)
    if producer:
        query = query.filter(Sample.producer.ilike(f"%{producer}%"))
    if supplier_reference:
        query = query.filter(Sample.supplier_reference.ilike(f"%{supplier_reference}%"))
    if purchase_cvc:
        query = query.filter(Sample.purchase_contract_cvc == purchase_cvc)
    if sales_cvv:
        query = query.filter(Sample.sales_contract_cvv == sales_cvv)
    if quality:
        query = query.filter(Sample.quality.ilike(f"%{quality}%"))
    if commercial_result:
        query = query.filter(Sample.commercial_result == commercial_result)

    # Indian score range filter: join tastings
    if indian_min is not None or indian_max is not None:
        tquery = db.query(Sample).join(Tasting)
        if indian_min is not None:
            tquery = tquery.filter(Tasting.indian_score >= indian_min)
        if indian_max is not None:
            tquery = tquery.filter(Tasting.indian_score <= indian_max)
        ids = [s.id for s in tquery.distinct().all()]
        query = query.filter(Sample.id.in_(ids))
    
    samples = query.order_by(desc(Sample.created_at)).all()
    
    return templates.TemplateResponse("samples.html", {
        "request": request,
        "samples": samples,
        "countries": get_all_countries(),
        "statuses": [s.value for s in SampleStatus],
    })


@app.get("/samples/new", response_class=HTMLResponse)
async def new_sample_form(request: Request):
    """Formulario para nueva muestra"""
    return templates.TemplateResponse("sample_form.html", {
        "request": request,
        "countries": get_all_countries(),
        "processing_methods": [
            "Washed/Lavado", "Natural/Secado al sol", "Honey/Miel",
            "Anaerobic", "Fermented"
        ]
    })


@app.post("/samples")
async def create_sample(
    code: str = Form(...),
    received_date: str = Form(None),
    initial_quantity_grams: str = Form(None),
    available_quantity_grams: str = Form(None),
    country_code: str = Form(None),
    origin: str = Form(None),
    producer: str = Form(None),
    supplier_reference: str = Form(None),
    provider_sample_number: str = Form(None),
    purchase_contract_cvc: str = Form(None),
    sales_contract_cvv: str = Form(None),
    quality: str = Form(None),
    warehouse: str = Form(None),
    sample_type: str = Form(None),
    category: str = Form(None),
    commercial_result: str = Form(None),
    harvest_date: str = Form(None),
    variety: str = Form(None),
    altitude: int = Form(None),
    processing: str = Form(None),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    """Crear nueva muestra"""
    existing = db.query(Sample).filter(Sample.code == code).first()
    if existing:
        raise HTTPException(status_code=400, detail="El código de muestra ya existe")

    try:
        initial_quantity = float(initial_quantity_grams) / 1000.0 if initial_quantity_grams not in (None, '', '0') else 0.0
    except ValueError:
        initial_quantity = 0.0
    try:
        available_quantity = float(available_quantity_grams) / 1000.0 if available_quantity_grams not in (None, '') else initial_quantity
    except ValueError:
        available_quantity = initial_quantity

    if initial_quantity < 0 or available_quantity < 0:
        raise HTTPException(status_code=400, detail="Las cantidades no pueden ser negativas")
    if initial_quantity != 0 and available_quantity > initial_quantity:
        raise HTTPException(status_code=400, detail="La cantidad disponible no puede ser mayor que la cantidad recibida")

    created_at = datetime.utcnow()
    if received_date:
        try:
            created_at = datetime.fromisoformat(received_date)
        except ValueError:
            created_at = datetime.utcnow()

    sample = Sample(
        code=code,
        country_code=country_code,
        country_name=get_country_name(country_code) if country_code else None,
        origin=origin,
        producer=producer,
        supplier_reference=supplier_reference,
        provider_sample_number=provider_sample_number,
        purchase_contract_cvc=purchase_contract_cvc,
        sales_contract_cvv=sales_contract_cvv,
        quality=quality,
        warehouse=warehouse,
        sample_type=sample_type,
        category=category,
        commercial_result=commercial_result,
        harvest_date=harvest_date,
        variety=variety,
        altitude=altitude,
        processing=processing,
        initial_quantity=initial_quantity,
        available_quantity=available_quantity,
        received_quantity_g=int(initial_quantity_grams or 0),
        available_quantity_g=int(available_quantity_grams if available_quantity_grams is not None else (initial_quantity_grams or 0)),
        notes=notes,
        status=SampleStatus.RECEIVED,
        created_at=created_at
    )

    db.add(sample)
    db.commit()
    db.refresh(sample)

    event = Event(
        sample_id=sample.id,
        event_type="received",
        description=f"Muestra registrada - {int(initial_quantity_grams or 0)} g"
    )
    db.add(event)
    db.commit()

    return JSONResponse({"id": sample.id, "code": sample.code})


@app.get("/samples/{sample_id}/edit", response_class=HTMLResponse)
async def edit_sample_form(sample_id: int, request: Request, db: Session = Depends(get_db)):
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Muestra no encontrada")

    return templates.TemplateResponse("sample_form.html", {
        "request": request,
        "sample": sample,
        "action_url": f"/samples/{sample.id}",
        "submit_label": "Actualizar muestra",
        "countries": get_all_countries(),
        "processing_methods": [
            "Washed/Lavado", "Natural/Secado al sol", "Honey/Miel",
            "Anaerobic", "Fermented"
        ]
    })


@app.post("/samples/{sample_id}")
async def update_sample(
    sample_id: int,
    code: str = Form(...),
    received_date: str = Form(None),
    initial_quantity_grams: int = Form(None),
    available_quantity_grams: int = Form(None),
    country_code: str = Form(None),
    origin: str = Form(None),
    producer: str = Form(None),
    supplier_reference: str = Form(None),
    provider_sample_number: str = Form(None),
    purchase_contract_cvc: str = Form(None),
    sales_contract_cvv: str = Form(None),
    quality: str = Form(None),
    warehouse: str = Form(None),
    sample_type: str = Form(None),
    category: str = Form(None),
    commercial_result: str = Form(None),
    harvest_date: str = Form(None),
    variety: str = Form(None),
    altitude: int = Form(None),
    processing: str = Form(None),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Muestra no encontrada")
    existing = db.query(Sample).filter(Sample.code == code, Sample.id != sample_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="El código de muestra ya existe")

    try:
        initial_quantity = float(initial_quantity_grams) / 1000.0 if initial_quantity_grams not in (None, '', '0') else 0.0
    except ValueError:
        initial_quantity = 0.0
    try:
        available_quantity = float(available_quantity_grams) / 1000.0 if available_quantity_grams not in (None, '') else initial_quantity
    except ValueError:
        available_quantity = initial_quantity

    if initial_quantity < 0 or available_quantity < 0:
        raise HTTPException(status_code=400, detail="Las cantidades no pueden ser negativas")
    if initial_quantity != 0 and available_quantity > initial_quantity:
        raise HTTPException(status_code=400, detail="La cantidad disponible no puede ser mayor que la cantidad recibida")

    sample.code = code
    sample.country_code = country_code
    sample.country_name = get_country_name(country_code) if country_code else None
    sample.origin = origin
    sample.producer = producer
    sample.supplier_reference = supplier_reference
    sample.provider_sample_number = provider_sample_number
    sample.purchase_contract_cvc = purchase_contract_cvc
    sample.sales_contract_cvv = sales_contract_cvv
    sample.quality = quality
    sample.warehouse = warehouse
    sample.sample_type = sample_type
    sample.category = category
    sample.commercial_result = commercial_result
    sample.harvest_date = harvest_date
    sample.variety = variety
    sample.altitude = altitude
    sample.processing = processing
    sample.initial_quantity = initial_quantity
    sample.available_quantity = available_quantity
    sample.received_quantity_g = int(initial_quantity_grams or 0)
    sample.available_quantity_g = int(available_quantity_grams if available_quantity_grams is not None else (initial_quantity_grams or 0))
    sample.notes = notes

    if received_date:
        try:
            sample.created_at = datetime.fromisoformat(received_date)
        except ValueError:
            pass

    db.commit()
    db.refresh(sample)
    return JSONResponse({"id": sample.id, "code": sample.code})


@app.get("/samples/{sample_id}", response_class=HTMLResponse)
async def sample_detail(
    sample_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Detalle de muestra"""
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Muestra no encontrada")
    
    tastings = db.query(Tasting).filter(Tasting.sample_id == sample_id).all()
    shipments = db.query(Shipment).filter(Shipment.sample_id == sample_id).all()
    events = db.query(Event).filter(Event.sample_id == sample_id).order_by(
        desc(Event.event_date)
    ).all()
    documents = db.query(Document).filter(Document.sample_id == sample_id).all()
    
    best_tasting = None
    if tastings:
        best_tasting = max(tastings, key=lambda x: x.indian_score or 0)
    
    return templates.TemplateResponse("sample_detail.html", {
        "request": request,
        "sample": sample,
        "tastings": tastings,
        "shipments": shipments,
        "events": events,
        "documents": documents,
        "best_tasting": best_tasting,
        "flag": get_country_flag(sample.country_code),
    })


@app.post("/samples/{sample_id}/tastings/{tasting_id}/documents")
async def upload_tasting_document(sample_id: int, tasting_id: int, file: UploadFile = File(...), document_type: str = Form(None), db: Session = Depends(get_db)):
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    tasting = db.query(Tasting).filter(Tasting.id == tasting_id, Tasting.sample_id == sample_id).first()
    if not sample or not tasting:
        raise HTTPException(status_code=404, detail="Sample or tasting not found")

    upload_dir = os.path.join("uploads", "samples", str(sample_id), "tastings", str(tasting_id))
    os.makedirs(upload_dir, exist_ok=True)
    filename = os.path.basename(file.filename)
    safe_name = f"{int(datetime.utcnow().timestamp())}_{filename}"
    save_path = os.path.join(upload_dir, safe_name)

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = Document(sample_id=sample.id, tasting_id=tasting.id, file_name=filename, file_path=save_path, file_type=document_type or file.content_type)
    db.add(doc)
    db.commit()

    return RedirectResponse(f"/samples/{sample_id}", status_code=303)


@app.get("/samples/{sample_id}/tastings/{tasting_id}/pdf")
async def tasting_pdf(sample_id: int, tasting_id: int, db: Session = Depends(get_db)):
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    tasting = db.query(Tasting).filter(Tasting.id == tasting_id, Tasting.sample_id == sample_id).first()
    if not sample or not tasting:
        raise HTTPException(status_code=404, detail="Sample or tasting not found")

    # create PDF with sample + tasting info and include tasting images if any
    docs = db.query(Document).filter(Document.tasting_id == tasting_id).all()

    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter

    # Header with logo
    try:
        logo_path = Path(__file__).parent / "static" / "logo.png"
        if logo_path.exists():
            c.drawImage(ImageReader(str(logo_path)), 10*mm, height - 30*mm, width=40*mm, height=15*mm, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass

    c.setFont("Helvetica-Bold", 12)
    c.drawString(10*mm, height - 40*mm, f"Ficha de cata - {sample.code}")
    c.setFont("Helvetica", 10)
    c.drawString(10*mm, height - 50*mm, f"Proveedor: {sample.producer or '-'} | Ref: {sample.supplier_reference or '-'} | CVC: {sample.purchase_contract_cvc or '-'}")

    # Tasting details
    y = height - 65*mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(10*mm, y, f"Cata por: {tasting.evaluator}")
    y -= 6*mm
    c.setFont("Helvetica", 9)
    c.drawString(10*mm, y, f"Fecha: {tasting.tasting_date.strftime('%Y-%m-%d')}")
    y -= 6*mm
    c.drawString(10*mm, y, f"Humedad: {tasting.humidity}%  Cribas: 18+ {tasting.sieve_18}% 16+ {tasting.sieve_16}% 14+ {tasting.sieve_14}%")
    y -= 6*mm
    c.drawString(10*mm, y, f"Defectos (prim/seg): {tasting.defects_primary}/{tasting.defects_secondary}")
    y -= 6*mm
    c.drawString(10*mm, y, f"Indian Score: {tasting.indian_score:.1f}  Cup Score: {tasting.cup_score:.1f}  Comercial: {tasting.commercial_score:.1f}")
    y -= 8*mm
    if tasting.tasting_notes:
        c.drawString(10*mm, y, "Notas:")
        y -= 5*mm
        text = c.beginText(10*mm, y)
        text.setFont("Helvetica", 8)
        for line in (tasting.tasting_notes or "").splitlines():
            text.textLine(line)
            y -= 4*mm
        c.drawText(text)

    # Images: include up to 4 thumbnails
    img_x = 10*mm
    img_y = y - 10*mm
    for doc in docs[:4]:
        try:
            c.drawImage(ImageReader(doc.file_path), img_x, img_y, width=45*mm, height=30*mm, preserveAspectRatio=True, mask='auto')
            img_x += 50*mm
        except Exception:
            continue

    c.save()
    pdf_buffer.seek(0)
    return FileResponse(pdf_buffer, media_type="application/pdf", filename=f"ficha_cata_{sample.code}_{tasting_id}.pdf")


@app.post("/samples/{sample_id}/documents")
async def upload_document(sample_id: int, file: UploadFile = File(...), document_type: str = Form(None), db: Session = Depends(get_db)):
    """Upload a document or photo for a sample"""
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    upload_dir = os.path.join("uploads", str(sample_id))
    os.makedirs(upload_dir, exist_ok=True)
    filename = os.path.basename(file.filename)
    safe_name = f"{int(datetime.utcnow().timestamp())}_{filename}"
    save_path = os.path.join(upload_dir, safe_name)

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = Document(sample_id=sample.id, file_name=filename, file_path=save_path, file_type=document_type or file.content_type)
    db.add(doc)
    db.commit()

    return RedirectResponse(f"/samples/{sample_id}", status_code=303)


# ============================================================================
# TASTING/CUPPING
# ============================================================================

@app.post("/samples/{sample_id}/tastings")
async def create_tasting(
    sample_id: int,
    evaluator: str = Form(...),
    tasting_date: str = Form(None),
    roast_date: str = Form(None),
    sieve_18: float = Form(...),
    sieve_17: float = Form(None),
    sieve_16: float = Form(...),
    sieve_15: float = Form(None),
    sieve_14: float = Form(...),
    sieve_13: float = Form(None),
    sieve_12: float = Form(None),
    sieve_plato: float = Form(None),
    humidity: float = Form(...),
    defects_primary: int = Form(0),
    defects_secondary: int = Form(0),
    aroma: float = Form(...),
    acidity: float = Form(...),
    body: float = Form(...),
    flavor: float = Form(...),
    aftertaste: float = Form(...),
    cleanliness: float = Form(...),
    balance: float = Form(...),
    tasting_notes: str = Form(None),
    recommendations: str = Form(None),
    valuation: float = Form(None),
    result: str = Form(None),
    redirect: str = Form(None),
    db: Session = Depends(get_db)
):
    """Crear cata/evaluación"""
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Muestra no encontrada")
    
    # Parse optional dates
    td = datetime.utcnow()
    if tasting_date:
        try:
            td = datetime.fromisoformat(tasting_date)
        except Exception:
            td = datetime.utcnow()

    rd = None
    if roast_date:
        try:
            rd = datetime.fromisoformat(roast_date)
        except Exception:
            rd = None

    # Calculate scores
    cup_score = (aroma + acidity + body + flavor + aftertaste + cleanliness + balance) / 7
    
    # Indian Score: proprietary calculation
    # SCA-based with custom adjustments
    base_score = cup_score
    sieve_bonus = (sieve_18 * 0.5) if sieve_18 >= 50 else 0
    humidity_penalty = 5 if humidity > 12 else 0
    defect_penalty = (defects_primary * 2) + (defects_secondary * 1)
    
    indian_score = min(100, max(0, base_score + (sieve_bonus - humidity_penalty - defect_penalty)))
    
    # Commercial score based on commercial viability
    commercial_score = indian_score
    if humidity > 12:
        commercial_score -= 10
    if defects_primary > 5:
        commercial_score -= 20
    
    commercial_score = max(0, min(100, commercial_score))
    
    tasting = Tasting(
        sample_id=sample_id,
        evaluator=evaluator,
        tasting_date=td,
        roast_date=rd,
        sieve_18=sieve_18,
        sieve_17=sieve_17,
        sieve_16=sieve_16,
        sieve_15=sieve_15,
        sieve_14=sieve_14,
        sieve_13=sieve_13,
        sieve_12=sieve_12,
        sieve_plato=sieve_plato,
        humidity=humidity,
        defects_primary=defects_primary,
        defects_secondary=defects_secondary,
        aroma=aroma,
        acidity=acidity,
        body=body,
        flavor=flavor,
        aftertaste=aftertaste,
        cleanliness=cleanliness,
        balance=balance,
        cup_score=cup_score,
        indian_score=indian_score,
        commercial_score=commercial_score,
        tasting_notes=tasting_notes,
        recommendations=recommendations,
        valuation=valuation,
        result=(result if result in ["pending","approved","rejected"] else None)
    )
    
    db.add(tasting)
    
    # Update sample status
    if sample.status == SampleStatus.RECEIVED:
        sample.status = SampleStatus.ANALYZING
    
    # Create event
    event = Event(
        sample_id=sample_id,
        event_type="tasted",
        description=f"Evaluada con puntuación Indian Score: {indian_score:.1f}"
    )
    db.add(event)
    
    db.commit()
    db.refresh(tasting)

    if redirect:
        return RedirectResponse(f"/samples/{sample_id}", status_code=303)

    return JSONResponse({"id": tasting.id, "indian_score": indian_score})


# ============================================================================
# SHIPMENTS
# ============================================================================

@app.post("/samples/{sample_id}/shipments")
async def create_shipment(
    sample_id: int,
    quantity_g: int = Form(...),
    destination: str = Form(...),
    reference: str = Form(...),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    """Registrar envío"""
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Muestra no encontrada")
    
    if quantity_g > sample.available_quantity_g:
        raise HTTPException(
            status_code=400,
            detail=f"Cantidad solicitada ({quantity_g} g) mayor que disponible ({sample.available_quantity_g} g)"
        )
    
    # Create shipment
    shipment = Shipment(
        sample_id=sample_id,
        quantity=quantity_g / 1000.0,
        quantity_g=quantity_g,
        destination=destination,
        reference=reference,
        notes=notes,
        status="pending"
    )
    
    # Reduce available quantity (grams and kg)
    sample.available_quantity_g -= quantity_g
    sample.available_quantity -= (quantity_g / 1000.0)
    
    # Update status
    if sample.available_quantity <= 0:
        sample.status = SampleStatus.SHIPPED
    elif sample.available_quantity < sample.initial_quantity:
        sample.status = SampleStatus.PARTIALLY_SHIPPED
    
    # Create event
    event = Event(
        sample_id=sample_id,
        event_type="shipped",
        description=f"Envío de {quantity_g} g a {destination}"
    )
    
    db.add(shipment)
    db.add(event)
    db.commit()
    db.refresh(shipment)
    
    return JSONResponse({"id": shipment.id, "quantity": quantity})


# ============================================================================
# PDF LABELS WITH QR
# ============================================================================

@app.get("/samples/{sample_id}/label")
async def generate_label(sample_id: int, db: Session = Depends(get_db)):
    """Generar etiqueta PDF con QR"""
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Muestra no encontrada")
    
    best_tasting = db.query(Tasting).filter(
        Tasting.sample_id == sample_id
    ).order_by(desc(Tasting.indian_score)).first()
    
    # Generate QR code pointing to the sample detail (public relative URL)
    qr_data = f"http://localhost:8000/samples/{sample_id}"
    qr = qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Create PDF
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A6)
    
    # Dimensions
    width, height = A6
    

    # Title and logo
    c.setFont("Helvetica-Bold", 10)
    c.drawString(10*mm, height - 10*mm, "INDIAN ECOTRADE")
    c.setFont("Helvetica", 8)
    c.drawString(10*mm, height - 15*mm, "Café Verde")

    # Try to draw logo if exists
    try:
        logo_path = Path(__file__).parent / "static" / "logo.png"
        if logo_path.exists():
            logo_reader = ImageReader(str(logo_path))
            c.drawImage(logo_reader, width - 40*mm, height - 18*mm, width=28*mm, height=12*mm, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass

    # Sample info block
    c.setFont("Helvetica-Bold", 8)
    c.drawString(10*mm, height - 22*mm, f"Código: {sample.code}")
    c.setFont("Helvetica", 7)
    # country and flag (flag may be emoji)
    try:
        flag = get_country_flag(sample.country_code)
    except Exception:
        flag = ''
    c.drawString(10*mm, height - 26*mm, f"País: {sample.country_name} {flag}")
    c.drawString(10*mm, height - 29*mm, f"Origen: {sample.origin}")
    c.drawString(10*mm, height - 32*mm, f"Calidad: {sample.quality or '-'}")
    c.drawString(10*mm, height - 35*mm, f"Proveedor: {sample.producer or '-'}")
    c.drawString(10*mm, height - 38*mm, f"Ref. proveedor: {sample.supplier_reference or '-'}")
    c.drawString(10*mm, height - 41*mm, f"Contrato CVC: {sample.purchase_contract_cvc or '-'}")
    if sample.sales_contract_cvv:
        c.drawString(10*mm, height - 44*mm, f"Contrato CVV: {sample.sales_contract_cvv}")
    c.drawString(10*mm, height - 47*mm, f"Disponibles: {sample.available_quantity} kg")

    if best_tasting:
        c.setFont("Helvetica-Bold", 8)
        c.drawString(10*mm, height - 51*mm, f"Indian Score: {best_tasting.indian_score:.1f}")
    
    # QR Code
    qr_path = io.BytesIO()
    qr_img.save(qr_path, format="PNG")
    qr_path.seek(0)
    
    try:
        c.drawImage(ImageReader(qr_path), width - 35*mm, 10*mm, width=25*mm, height=25*mm)
    except:
        pass
    
    c.save()
    
    pdf_buffer.seek(0)
    return FileResponse(
        pdf_buffer,
        media_type="application/pdf",
        filename=f"muestra_{sample.code}.pdf"
    )


# ============================================================================
# COMPARATOR
# ============================================================================

@app.get("/compare", response_class=HTMLResponse)
async def compare_samples(
    request: Request,
    ids: str = None,
    db: Session = Depends(get_db)
):
    """Comparador de muestras"""
    samples = []
    tastings = []
    
    if ids:
        sample_ids = [int(id) for id in ids.split(",")]
        samples = db.query(Sample).filter(Sample.id.in_(sample_ids)).all()
        tastings = {
            s.id: db.query(Tasting).filter(
                Tasting.sample_id == s.id
            ).order_by(desc(Tasting.indian_score)).first()
            for s in samples
        }
    
    return templates.TemplateResponse("compare.html", {
        "request": request,
        "samples": samples,
        "tastings": tastings,
        "all_samples": db.query(Sample).all(),
    })


@app.get('/labels', response_class=HTMLResponse)
async def labels_page(request: Request, db: Session = Depends(get_db)):
    samples = db.query(Sample).order_by(desc(Sample.created_at)).all()
    return templates.TemplateResponse('labels.html', {"request": request, "all_samples": samples})


@app.get('/tastings', response_class=HTMLResponse)
async def list_tastings(request: Request, db: Session = Depends(get_db)):
    tastings = db.query(Tasting).order_by(desc(Tasting.tasting_date)).all()
    return templates.TemplateResponse('tastings.html', {"request": request, "tastings": tastings})


@app.get('/samples/{sample_id}/tastings/new', response_class=HTMLResponse)
async def new_tasting_form(sample_id: int, request: Request, db: Session = Depends(get_db)):
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Muestra no encontrada")
    return templates.TemplateResponse('tasting_form.html', {"request": request, "sample": sample})


# ============================================================================
# IMPORT/EXPORT
# ============================================================================

@app.post("/import/excel")
async def import_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Importar muestras desde Excel"""
    try:
        from openpyxl import load_workbook
        
        contents = await file.read()
        wb = load_workbook(filename=io.BytesIO(contents))
        ws = wb.active
        
        imported = 0
        errors = []
        
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            try:
                # Try to unpack common columns; handle extra optional columns
                values = list(row)
                code = values[0] if len(values) > 0 else None
                country = values[1] if len(values) > 1 else None
                origin = values[2] if len(values) > 2 else None
                producer = values[3] if len(values) > 3 else None
                harvest = values[4] if len(values) > 4 else None
                variety = values[5] if len(values) > 5 else None
                altitude = values[6] if len(values) > 6 else None
                processing = values[7] if len(values) > 7 else None
                quantity = values[8] if len(values) > 8 else None
                # extra fields
                supplier_reference = values[9] if len(values) > 9 else None
                provider_sample_number = values[10] if len(values) > 10 else None
                purchase_cvc = values[11] if len(values) > 11 else None
                sales_cvv = values[12] if len(values) > 12 else None
                quality = values[13] if len(values) > 13 else None
                warehouse = values[14] if len(values) > 14 else None
                sample_type = values[15] if len(values) > 15 else None
                category = values[16] if len(values) > 16 else None
                comments = values[17] if len(values) > 17 else None

                if not code:
                    continue

                existing = db.query(Sample).filter(Sample.code == code).first()
                if existing:
                    errors.append(f"Row {row_idx}: Código duplicado")
                    continue

                sample = Sample(
                    code=str(code).strip(),
                    country_code=str(country).strip()[:5] if country else None,
                    country_name=get_country_name(str(country).strip()[:5]) if country else None,
                    origin=str(origin).strip() if origin else "",
                    producer=str(producer).strip() if producer else "",
                    supplier_reference=str(supplier_reference).strip() if supplier_reference else None,
                    provider_sample_number=str(provider_sample_number).strip() if provider_sample_number else None,
                    purchase_contract_cvc=str(purchase_cvc).strip() if purchase_cvc else None,
                    sales_contract_cvv=str(sales_cvv).strip() if sales_cvv else None,
                    quality=str(quality).strip() if quality else None,
                    warehouse=str(warehouse).strip() if warehouse else None,
                    sample_type=str(sample_type).strip() if sample_type else None,
                    category=str(category).strip() if category else None,
                    notes=str(comments).strip() if comments else None,
                    harvest_date=str(harvest).strip() if harvest else "",
                    variety=str(variety).strip() if variety else "",
                    altitude=int(altitude) if altitude else 0,
                    processing=str(processing).strip() if processing else "",
                    initial_quantity=float(quantity) if quantity else 0,
                    available_quantity=float(quantity) if quantity else 0,
                )

                db.add(sample)
                imported += 1

            except Exception as e:
                errors.append(f"Row {row_idx}: {str(e)}")
        
        db.commit()
        
        return JSONResponse({
            "imported": imported,
            "errors": errors
        })
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/import", response_class=HTMLResponse)
async def import_form(request: Request):
    return templates.TemplateResponse("import.html", {"request": request})


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/api/samples")
async def api_samples(db: Session = Depends(get_db)):
    """API: Lista de muestras"""
    samples = db.query(Sample).all()
    return {
        "samples": [
            {
                "id": s.id,
                "code": s.code,
                "country": s.country_name,
                "origin": s.origin,
                "available": s.available_quantity,
                "status": s.status.value,
            }
            for s in samples
        ]
    }


@app.get("/api/samples/{sample_id}")
async def api_sample_detail(sample_id: int, db: Session = Depends(get_db)):
    """API: Detalle de muestra"""
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Not found")
    
    tastings = db.query(Tasting).filter(Tasting.sample_id == sample_id).all()
    
    return {
        "id": sample.id,
        "code": sample.code,
        "country": sample.country_name,
        "origin": sample.origin,
        "producer": sample.producer,
        "available": sample.available_quantity,
        "status": sample.status.value,
        "tastings": [
            {
                "id": t.id,
                "evaluator": t.evaluator,
                "date": t.tasting_date.isoformat(),
                "indian_score": t.indian_score,
                "cup_score": t.cup_score,
                "commercial_score": t.commercial_score,
            }
            for t in tastings
        ]
    }


@app.get("/api/health")
async def health():
    """Health check"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
