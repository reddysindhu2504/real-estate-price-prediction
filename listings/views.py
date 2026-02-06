# listings/views.py  — FINAL (dashboard + history + predictor integration)
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
#from django.contrib.auth.tokens import default_token_generator
#from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
#from django.utils.encoding import force_bytes, force_str
#from django.template.loader import render_to_string
#from django.core.mail import send_mail

from django.db.models import Avg, Count
from django.db.models.functions import TruncDate

from .models import LandQuery
from .land_predictor import predict_land_price

from .forms import PropertyForm
from .models import PropertyQuery, Realtor
from .predictor_construction_ann import predict_construction_cost

from .models import LoginHistory
from django.contrib.auth.decorators import login_required

import os
import joblib
import json
import traceback
import numpy as np

from django.db.models import Avg, Count
from django.db.models.functions import Coalesce

# ---------------------------
# PATHS
# ---------------------------
BASE_DIR = settings.BASE_DIR
PIPELINE_PATH = os.path.join(BASE_DIR, "model", "pipeline_full.joblib")
CLUSTERER_PATH = os.path.join(BASE_DIR, "model", "clusterer_kmeans.joblib")
METRICS_PATH = os.path.join(BASE_DIR, "model", "metrics.json")
CLUSTER_INFO_PATH = os.path.join(BASE_DIR, "model", "cluster_info.json")
LAND_DATASET_PATH = os.path.join(settings.BASE_DIR, "listings", "data", "up.csv")


pipeline = None
clusterer = None
model_rmse = None
cluster_info = {}

# ---------------------------
# LOAD MODEL ARTIFACTS
# ---------------------------
def load_artifacts():
    global pipeline, clusterer, model_rmse, cluster_info

    # pipeline
    try:
        if pipeline is None and os.path.exists(PIPELINE_PATH):
            pipeline = joblib.load(PIPELINE_PATH)
            print("Loaded pipeline:", PIPELINE_PATH)
    except Exception as e:
        print("Pipeline load failed:", e)
        pipeline = None

    # clusterer
    try:
        if clusterer is None and os.path.exists(CLUSTERER_PATH):
            clusterer = joblib.load(CLUSTERER_PATH)
            print("Loaded clusterer:", CLUSTERER_PATH)
    except Exception as e:
        print("Clusterer load failed:", e)
        clusterer = None

    # metrics
    try:
        if os.path.exists(METRICS_PATH):
            with open(METRICS_PATH, "r", encoding="utf-8") as f:
                m = json.load(f)
                # prefer rmse in INR if present, else log rmse
                model_rmse = m.get("rmse_inr") or m.get("rmse_log")
                # ensure numeric or None
                try:
                    model_rmse = float(model_rmse) if model_rmse is not None else None
                except:
                    model_rmse = None
    except Exception as e:
        print("Metrics load failed:", e)
        model_rmse = None

    # cluster_info
    try:
        if os.path.exists(CLUSTER_INFO_PATH):
            with open(CLUSTER_INFO_PATH, "r", encoding="utf-8") as f:
                cluster_info = json.load(f)
    except Exception as e:
        print("Cluster info load failed:", e)
        cluster_info = {}

# initial load
load_artifacts()

# ---------------------------
# HELPERS
# ---------------------------
def _to_float(x, default=0.0):
    try:
        if x is None or (isinstance(x, str) and x.strip() == ""):
            return float(default)
        return float(x)
    except:
        return float(default)

def _to_int(x, default=0):
    try:
        if x is None or (isinstance(x, str) and x.strip() == ""):
            return int(default)
        return int(float(x))
    except:
        return int(default)

# ---------------------------
# AUTH: signup / activation
# ---------------------------
def signup(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        if not email or not password:
            return render(request, "registration/signup.html", {
                "error": "Email and password required"
            })

        if User.objects.filter(username=email).exists():
            return render(request, "registration/signup.html", {
                "error": "Email already exists"
            })

        # ✅ Direct user creation (NO activation)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        
        return redirect("login")

    return render(request, "registration/signup.html")
# def signup(request):
#     if request.method == "POST":
#         email = request.POST.get("email", "").strip().lower()
#         password = request.POST.get("password", "")
#         if not email or not password:
#             return render(request, "registration/signup.html", {"error": "Email and password required."})
#         if User.objects.filter(username=email).exists():
#             return render(request, "registration/signup.html", {"error": "Email already exists."})

#         user = User.objects.create_user(username=email, email=email, password=password, is_active=False)
#         uid = urlsafe_base64_encode(force_bytes(user.pk))
#         token = default_token_generator.make_token(user)
#         activation_link = request.build_absolute_uri(f"/activate/{uid}/{token}/")

#         subject = "Activate Account"
#         message = render_to_string("registration/activation_email.txt", {"activation_link": activation_link, "user": user})
#         try:
#             send_mail(subject, message, None, [email])
#         except Exception:
#             print("send_mail error (ignored)")

#         return render(request, "registration/signup_done.html", {"email": email})
#     return render(request, "registration/signup.html")

# def activate(request, uidb64, token):
#     try:
#         uid = force_str(urlsafe_base64_decode(uidb64))
#         user = User.objects.get(pk=uid)
#     except Exception:
#         user = None
#     if user is not None and default_token_generator.check_token(user, token):
#         user.is_active = True
#         user.save()
#         login(request, user)
#         return redirect("choose")
#     return render(request, "registration/activation_invalid.html")

@login_required
def choose(request):
    return render(request, "listings/choose.html")


@login_required
def land_home(request):
    return render(request, "listings/land.html")

# ---------------------------
# HOME / PREDICTION
# ---------------------------
@login_required
def index(request):
    load_artifacts()
    form = PropertyForm(request.POST or None)

    result = None
    result_lakhs = None
    contacts = []
    saved_state = ""
    saved_district = ""

    if request.method == "POST":
        if form.is_valid():
            data = form.cleaned_data
            state = (data.get("state") or "").strip()
            district = (data.get("district") or "").strip()
            city = (data.get("city") or "").strip() or district
            locality = (data.get("locality") or "").strip() or district
            saved_state, saved_district = state, district

            size_sqft = _to_float(data.get("size_sqft"), 0.0)
            bedrooms = _to_int(data.get("bedrooms"), 0)
            bathrooms = _to_int(data.get("bathrooms"), 1)
            age = _to_int(data.get("age"), 0)

            predictor_input = {
                "state": state,
                "city": city,
                "locality": locality,
                "size_sqft": size_sqft,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "age": age,
                "bhk": bedrooms,
                "BHK": bedrooms
            }

            # call predictor (returns lakhs)
            try:
                price_lakhs =predict_construction_cost(predictor_input)
                if price_lakhs is not None:
                    result_lakhs = float(price_lakhs)
                    result = float(price_lakhs) * 100000.0
                else:
                    result = None
                    result_lakhs = None
            except Exception as e:
                print("Prediction error (views):", e)
                traceback.print_exc()
                messages.error(request, "Prediction failed.")

            # try to compute cluster (best-effort) if pipeline/clusterer present
            cluster_label = None
            try:
                preproc = None
                if pipeline is not None:
                    # safe access to named_steps
                    preproc = getattr(pipeline, "named_steps", {}).get("preprocessor") or None
                if preproc is None and pipeline is not None:
                    # fallback: try common names
                    for name in ("preprocessor","pre","transformer","prep"):
                        preproc = getattr(pipeline, "named_steps", {}).get(name)
                        if preproc is not None:
                            break
                if preproc is not None and clusterer is not None and result is not None:
                    # create a minimal dataframe for transform (pipeline expects particular feature names)
                    # we will not import pandas here to avoid overhead; use a simple 1-row dict if pipeline accepts it
                    # but many sklearn preprocessor.transform expects array or DataFrame — so skip cluster prediction if unsure
                    # keep as a best-effort no-fail block
                    try:
                        import pandas as _pd
                        X_for_cluster = _pd.DataFrame([{
                            "state": state,
                            "city": city,
                            "locality": locality,
                            "size_sqft": size_sqft,
                            "bedrooms": bedrooms,
                            "bathrooms": bathrooms,
                            "age": age
                        }])
                        Xp = preproc.transform(X_for_cluster)
                        cluster_label = int(clusterer.predict(Xp)[0])
                    except Exception:
                        cluster_label = None
            except Exception:
                cluster_label = None

            # Save query (ensure bathrooms default is present to avoid DB NOT NULL)
            if result is not None:
                try:
                    PropertyQuery.objects.create(
                        user=request.user,
                        state=state,
                        district=district or city,
                        location=locality,
                        size_sqft=size_sqft,
                        bedrooms=bedrooms,
                        bathrooms=bathrooms,
                        age=age,
                        amenities_score=data.get("amenities_score") or 0,
                        monthly_income=data.get("monthly_income"),
                        predicted_price=result,
                        cluster=cluster_label
                    )
                except Exception as e:
                    print("DB save failed:", e)
                    traceback.print_exc()
                    messages.warning(request, "Prediction saved failed.")

            # load contacts
            try:
                contacts = Realtor.objects.filter(
    state__iexact=state,
    district__iexact=district
)[:10]
            except Exception:
                contacts = []

            if result is not None:
                messages.success(request, "Prediction generated successfully.")
        else:
            messages.error(request, "Please correct the form errors.")

    return render(request, "listings/index.html", {
        "form": form,
        "result": result,
        "result_lakhs": result_lakhs,
        "contacts": contacts,
        "saved_state": saved_state,
        "saved_district": saved_district,
        "model_rmse": model_rmse,
        "cluster_info": cluster_info
    })




@login_required
#from django.contrib.auth.decorators import login_required

@login_required
def land_prediction(request):
    result = None

    if request.method == "POST":
        data = {
            "state": request.POST.get("state"),
            "city": request.POST.get("city"),
            "plot_type": request.POST.get("plot_type"),
            "Area": request.POST.get("Area"),
        }

        # 🔮 Predict land price
        result = predict_land_price(data)

        # 🔐 SAVE TO LAND HISTORY
        if result is not None and result > 0:
            try:
                LandQuery.objects.create(
                    user=request.user,  # ✅ logged-in user
                    state=(data.get("state") or "").strip(),
                    district=(data.get("city") or "").strip(),
                    land_area=float(data.get("Area")) if data.get("Area") else 0.0,
                    soil_type=(data.get("plot_type") or "Unknown"),
                    road_width=0.0,
                    land_shape="Residential",
                    predicted_price=float(result)
                )
                print("✅ Land history saved")

            except Exception as e:
                print("❌ Land history save failed:", e)

    return render(request, "listings/land.html", {
        "result": result
    })
# def land_prediction(request):
#     result = None

#     if request.method == "POST":
#         data = {
#             "state": request.POST.get("state"),
#             "city": request.POST.get("city"),
#             "plot_type": request.POST.get("plot_type"),
#             "Area": request.POST.get("Area"),
#         }

#         # 🔮 Predict land price
#         result = predict_land_price(data)

#         # 🔐 SAVE TO LAND HISTORY (only if prediction success)
#         if result is not None:
#             try:
#                 LandQuery.objects.create(
#                     user=request.user,
#                     state=data.get("state"),
#                     district=data.get("city"),          # city → district
#                     land_area=float(data.get("Area")), # safe float
#                     soil_type=data.get("plot_type"),   # reuse plot_type
#                     road_width=0.0,                     # default
#                     land_shape="Residential",           # default
#                     predicted_price=float(result)
#                 )
#             except Exception as e:
#                 print("❌ Land history save failed:", e)

#     return render(request, "listings/land.html", {
#         "result": result
#     })

# ---------------------------
# HISTORY
# ---------------------------
def history(request):
    qs = PropertyQuery.objects.all().order_by("-created_at")
    records = []
    for r in qs:
        try:
            lakhs = (float(r.predicted_price) / 100000.0) if r.predicted_price is not None else None
        except Exception:
            lakhs = None
        records.append({
            "location": r.location or r.district or r.state,
            "size_sqft": r.size_sqft,
            "bedrooms": r.bedrooms,
            "bathrooms": r.bathrooms,
            "predicted_price_inr": r.predicted_price,
            "predicted_price_lakhs": lakhs,
            "created_at": r.created_at
        })
    return render(request, "listings/history.html", {"records": records})

@login_required
# def land_history(request):
#     records = LandQuery.objects.filter(
#         user=request.user
#     ).order_by("-created_at")

#     return render(request, "listings/land_history.html", {
#         "records": records
#     })


@login_required
def land_history(request):
    records = LandQuery.objects.all().order_by("-created_at")

    return render(request, "listings/land_history.html", {
        "records": records
    })
# ---------------------------
# DASHBOARD (ORM-based aggregations)
# ---------------------------
@login_required
def dashboard(request):
    load_artifacts()

    qs = PropertyQuery.objects.all()
    total = qs.count()

    # average predicted price (INR)
    try:
        avg_price = qs.aggregate(avg=Coalesce(Avg("predicted_price"), 0.0))["avg"] or 0.0
    except Exception:
        avg_price = 0.0

    # avg_by_location: list of tuples (location, avg_inr)
    avg_by_location = []
    try:
        loc_qs = qs.values("location").annotate(avg_price=Coalesce(Avg("predicted_price"), 0.0)).order_by("-avg_price")
        avg_by_location = [(row["location"] or "Unknown", float(round(row["avg_price"], 2))) for row in loc_qs]
    except Exception as e:
        print("avg_by_location compute error:", e)
        avg_by_location = []

    # cluster_stats: list of dicts {cluster, cnt, avg_price}
    cluster_stats = []
    try:
        cluster_qs = qs.exclude(cluster__isnull=True).values("cluster").annotate(cnt=Count("id"), avg_price=Coalesce(Avg("predicted_price"), 0.0)).order_by("cluster")
        for row in cluster_qs:
            cluster_stats.append({
                "cluster": int(row["cluster"]),
                "cnt": int(row["cnt"]),
                "avg_price": float(round(row["avg_price"], 2))
            })
    except Exception as e:
        print("cluster_stats compute error:", e)
        cluster_stats = []

    return render(request, "listings/dashboard.html", {
        "total": total,
        "avg_price": float(round(avg_price, 2)),
        "avg_by_location": avg_by_location,
        "cluster_stats": cluster_stats,
        "cluster_pca_img": "listings/img/cluster_pca.png",
        "cluster_info": cluster_info
    })

@login_required
def land_dashboard(request):
    qs = LandQuery.objects.all()

    # ---------------------------
    # STATE-WISE AVERAGE PRICE
    # ---------------------------
    state_qs = (
        qs.values("state")
        .annotate(avg_price=Avg("predicted_price"))
        .order_by("state")
    )

    states = [x["state"] for x in state_qs]
    avg_prices = [round(x["avg_price"], 2) for x in state_qs]

    # ---------------------------
    # PLOT TYPE (soil_type) DISTRIBUTION
    # ---------------------------
    plot_qs = (
        qs.values("soil_type")
        .annotate(cnt=Count("id"))
        .order_by("soil_type")
    )

    plot_labels = [x["soil_type"] for x in plot_qs]
    plot_counts = [x["cnt"] for x in plot_qs]

    # ---------------------------
    # PREDICTION TREND (DATE-WISE)
    # ---------------------------
    trend_qs = (
        qs.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(avg_price=Avg("predicted_price"))
        .order_by("day")
    )

    trend_dates = [x["day"].strftime("%Y-%m-%d") for x in trend_qs]
    trend_prices = [round(x["avg_price"], 2) for x in trend_qs]

    context = {
        "states": json.dumps(states),
        "avg_prices": json.dumps(avg_prices),
        "plot_labels": json.dumps(plot_labels),
        "plot_counts": json.dumps(plot_counts),
        "trend_dates": json.dumps(trend_dates),
        "trend_prices": json.dumps(trend_prices),
    }
    return render(request, "listings/land_dashboard.html",context)
# ---------------------------
# STATIC PAGES
# ---------------------------
def about(request):
    return render(request, "listings/about.html")

def details(request):
    context = {
        "algorithm": "Regression pipeline",
        "framework": "Django + scikit-learn",
        "features": ["state", "city", "locality", "size_sqft", "bedrooms", "bathrooms", "age"],
        "output": "Predicted price (₹)"
    }
    return render(request, "listings/details.html", context)
@login_required
def land_details(request):
    context = {
        "algorithm": "Artificial Neural Network (ANN)",
        "model_type": "Deep Learning Regression",
        "features": [
            "State",
            "City",
            "Plot Type",
            "Land Area (sq.ft)"
        ],
        "output": "Predicted Land Price (₹)",
        "dataset": "Historical land price dataset (up.csv)"
    }
    return render(request, "listings/land_details.html", context)
def logout_view(request):
    logout(request)
    return redirect("login")

def landing(request):
    if request.user.is_authenticated:
        return redirect('choose')
    return render(request, "listings/landing.html")

# def auth_landing(request):
#     return render(request, "listings/auth_landing.html")



@login_required
def login_history(request):
    records = LoginHistory.objects.filter(user=request.user).order_by('-login_time')
    return render(request, "listings/login_history.html", {
        "records": records
    })

