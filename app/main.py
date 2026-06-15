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
    total_quantity = db.query(Sample).filter(
        Sample.available_quantity > 0
    ).with_entities(func.sum(Sample.available_quantity)).scalar() or 0
    
    recent_samples = db.query(Sample).order_by(desc(Sample.created_at)).limit(5).all()
    high_score_samples = db.query(Sample).join(Tasting).order_by(
        desc(Tasting.indian_score)
    ).limit(5).all()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total_samples": total_samples,
        "available_samples": available_samples,
        "total_quantity": f"{total_quantity:.1f}",
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
    country_code: str = Form(...),
    origin: str = Form(...),
    producer: str = Form(...),
    supplier_reference: str = Form(None),
    provider_sample_number: str = Form(None),
    purchase_contract_cvc: str = Form(None),
    sales_contract_cvv: str = Form(None),
    quality: str = Form(None),
    warehouse: str = Form(None),
    sample_type: str = Form(None),
    category: str = Form(None),
    commercial_result: str = Form(None),
    harvest_date: str = Form(...),
    variety: str = Form(...),
    altitude: int = Form(...),
    processing: str = Form(...),
    initial_quantity: float = Form(...),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    """Crear nueva muestra"""
    # Check if code already exists
    existing = db.query(Sample).filter(Sample.code == code).first()
    if existing:
        raise HTTPException(status_code=400, detail="El código de muestra ya existe")
    
    # Create sample
    sample = Sample(
        code=code,
        country_code=country_code,
        country_name=get_country_name(country_code),
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
        available_quantity=initial_quantity,
        notes=notes,
        status=SampleStatus.RECEIVED
    )
    
    db.add(sample)
    db.commit()
    db.refresh(sample)
    
    # Create event
    event = Event(
        sample_id=sample.id,
        event_type="received",
        description=f"Muestra recibida - {initial_quantity}kg"
    )
    db.add(event)
    db.commit()
    
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
    sieve_18: float = Form(...),
    sieve_16: float = Form(...),
    sieve_14: float = Form(...),
    humidity: float = Form(...),
    defects_primary: int = Form(0),
    defects_secondary: int = Form(0),
    aroma: int = Form(...),
    acidity: int = Form(...),
    body: int = Form(...),
    flavor: int = Form(...),
    aftertaste: int = Form(...),
    cleanliness: int = Form(...),
    balance: int = Form(...),
    tasting_notes: str = Form(None),
    recommendations: str = Form(None),
    db: Session = Depends(get_db)
):
    """Crear cata/evaluación"""
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Muestra no encontrada")
    
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
        tasting_date=datetime.utcnow(),
        sieve_18=sieve_18,
        sieve_16=sieve_16,
        sieve_14=sieve_14,
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
    
    return JSONResponse({"id": tasting.id, "indian_score": indian_score})


# ============================================================================
# SHIPMENTS
# ============================================================================

@app.post("/samples/{sample_id}/shipments")
async def create_shipment(
    sample_id: int,
    quantity: float = Form(...),
    destination: str = Form(...),
    reference: str = Form(...),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    """Registrar envío"""
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Muestra no encontrada")
    
    if quantity > sample.available_quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Cantidad solicitada ({quantity}kg) mayor que disponible ({sample.available_quantity}kg)"
        )
    
    # Create shipment
    shipment = Shipment(
        sample_id=sample_id,
        quantity=quantity,
        destination=destination,
        reference=reference,
        notes=notes,
        status="pending"
    )
    
    # Reduce available quantity
    sample.available_quantity -= quantity
    
    # Update status
    if sample.available_quantity <= 0:
        sample.status = SampleStatus.SHIPPED
    elif sample.available_quantity < sample.initial_quantity:
        sample.status = SampleStatus.PARTIALLY_SHIPPED
    
    # Create event
    event = Event(
        sample_id=sample_id,
        event_type="shipped",
        description=f"Envío de {quantity}kg a {destination}"
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
