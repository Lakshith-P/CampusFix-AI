from pathlib import Path
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from .config import settings
from .database import Base, engine, get_db
from .models import User, Complaint, AuditEvent, AIUsage, ComplaintAttachment
from .schemas import RegisterIn, LoginIn, TokenOut, UserOut, ComplaintIn, ComplaintOut, ComplaintUpdate
from .security import hash_password, verify_password, create_access_token, get_current_user, require_roles
from .ai import classify, verify_with_second_model, detect_location_conflicts, _call_provider, configured_providers
from .multimodal import extract_attachment
from .prompt_registry import prompt_manifest

Base.metadata.create_all(bind=engine)
# Lightweight SQLite-safe migration for databases created by earlier CampusFix ZIPs.
if settings.database_url.startswith("sqlite"):
    from sqlalchemy import inspect, text
    with engine.begin() as conn:
        cols = {c["name"] for c in inspect(engine).get_columns("users")}
        if "specialization" not in cols: conn.execute(text("ALTER TABLE users ADD COLUMN specialization VARCHAR(80) NOT NULL DEFAULT ''"))
        if "available" not in cols: conn.execute(text("ALTER TABLE users ADD COLUMN available BOOLEAN NOT NULL DEFAULT 1"))
app=FastAPI(title="CampusFix AI API",version="2.11.0",description="Multimodal campus complaint triage and resolution")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",allow_credentials=True,allow_methods=["GET","POST","PATCH","DELETE","OPTIONS"],allow_headers=["Authorization","Content-Type"])

def audit(db,actor,action,entity,entity_id,detail=""):
    db.add(AuditEvent(actor_id=actor.id if actor else None,action=action,entity_type=entity,entity_id=str(entity_id),detail=detail))

def record_usage(db,result,success=True):
    cost=(result.input_tokens+result.output_tokens)/1000000*settings.ai_cost_per_million_tokens_usd if result.provider not in {"rules_fallback", "local_dataset_ml"} else 0.0
    db.add(AIUsage(provider=result.provider,model=result.model,input_tokens=result.input_tokens,output_tokens=result.output_tokens,estimated_cost_usd=cost,success=success))

def enforce_ai_budget(db:Session):
    month_start=datetime.now(timezone.utc).replace(day=1,hour=0,minute=0,second=0,microsecond=0)
    current_cost=db.scalar(select(func.coalesce(func.sum(AIUsage.estimated_cost_usd),0.0)).where(AIUsage.created_at>=month_start)) or 0.0
    if settings.ai_monthly_budget_usd > 0 and current_cost + settings.ai_estimated_cost_per_call_usd > settings.ai_monthly_budget_usd:
        raise HTTPException(429,"AI budget limit would be exceeded; request was not processed")


async def selected_text_result(source:str, mode:str, provider:str, model:str, second_provider:str="", second_model:str=""):
    """Run explicitly selected text model(s); auto mode uses the existing free-only router."""
    mode=(mode or "auto").casefold()
    allowed={"groq":settings.groq_model,"gemini":settings.gemini_model,"openrouter":settings.openrouter_model}
    if mode=="auto":
        return await classify(source), "automatic free-tier routing"
    if provider not in allowed or not allowed[provider] or model!=allowed[provider]:
        raise HTTPException(422,"Selected text provider/model is not in the configured free-tier allow-list")
    if not getattr(settings, f"{provider}_api_key", None):
        raise HTTPException(424,f"{provider} credentials are not configured")
    first=await _call_provider(provider,source[:settings.ai_max_input_chars],model_override=model)
    if mode!="compare": return first, "manual provider/model selection"
    if second_provider not in allowed or not allowed[second_provider] or second_model!=allowed[second_provider]:
        raise HTTPException(422,"Second comparison model is not in the configured free-tier allow-list")
    if second_provider==provider and second_model==model:
        raise HTTPException(422,"Choose a different second model for comparison")
    if not getattr(settings, f"{second_provider}_api_key", None):
        raise HTTPException(424,f"Second provider {second_provider} credentials are not configured")
    second=await _call_provider(second_provider,source[:settings.ai_max_input_chars],model_override=second_model)
    mismatch=(first.category.casefold()!=second.category.casefold() or first.priority.casefold()!=second.priority.casefold() or first.department.casefold()!=second.department.casefold())
    first.human_review=bool(first.human_review or second.human_review or mismatch)
    return first, f"comparison: {provider}/{model} vs {second_provider}/{second_model}; disagreement={mismatch}"

def suggest_specialist(db:Session, category:str, confidence:float, needs_review:bool):
    """Suggest an available worker by explicit specialization; never auto-assign uncertain cases."""
    if confidence < 0.70 or needs_review:
        return None
    key=category.casefold()
    if "plumb" in key or "water" in key: required="plumbing"
    elif "elect" in key or "safety" in key: required="electrical"
    elif "hvac" in key or "air condition" in key or "air conditioning" in key: required="hvac"
    elif "sanit" in key or "clean" in key: required="housekeeping"
    elif "network" in key or "it/" in key or key == "it": required="it and network"
    elif "carpent" in key or "furniture" in key: required="carpentry"
    elif "civil" in key: required="civil maintenance"
    else: required="general maintenance"
    workers=db.scalars(select(User).where(User.role=="staff",User.active.is_(True),User.available.is_(True)).order_by(User.id)).all()
    matching=[w for w in workers if required in (w.specialization or "").casefold()]
    return matching[0].id if matching else None

@app.get("/ai/catalog")
def ai_catalog(user:User=Depends(get_current_user)):
    """Return provider capabilities to every authenticated portal role.

    This endpoint is intentionally NOT admin-only: students and maintenance staff
    need the same capability catalogue to select compatible models in their forms.
    API keys are never returned; only boolean configured flags are exposed.
    """
    return {"mode":"free_only","prompt_version":"registry","prompts":prompt_manifest(),"providers":[
        {"id":"groq","configured":bool(settings.groq_api_key),"models":[{"id":settings.groq_model,"modalities":["text"]},{"id":settings.groq_audio_model,"modalities":["audio"]}]},
        {"id":"gemini","configured":bool(settings.gemini_api_key),"models":[{"id":settings.gemini_model,"modalities":["text","vision","audio","document"]}]+([{"id":settings.gemini_document_secondary_model,"modalities":["document"]}] if settings.gemini_document_secondary_model else [])},
        {"id":"openrouter","configured":bool(settings.openrouter_api_key),"models":[{"id":settings.openrouter_model,"modalities":["text"]}]+([{"id":settings.openrouter_vision_model,"modalities":["vision"]}] if settings.openrouter_vision_model else [])},
        {"id":"local","configured":True,"models":[{"id":"pypdf","modalities":["document"]}]}
    ],"paid_fallback":False,"note":"Only configured providers are callable. PDF extraction is local; free-tier quota and model availability are provider-controlled."}


@app.get("/ai/prompts")
def ai_prompt_versions(user:User=Depends(get_current_user)):
    """Expose prompt keys/immutable versions to authenticated users; never expose secrets."""
    return {"active":prompt_manifest(),"policy":"prompt instructions are trusted; complaint/media payloads are untrusted evidence"}

def auto_provider_candidates(modality: str) -> list[tuple[str, str]]:
    """Ordered free-tier allow-list. Text can fail over across configured providers;
    modalities with a single supported adapter remain single-provider and fail closed.
    """
    candidates = {
        "text": [("groq", settings.groq_model, settings.groq_api_key),
                 ("gemini", settings.gemini_model, settings.gemini_api_key),
                 ("openrouter", settings.openrouter_model, settings.openrouter_api_key)],
        "vision": [("gemini", settings.gemini_model, settings.gemini_api_key), ("openrouter", settings.openrouter_vision_model, settings.openrouter_api_key)],
        "audio": [("groq", settings.groq_audio_model, settings.groq_api_key), ("gemini", settings.gemini_model, settings.gemini_api_key)],
        "document": [("gemini", settings.gemini_model, settings.gemini_api_key), ("local", "pypdf", True)],
    }
    return [(provider, model) for provider, model, configured in candidates.get(modality, []) if configured and model]

@app.post("/ai/execute")
async def ai_execute(modality:str=Form(...),provider:str=Form(...),model:str=Form(...),prompt:str=Form(""),file:UploadFile|None=File(None),db:Session=Depends(get_db),admin:User=Depends(get_current_user)):
    """Capability-aware authenticated execution. Auto text mode retries the ordered free allow-list."""
    modality=modality.casefold().strip(); provider=provider.casefold().strip(); model=model.strip()
    capabilities={
      "text":{"groq":(settings.groq_model,settings.groq_api_key),"gemini":(settings.gemini_model,settings.gemini_api_key),"openrouter":(settings.openrouter_model,settings.openrouter_api_key)},
      "vision":{"gemini":(settings.gemini_model,settings.gemini_api_key),"openrouter":(settings.openrouter_vision_model,settings.openrouter_api_key)},
      "audio":{"groq":(settings.groq_audio_model,settings.groq_api_key),"gemini":(settings.gemini_model,settings.gemini_api_key)},
      "document":{"local":("pypdf",True),"gemini":(settings.gemini_model,settings.gemini_api_key)}
    }
    if modality not in capabilities: raise HTTPException(422,"Unsupported modality")
    auto_used = provider == "auto"
    if auto_used:
      candidates=auto_provider_candidates(modality)
      if not candidates: raise HTTPException(424,f"No configured free provider supports {modality}")
      provider,model=candidates[0]
    if provider not in capabilities[modality]: raise HTTPException(422,"Provider does not support this modality")
    allowed_model,key=capabilities[modality][provider]
    if not allowed_model or (model != "auto" and model != allowed_model): raise HTTPException(422,"Model is not in the backend capability allow-list")
    model=allowed_model
    if not key: raise HTTPException(424,f"{provider} credentials are not configured in backend/.env")
    if modality=="text":
      if not prompt.strip(): raise HTTPException(422,"Enter text to analyze")
      enforce_ai_budget(db)
      candidates=auto_provider_candidates("text") if auto_used else [(provider,model)]
      failures=[]; r=None
      for candidate_provider,candidate_model in candidates:
        try:
          r=await _call_provider(candidate_provider,prompt[:settings.ai_max_input_chars],model_override=candidate_model)
          provider,model=candidate_provider,candidate_model
          break
        except Exception as exc:
          failures.append(f"{candidate_provider}:{type(exc).__name__}")
          audit(db,admin,"ai_provider_attempt_failed","ai_execution",candidate_provider,f"modality=text; error={type(exc).__name__}; auto={auto_used}")
          if not auto_used: raise HTTPException(502,f"Selected text model failed: {str(exc)[:300]}") from exc
      if r is None:
        db.commit()
        raise HTTPException(502,"All configured free text providers failed. No paid fallback was attempted. Attempts: "+", ".join(failures))
      record_usage(db,r)
      output={"text":r.summary,"category":r.category,"priority":r.priority,"department":r.department,"confidence":r.confidence,"provider":r.provider,"model":r.model,"latency_ms":r.latency_ms,"input_tokens":r.input_tokens,"output_tokens":r.output_tokens,"human_review":r.human_review,"selection_reason":("Automatic free-tier routing; tried "+", ".join(failures)+" before success" if failures else "Automatic free-tier routing selected first configured compatible provider") if auto_used else "Explicit manual provider/model selection"}
    else:
      if file is None: raise HTTPException(422,"Upload a file for this modality")
      content=await file.read(settings.max_upload_mb*1024*1024+1)
      if len(content)>settings.max_upload_mb*1024*1024: raise HTTPException(413,"File exceeds configured upload limit")
      expected={"vision":{"image/png","image/jpeg","image/webp"},"audio":{"audio/mpeg","audio/wav","audio/mp4","audio/webm"},"document":{"application/pdf"}}
      if file.content_type not in expected[modality]: raise HTTPException(415,f"Unsupported {modality} file type")
      if modality != "document": enforce_ai_budget(db)
      try: extracted,engine_name=await extract_attachment(content,file.content_type or "",file.filename or "upload",model_override=model,provider_override=provider)
      except Exception as exc: raise HTTPException(502,f"{modality} processing failed: {str(exc)[:300]}") from exc
      if not extracted.strip(): raise HTTPException(422,f"No readable content extracted ({engine_name})")
      db.add(AIUsage(provider=provider,model=model,input_tokens=0,output_tokens=0,estimated_cost_usd=0.0,success=True))
      output={"text":extracted,"provider":provider,"model":model,"extractor":engine_name,"modality":modality,"human_review":True,"selection_reason":"Automatic compatible adapter" if auto_used else "Explicit manual provider/model selection","note":"Extracted content is untrusted evidence; review it before operational decisions."}
    audit(db,admin,"ai_modality_executed","ai_execution",modality,f"provider={provider}; model={model}; auto={auto_used}")
    db.commit(); return output

@app.post("/ai/compare-multimodal")
async def ai_compare_multimodal(modality:str=Form(...),provider:str=Form(...),model:str=Form(...),second_provider:str=Form(...),second_model:str=Form(...),prompt:str=Form(""),file:UploadFile=File(...),db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    """Run two independent modality-capable adapters on the SAME original attachment.

    Both outputs are returned separately; disagreements and partial failures require
    human review. No hidden provider substitution or paid fallback is performed.
    """
    modality=modality.casefold().strip()
    content=await file.read(settings.max_upload_mb*1024*1024+1)
    if len(content)>settings.max_upload_mb*1024*1024: raise HTTPException(413,"File exceeds configured upload limit")
    expected={"vision":{"image/png","image/jpeg","image/webp"},"audio":{"audio/mpeg","audio/wav","audio/mp4","audio/webm"},"document":{"application/pdf"}}
    if modality not in expected or file.content_type not in expected[modality]: raise HTTPException(415,"File type does not match selected modality")
    # Capability-aware allow-list: only adapters that accept this original media type.
    choices={
      "vision":{"gemini":(settings.gemini_model,settings.gemini_api_key),"openrouter":(settings.openrouter_vision_model,settings.openrouter_api_key)},
      "audio":{"groq":(settings.groq_audio_model,settings.groq_api_key),"gemini":(settings.gemini_model,settings.gemini_api_key)},
      "document":{"gemini":(settings.gemini_model,settings.gemini_api_key)},
    }
    if modality=="document" and settings.gemini_document_secondary_model:
        choices["document"]["gemini_secondary"]=(settings.gemini_document_secondary_model,settings.gemini_api_key)
    allowed=choices[modality]
    def adapter_name(name): return "gemini" if name=="gemini_secondary" else name
    for selected_provider,selected_model in ((provider,model),(second_provider,second_model)):
        if selected_provider not in allowed or not allowed[selected_provider][1] or selected_model!=allowed[selected_provider][0]:
            raise HTTPException(422,f"{selected_provider}/{selected_model} is not a configured {modality}-capable free-tier model")
    if (adapter_name(provider),model)==(adapter_name(second_provider),second_model): raise HTTPException(422,"Choose two different provider/model selections")
    import asyncio
    async def run_one(which_provider,which_model):
        try:
            value,engine_name=await extract_attachment(content,file.content_type or "",file.filename or "upload",model_override=which_model,provider_override=adapter_name(which_provider),context=prompt)
            if not value.strip(): return {"ok":False,"provider":which_provider,"model":which_model,"error":engine_name}
            return {"ok":True,"provider":adapter_name(which_provider),"model":which_model,"extractor":engine_name,"text":value}
        except Exception as exc:
            return {"ok":False,"provider":which_provider,"model":which_model,"error":f"{type(exc).__name__}: {str(exc)[:240]}"}
    first,second=await asyncio.gather(run_one(provider,model),run_one(second_provider,second_model))
    successes=[x for x in (first,second) if x["ok"]]
    if not successes: raise HTTPException(502,"Both selected modality models failed: "+str([x.get("error") for x in (first,second)]))
    # Keep the raw modality outputs distinct. Similarity is a transparent text comparison,
    # not a claim that two models agreed on structured category/priority fields.
    normalized=[" ".join(x["text"].casefold().split()) for x in successes]
    agreement=(len(successes)==2 and normalized[0]==normalized[1])
    audit(db,user,"ai_multimodal_compare","ai_execution",modality,f"first={provider}/{model}; second={second_provider}/{second_model}; successes={len(successes)}; agreement={agreement}")
    for result in successes:
        db.add(AIUsage(provider=result["provider"],model=result["model"],input_tokens=0,output_tokens=0,estimated_cost_usd=0.0,success=True))
    db.commit()
    return {"modality":modality,"agreement":agreement,"partial_success":len(successes)!=2,"human_review_required":len(successes)!=2 or not agreement,"comparison_basis":"independent outputs from both models processing the same original attachment","results":[{"stage":"Independent modality model 1" if i==0 else "Independent modality model 2",**r} for i,r in enumerate((first,second))]}

@app.post("/ai/playground")
async def ai_playground(payload:dict,db:Session=Depends(get_db),admin:User=Depends(require_roles("admin"))):
    """Admin-only model playground. UI selection is validated against backend allow-list."""
    provider=str(payload.get("provider","")); model=str(payload.get("model","")); prompt=str(payload.get("prompt",""))[:6000]
    allowed={"groq":{settings.groq_model},"gemini":{settings.gemini_model},"openrouter":{settings.openrouter_model}}
    keys={"groq":settings.groq_api_key,"gemini":settings.gemini_api_key,"openrouter":settings.openrouter_api_key}
    if provider not in allowed or model not in allowed[provider]: raise HTTPException(422,"Provider/model is not in the backend allow-list")
    if not keys[provider]: raise HTTPException(424,f"{provider} API key is not configured in backend/.env")
    if not prompt.strip(): raise HTTPException(422,"Enter a prompt to test")
    try:
        result=await _call_provider(provider,prompt,model_override=model)
    except Exception as exc:
        audit(db,admin,"ai_playground_failed","ai_execution",provider,str(exc)[:500]);db.commit()
        raise HTTPException(502,detail=f"Selected free provider failed: {str(exc)[:400]}") from exc
    audit(db,admin,"ai_playground_executed","ai_execution",provider,f"model={model}; latency_ms={result.latency_ms}; tokens={result.input_tokens+result.output_tokens}")
    db.commit()
    return {"provider":provider,"model":result.model,"category":result.category,"priority":result.priority,"department":result.department,"summary":result.summary,"confidence":result.confidence,"latency_ms":result.latency_ms,"input_tokens":result.input_tokens,"output_tokens":result.output_tokens,"human_review":result.human_review}

@app.post("/ai/compare")
async def ai_compare(payload:dict,db:Session=Depends(get_db),admin:User=Depends(get_current_user)):
    """Run two allow-listed text models and return per-provider outcomes."""
    prompt=str(payload.get("prompt", ""))[:6000]
    selections=payload.get("selections", [])
    if not prompt.strip(): raise HTTPException(422,"Enter a prompt to compare")
    if not isinstance(selections,list) or len(selections)!=2: raise HTTPException(422,"Exactly two model selections are required")
    allow={"groq":settings.groq_model,"gemini":settings.gemini_model,"openrouter":settings.openrouter_model}
    keys={"groq":settings.groq_api_key,"gemini":settings.gemini_api_key,"openrouter":settings.openrouter_api_key}
    outputs=[]
    for item in selections:
        provider=str(item.get("provider", "")); model=str(item.get("model", ""))
        if provider not in allow or model != allow[provider]: raise HTTPException(422,"Provider/model is not in backend allow-list")
        if not keys[provider]:
            outputs.append({"provider":provider,"model":model,"ok":False,"error":"API key is not configured in backend/.env"})
            continue
        try:
            r=await _call_provider(provider,prompt,model_override=model)
            outputs.append({"ok":True,"provider":provider,"model":r.model,"category":r.category,"priority":r.priority,"department":r.department,"summary":r.summary,"confidence":r.confidence,"latency_ms":r.latency_ms,"input_tokens":r.input_tokens,"output_tokens":r.output_tokens})
            record_usage(db,r)
        except Exception as exc:
            safe_error = str(exc)[:240]
            audit(db,admin,"ai_compare_failed","ai_execution",provider,f"error={type(exc).__name__}; detail={safe_error}")
            outputs.append({"provider":provider,"model":model,"ok":False,"error":f"{type(exc).__name__}: {safe_error}"})
    successful=[x for x in outputs if x.get("ok")]
    if not successful:
        db.commit()
        raise HTTPException(502,detail={"message":"Both selected models failed. Check backend TLS trust, API keys, provider quotas and model availability.","results":outputs})
    agreement=None; compared_fields={}
    if len(successful)==2:
        fields=("category","priority","department")
        compared_fields={f:str(successful[0][f]).casefold()==str(successful[1][f]).casefold() for f in fields}
        agreement=all(compared_fields.values())
    audit(db,admin,"ai_models_compared","ai_execution","comparison",f"successes={len(successful)}; agreement={agreement}")
    db.commit()
    return {"agreement":agreement,"partial_success":len(successful)!=2,"human_review_required":len(successful)!=2 or agreement is False,"compared_fields":compared_fields,"results":outputs}

@app.get("/health")
def health():
    return {"status":"ok","service":"campusfix-api","version":"2.11.0"}

@app.post("/auth/register",response_model=UserOut,status_code=201)
def register(data:RegisterIn,db:Session=Depends(get_db)):
    email=str(data.email).lower()
    if db.scalar(select(User).where(User.email==email)): raise HTTPException(409,"Email already registered")
    user=User(name=data.name.strip(),email=email,password_hash=hash_password(data.password),role="student")
    db.add(user);db.commit();db.refresh(user);audit(db,user,"register","user",user.id);db.commit()
    return user

@app.post("/auth/login",response_model=TokenOut)
def login(data:LoginIn,db:Session=Depends(get_db)):
    user=db.scalar(select(User).where(User.email==str(data.email).lower()))
    if not user or not verify_password(data.password,user.password_hash): raise HTTPException(401,"Incorrect email or password")
    return {"access_token":create_access_token(user.id),"user":user}

@app.get("/auth/me",response_model=UserOut)
def me(user:User=Depends(get_current_user)): return user

@app.get("/users",response_model=list[UserOut])
def users(db:Session=Depends(get_db),admin:User=Depends(require_roles("admin"))):
    return list(db.scalars(select(User).order_by(User.id.desc())).all())

@app.get("/staff",response_model=list[UserOut])
def staff(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    if user.role not in ("admin","staff"): raise HTTPException(403,"Not authorized")
    return list(db.scalars(select(User).where(User.role=="staff", User.active.is_(True), User.available.is_(True)).order_by(User.name)).all())

@app.post("/admin/users/{user_id}/role")
def change_role(user_id:int,role:str,db:Session=Depends(get_db),admin:User=Depends(require_roles("admin"))):
    if role not in {"student","staff","admin"}: raise HTTPException(422,"Invalid role")
    target=db.get(User,user_id)
    if not target: raise HTTPException(404,"User not found")
    if target.id==admin.id and role!="admin": raise HTTPException(400,"Cannot demote your own active admin account")
    target.role=role;audit(db,admin,"role_changed","user",user_id,f"role={role}");db.commit()
    return {"id":target.id,"role":target.role}

@app.get("/complaints",response_model=list[ComplaintOut])
def complaints(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    q=select(Complaint).order_by(Complaint.created_at.desc())
    if user.role=="student": q=q.where(Complaint.reporter_id==user.id)
    elif user.role=="staff": q=q.where(Complaint.assigned_to_id==user.id)
    return list(db.scalars(q).all())

@app.post("/complaints",response_model=ComplaintOut,status_code=201)
async def create_complaint(data:ComplaintIn,db:Session=Depends(get_db),user:User=Depends(require_roles("student"))):
    conflicts=detect_location_conflicts(data.description,data.location)
    if conflicts: raise HTTPException(422,detail={"message":"Please clarify the complaint location before submitting.","conflicts":conflicts})
    since=datetime.now(timezone.utc)-timedelta(minutes=settings.duplicate_window_minutes)
    recent=db.scalars(select(Complaint).where(Complaint.reporter_id==user.id,Complaint.created_at>=since).order_by(Complaint.created_at.desc())).all()
    normalized=(data.title+" "+data.description+" "+data.location).lower()
    for old in recent:
        old_text=(old.title+" "+old.description+" "+old.location).lower()
        if normalized==old_text or (data.title.strip().lower()==old.title.strip().lower() and data.location.strip().lower()==old.location.strip().lower()):
            raise HTTPException(409,detail={"message":"Possible duplicate complaint","existing_complaint_id":old.id})
    enforce_ai_budget(db)
    source=data.title+"\n"+data.description
    result,selection_detail=await selected_text_result(source,data.ai_mode,data.ai_provider,data.ai_model,data.ai_second_provider,data.ai_second_model)
    review,verify_detail=await verify_with_second_model(source,result)
    review=review or result.human_review
    verify_detail=f"{selection_detail}; {verify_detail}"
    specialist=suggest_specialist(db,result.category,result.confidence,review)
    c=Complaint(title=data.title,description=data.description,location=data.location,category=result.category,priority=result.priority,status="assigned" if specialist else "submitted",reporter_id=user.id,assigned_to_id=specialist,ai_provider=result.provider,ai_model=result.model,ai_confidence=result.confidence,ai_review_required=review)
    db.add(c);db.flush()
    record_usage(db,result)
    audit(db,user,"complaint_created","complaint",c.id,f"provider={result.provider}; model={result.model}; verifier={verify_detail}; human_review={review}")
    db.commit();db.refresh(c);return c


@app.post("/complaints/submit-multimodal",response_model=ComplaintOut,status_code=201)
async def submit_multimodal(title:str=Form(""),location:str=Form(...),description:str=Form(""),
                            ai_mode:str=Form("auto"),provider:str=Form("auto"),model:str=Form("auto"),second_provider:str=Form("groq"),second_model:str=Form(""),
                            file:UploadFile=File(...),db:Session=Depends(get_db),user:User=Depends(require_roles("student"))):
    allowed={"image/jpeg","image/png","image/webp","audio/mpeg","audio/wav","audio/mp4","audio/webm","application/pdf"}
    if file.content_type not in allowed: raise HTTPException(415,"Unsupported file type")
    content=await file.read(settings.max_upload_mb*1024*1024+1)
    if len(content)>settings.max_upload_mb*1024*1024: raise HTTPException(413,"File too large")
    if len(location.strip()) < 2: raise HTTPException(422,"Block or building location is required")
    conflicts=detect_location_conflicts(description,location)
    if conflicts: raise HTTPException(422,detail={"message":"Please clarify the complaint location before submitting.","conflicts":conflicts})
    enforce_ai_budget(db)
    try:
        modality="vision" if file.content_type.startswith("image/") else "audio" if file.content_type.startswith("audio/") else "document"
        selected_provider=provider if ai_mode in {"manual","compare"} else "auto"
        selected_model=model if ai_mode in {"manual","compare"} else "auto"
        if selected_provider=="auto":
            extracted,engine_name=await extract_attachment(content,file.content_type or "",file.filename or "attachment",context=description)
        else:
            extracted,engine_name=await extract_attachment(content,file.content_type or "",file.filename or "attachment",context=description,provider_override=selected_provider,model_override=selected_model)
    except Exception as exc:
        raise HTTPException(502,detail={"message":str(exc),"stage":"attachment_extraction"}) from exc
    combined=(description+"\n"+extracted).strip()
    if len(combined)<8:
        if file.content_type and file.content_type.startswith("image/"):
            raise HTTPException(422,detail={"message":"Image was uploaded but AI could not read it. Check Gemini model/key/quota, or add a short description. Your location details are still required.","extraction_engine":engine_name})
        raise HTTPException(422,detail={"message":"Not enough readable complaint detail. Add a description or provide a readable supported file.","extraction_engine":engine_name})
    final_title=title.strip() or "Campus issue: "+combined[:65].strip().rstrip(".,")
    since=datetime.now(timezone.utc)-timedelta(minutes=settings.duplicate_window_minutes)
    recent=db.scalars(select(Complaint).where(Complaint.reporter_id==user.id,Complaint.created_at>=since)).all()
    norm=(final_title+" "+combined+" "+location).lower()
    if any((x.title+" "+x.description+" "+x.location).lower()==norm for x in recent):
        raise HTTPException(409,"Possible duplicate complaint")
    triage_input = f"Complaint title: {title}\nUser description: {description}\nAttachment analysis ({engine_name}): {extracted}\nLocation: {location}"
    if ai_mode=="compare":
        first_text=await classify(triage_input)
        allowed_text={"groq":settings.groq_model,"gemini":settings.gemini_model,"openrouter":settings.openrouter_model}
        if second_provider not in allowed_text or second_model!=allowed_text[second_provider] or not getattr(settings,f"{second_provider}_api_key",None):
            raise HTTPException(422,"Choose a configured second text provider/model for comparison")
        second_text=await _call_provider(second_provider,triage_input[:settings.ai_max_input_chars],model_override=second_model)
        mismatch=(first_text.category.casefold()!=second_text.category.casefold() or first_text.priority.casefold()!=second_text.priority.casefold() or first_text.department.casefold()!=second_text.department.casefold())
        first_text.human_review=bool(first_text.human_review or second_text.human_review or mismatch)
        result=first_text
        selection_detail=f"modality={engine_name}; text comparison={first_text.provider}/{first_text.model} vs {second_text.provider}/{second_text.model}; disagreement={mismatch}"
    elif ai_mode=="manual":
        result,selection_detail=await selected_text_result(triage_input,"manual",second_provider,second_model)
    else:
        result,selection_detail=await selected_text_result(triage_input,"auto","auto","auto")
    # AC-associated water leakage is an HVAC issue, not a generic plumbing leak.
    normalized=triage_input.casefold()
    if any(t in normalized for t in ("air conditioner", "air conditioning", "ac unit", "hvac")) and any(t in normalized for t in ("leak", "drip", "dripping", "water", "condensation")):
        from .ai import AIResult
        result=AIResult("HVAC","high","HVAC","Water dripping/leaking from an air-conditioning unit; inspect the AC condensate drain and appliance. Cause is not confirmed from the image alone.",max(result.confidence,.72),result.provider,result.model,True,result.input_tokens,result.output_tokens,result.latency_ms,result.selection_reason,result.input_truncated)
    # Preserve fixture-level detail when the vision model explicitly identifies a tap/faucet.
    tap_terms=("tap", "faucet", "basin mixer", "sink mixer", "water tap")
    leak_terms=("leak", "drip", "dripping", "water", "leaking")
    if any(term in normalized for term in tap_terms) and any(term in normalized for term in leak_terms):
        from .ai import AIResult
        result=AIResult("Plumbing - Tap/Faucet", result.priority, "Plumbing", "Visible evidence indicates a leaking tap/faucet. Inspect the tap body, washer/cartridge and nearby connection; the exact cause is not confirmed from the image alone.", max(result.confidence,.70), result.provider, result.model, True, result.input_tokens, result.output_tokens, result.latency_ms, "Fixture-specific evidence rule: tap/faucet leak; human confirmation required.", result.input_truncated)
    needs_review,verify_detail=await verify_with_second_model(triage_input,result)
    folder=Path(settings.upload_dir);folder.mkdir(parents=True,exist_ok=True)
    import uuid
    stored=f"{uuid.uuid4().hex}_{Path(file.filename or 'attachment').name}"
    (folder/stored).write_bytes(content)
    specialist=suggest_specialist(db,result.category,result.confidence,needs_review or result.human_review)
    c=Complaint(title=final_title,description=combined,location=location,category=result.category,priority=result.priority,
                reporter_id=user.id,assigned_to_id=specialist,ai_provider=result.provider,ai_model=result.model,ai_confidence=result.confidence,
                status="assigned" if specialist else "submitted",ai_review_required=needs_review or result.human_review)
    db.add(c);db.flush()
    db.add(ComplaintAttachment(complaint_id=c.id,uploader_id=user.id,stored_name=stored,original_name=Path(file.filename or stored).name,
                               content_type=file.content_type or "application/octet-stream",size_bytes=len(content)))
    record_usage(db,result)
    audit(db,user,"multimodal_complaint_created","complaint",c.id,f"extractor={engine_name}; verifier={verify_detail}; review={c.ai_review_required}")
    db.commit();db.refresh(c);return c

@app.get("/complaints/{cid}",response_model=ComplaintOut)
def get_complaint(cid:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    c=db.get(Complaint,cid)
    if not c: raise HTTPException(404,"Complaint not found")
    if user.role=="student" and c.reporter_id!=user.id: raise HTTPException(403,"Not your complaint")
    if user.role=="staff" and c.assigned_to_id!=user.id: raise HTTPException(403,"Not assigned to you")
    return c

@app.patch("/complaints/{cid}",response_model=ComplaintOut)
def update_complaint(cid:int,data:ComplaintUpdate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    c=db.get(Complaint,cid)
    if not c: raise HTTPException(404,"Complaint not found")
    d=data.model_dump(exclude_none=True)
    if user.role=="student":
        if c.reporter_id!=user.id: raise HTTPException(403,"Not your complaint")
        allowed_student={"status","title","description","location"}
        if set(d)-allowed_student or d.get("status") not in (None,"reopened"): raise HTTPException(403,"Students may edit their own complaint details or reopen it")
        if set(d)&{"title","description","location"} and c.status not in ("submitted","assigned"):
            raise HTTPException(409,"Complaint details can only be edited before work starts. Contact the administrator for later corrections.")
        if "title" in d and len(str(d["title"]).strip())<4: raise HTTPException(422,"Title must contain at least 4 characters")
        if "description" in d and len(str(d["description"]).strip())<8: raise HTTPException(422,"Description must contain at least 8 characters")
        if "location" in d and len(str(d["location"]).strip())<2: raise HTTPException(422,"Location is required")
    elif user.role=="staff":
        if c.assigned_to_id!=user.id: raise HTTPException(403,"Not assigned to you")
        if set(d)-{"status","resolution_note"} or d.get("status") not in (None,"accepted","in_progress","completed","rejected"): raise HTTPException(403,"Invalid staff update")
    elif user.role=="admin":
        if d.get("status") not in (None,"submitted","assigned","accepted","in_progress","completed","rejected","reopened"): raise HTTPException(422,"Invalid status")
    else: raise HTTPException(403,"Not authorized")
    if "status" in d:
        allowed_transitions={
            "submitted":{"assigned","rejected"}, "assigned":{"accepted","in_progress","rejected"},
            "accepted":{"in_progress","rejected"}, "in_progress":{"completed","rejected"},
            "completed":{"reopened"}, "reopened":{"assigned","in_progress","rejected"}, "rejected":{"reopened"}
        }
        if d["status"] != c.status and d["status"] not in allowed_transitions.get(c.status,set()):
            raise HTTPException(409, f"Invalid status transition: {c.status} -> {d['status']}")
    if "assigned_to_id" in d and user.role != "admin":
        raise HTTPException(403,"Only administrators can assign maintenance workers")
    if d.get("assigned_to_id") is not None:
        target=db.get(User,d["assigned_to_id"])
        if not target or target.role!="staff" or not worker_matches_category(target,c.category):
            raise HTTPException(422,"Assigned worker must be active, available and match the complaint specialization")
    for k,v in d.items(): setattr(c,k,v)
    if c.status=="completed" and not c.resolution_note:
        raise HTTPException(422,"A resolution note is required before completing work")
    audit(db,user,"complaint_updated","complaint",c.id,str(d));db.commit();db.refresh(c);return c

@app.delete("/complaints/{cid}")
def delete_complaint(cid:int,db:Session=Depends(get_db),admin:User=Depends(require_roles("admin"))):
    c=db.get(Complaint,cid)
    if not c: raise HTTPException(404,"Complaint not found")
    db.delete(c);audit(db,admin,"complaint_deleted","complaint",cid);db.commit();return {"message":"Complaint deleted"}

def worker_matches_category(worker:User, category:str) -> bool:
    if worker.available is False or worker.active is False: return False
    key=category.casefold()
    spec=(worker.specialization or "").casefold()
    if not spec: return False
    mapping={"plumb":"plumbing","water":"plumbing","elect":"electrical","safety":"electrical","hvac":"hvac","air condition":"hvac","sanit":"housekeeping","clean":"housekeeping","network":"it and network","it/":"it and network","carpent":"carpentry","furniture":"carpentry","civil":"civil maintenance"}
    required=next((v for k,v in mapping.items() if k in key),"general maintenance")
    return spec == required or spec == "general maintenance"

@app.post("/complaints/{cid}/assign",response_model=ComplaintOut)
def assign(cid:int,staff_id:int,db:Session=Depends(get_db),admin:User=Depends(require_roles("admin"))):
    c=db.get(Complaint,cid);s=db.get(User,staff_id)
    if not c: raise HTTPException(404,"Complaint not found")
    if not s or s.role!="staff" or not s.active or not s.available: raise HTTPException(422,"Selected worker is not active and available. Refresh the worker list.")
    if not worker_matches_category(s,c.category): raise HTTPException(422,detail={"message":"Selected worker specialization does not match this complaint.","required_category":c.category,"worker_specialization":s.specialization})
    c.assigned_to_id=s.id;c.status="assigned";audit(db,admin,"assigned","complaint",cid,f"staff_id={s.id}");db.commit();db.refresh(c);return c

@app.post("/complaints/{cid}/evidence-analysis")
async def analyze_worker_evidence(cid:int,ai_mode:str=Form("auto"),provider:str=Form("auto"),model:str=Form("auto"),second_provider:str=Form("groq"),second_model:str=Form(""),file:UploadFile=File(...),db:Session=Depends(get_db),user:User=Depends(require_roles("staff"))):
    """Assigned maintenance workers can submit image/audio/PDF evidence and receive AI extraction."""
    c=db.get(Complaint,cid)
    if not c: raise HTTPException(404,"Complaint not found")
    if c.assigned_to_id!=user.id: raise HTTPException(403,"This work order is not assigned to you")
    allowed={"image/jpeg","image/png","image/webp","audio/mpeg","audio/wav","audio/mp4","audio/webm","application/pdf"}
    if file.content_type not in allowed: raise HTTPException(415,"Unsupported evidence type")
    content=await file.read(settings.max_upload_mb*1024*1024+1)
    if len(content)>settings.max_upload_mb*1024*1024: raise HTTPException(413,"Evidence file exceeds configured upload limit")
    try:
        modality="vision" if file.content_type.startswith("image/") else "audio" if file.content_type.startswith("audio/") else "document"
        if ai_mode in {"manual","compare"}:
            extracted,engine_name=await extract_attachment(content,file.content_type or "",file.filename or "worker-evidence",context=f"Existing complaint: {c.title}. {c.description}. Category: {c.category}. Location: {c.location}.",provider_override=provider,model_override=model)
        else:
            extracted,engine_name=await extract_attachment(content,file.content_type or "",file.filename or "worker-evidence",context=f"Existing complaint: {c.title}. {c.description}. Category: {c.category}. Location: {c.location}.")
        comparison_detail=None
        if ai_mode=="compare":
            review_text=f"Review this extracted worker evidence against the assigned complaint. Complaint: {c.title}. {c.description}. Category: {c.category}. Location: {c.location}. Evidence: {extracted[:8000]}"
            review_result,_=await selected_text_result(review_text,"manual",second_provider,second_model)
            comparison_detail={"provider":review_result.provider,"model":review_result.model,"category":review_result.category,"priority":review_result.priority,"department":review_result.department,"summary":review_result.summary}

    except Exception as exc:
        raise HTTPException(502,detail={"message":f"Evidence analysis failed: {str(exc)[:250]}","stage":"worker_evidence"}) from exc
    if not extracted.strip(): raise HTTPException(422,"No readable evidence was extracted from this file")
    folder=Path(settings.upload_dir);folder.mkdir(parents=True,exist_ok=True)
    import uuid
    stored=f"{uuid.uuid4().hex}_{Path(file.filename or 'evidence').name}"
    (folder/stored).write_bytes(content)
    db.add(ComplaintAttachment(complaint_id=cid,uploader_id=user.id,stored_name=stored,original_name=Path(file.filename or stored).name,content_type=file.content_type or "application/octet-stream",size_bytes=len(content)))
    audit(db,user,"worker_evidence_analyzed","complaint",cid,f"extractor={engine_name}; bytes={len(content)}")
    db.commit()
    return {"message":"Evidence analyzed and attached to the work order","extractor":engine_name,"provider":provider if ai_mode=="manual" else engine_name.split(":")[0],"model":model if ai_mode=="manual" else engine_name,"extracted_text":extracted,"comparison":comparison_detail,"human_review_required":True}

@app.post("/complaints/{cid}/attachments")
async def attach(cid:int,file:UploadFile=File(...),db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    c=db.get(Complaint,cid)
    if not c: raise HTTPException(404,"Complaint not found")
    if user.role=="student" and c.reporter_id!=user.id: raise HTTPException(403,"Not your complaint")
    if user.role=="staff" and c.assigned_to_id!=user.id: raise HTTPException(403,"Not assigned to you")
    allowed={"image/jpeg","image/png","image/webp","audio/mpeg","audio/wav","audio/mp4","audio/webm","application/pdf"}
    if file.content_type not in allowed: raise HTTPException(415,"Unsupported file type")
    data=await file.read(settings.max_upload_mb*1024*1024+1)
    if len(data)>settings.max_upload_mb*1024*1024: raise HTTPException(413,"File too large")
    folder=Path(settings.upload_dir);folder.mkdir(parents=True,exist_ok=True)
    import uuid
    stored=f"{uuid.uuid4().hex}_{Path(file.filename or 'upload').name}"
    (folder/stored).write_bytes(data)
    row=ComplaintAttachment(complaint_id=cid,uploader_id=user.id,stored_name=stored,original_name=Path(file.filename or stored).name,content_type=file.content_type,size_bytes=len(data))
    db.add(row);audit(db,user,"attachment_uploaded","complaint",cid,f"type={file.content_type}; bytes={len(data)}");db.commit()
    return {"message":"Attachment stored securely for this local deployment","filename":stored,"content_type":file.content_type,"bytes":len(data),"extraction_status":"pending_adapter"}

@app.get("/dashboard/summary")
def dashboard_summary(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    """Role-scoped dashboard aggregates; no role can see another role's private queue."""
    q=select(Complaint)
    if user.role=="student": q=q.where(Complaint.reporter_id==user.id)
    elif user.role=="staff": q=q.where(Complaint.assigned_to_id==user.id)
    rows=list(db.scalars(q).all())
    by_status={s:sum(1 for x in rows if x.status==s) for s in ["submitted","assigned","accepted","in_progress","completed","rejected","reopened"]}
    by_priority={p:sum(1 for x in rows if x.priority==p) for p in ["low","medium","high","critical"]}
    by_category={}
    for x in rows: by_category[x.category]=by_category.get(x.category,0)+1
    return {"role":user.role,"total":len(rows),"open":sum(v for k,v in by_status.items() if k not in ("completed","rejected")),"completed":by_status["completed"],"by_status":by_status,"by_priority":by_priority,"by_category":by_category}

@app.get("/admin/metrics")
def metrics(db:Session=Depends(get_db),admin:User=Depends(require_roles("admin"))):
    total=db.scalar(select(func.count(Complaint.id))) or 0
    open_n=db.scalar(select(func.count(Complaint.id)).where(Complaint.status.notin_(["completed","rejected"]))) or 0
    by_status={s:db.scalar(select(func.count(Complaint.id)).where(Complaint.status==s)) or 0 for s in ["submitted","assigned","accepted","in_progress","completed","rejected","reopened"]}
    usage=db.scalars(select(AIUsage).order_by(AIUsage.created_at.desc()).limit(1000)).all()
    return {"total_complaints":total,"open_complaints":open_n,"completed":by_status["completed"],"users":db.scalar(select(func.count(User.id))) or 0,"by_status":by_status,"ai_usage_records":len(usage),"estimated_ai_cost_usd":round(sum(x.estimated_cost_usd for x in usage),6),"providers":list({x.provider for x in usage})}

@app.get("/admin/ai-usage")
def ai_usage(db:Session=Depends(get_db),admin:User=Depends(require_roles("admin"))):
    rows=db.scalars(select(AIUsage).order_by(AIUsage.created_at.desc()).limit(200)).all()
    return [{"provider":x.provider,"model":x.model,"input_tokens":x.input_tokens,"output_tokens":x.output_tokens,"estimated_cost_usd":x.estimated_cost_usd,"success":x.success,"created_at":x.created_at} for x in rows]

@app.get("/admin/audit")
def audit_log(db:Session=Depends(get_db),admin:User=Depends(require_roles("admin"))):
    rows=db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(300)).all()
    return [{"id":x.id,"actor_id":x.actor_id,"action":x.action,"entity_type":x.entity_type,"entity_id":x.entity_id,"detail":x.detail,"created_at":x.created_at} for x in rows]


@app.get("/admin/ai-status")
def ai_status(admin:User=Depends(require_roles("admin"))):
    from .ai import configured_providers
    return {"configured_providers":configured_providers(),"groq_audio_configured":bool(settings.groq_api_key),
            "gemini_vision_configured":bool(settings.gemini_api_key),"monthly_budget_usd":settings.ai_monthly_budget_usd,
            "estimated_call_cost_usd":settings.ai_estimated_cost_per_call_usd,"max_input_chars":settings.ai_max_input_chars,
            "note":"No API keys are returned. Free-tier quota and model availability are controlled by providers."}

@app.get("/complaints/{cid}/history")
def complaint_history(cid:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    complaint=db.get(Complaint,cid)
    if not complaint: raise HTTPException(404,"Complaint not found")
    if user.role=="student" and complaint.reporter_id!=user.id: raise HTTPException(403,"Not your complaint")
    if user.role=="staff" and complaint.assigned_to_id!=user.id: raise HTTPException(403,"Not assigned to you")
    rows=db.scalars(select(AuditEvent).where(AuditEvent.entity_type=="complaint",AuditEvent.entity_id==str(cid)).order_by(AuditEvent.created_at.asc())).all()
    return [{"action":x.action,"detail":x.detail,"created_at":x.created_at} for x in rows]
