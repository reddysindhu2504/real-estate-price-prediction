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


@login_required
def choose(request):
    return render(request, "listings/choose.html")


@login_required
def land_home(request):
    return render(request, "listings/land.html")


@login_required
def index(request):
    result = None
    contacts = []

    if request.method == "POST":
        data = {
            "state": request.POST.get("state"),
            "city": request.POST.get("district"),
            "size_sqft": request.POST.get("size_sqft"),
            "bhk": request.POST.get("bedrooms"),
            "age": request.POST.get("age"),
        }

        # 🔮 Predict construction price
        result = predict_construction_cost(data)
        print("PREDICTED PRICE:", result)

        state = (data.get("state") or "").strip()
        district = (data.get("city") or "").strip()

        # 🔐 SAVE TO HISTORY
        if result is not None:
            try:
                PropertyQuery.objects.create(
                user=request.user,
                state=state,
                district=district,
                location=district,
                size_sqft=float(data.get("size_sqft") or 0),
                bedrooms=int(data.get("bhk") or 0),
                bathrooms=int(request.POST.get("bathrooms") or 0),
                age=int(data.get("age") or 0),
                predicted_price=float(result)
                )
                print("✅ Construction history saved")

            except Exception as e:
                print("❌ Construction history save failed:", e)
        else:
            print("result is None")

        # 🏢 LOAD CONTACTS
        if state and district:
            contacts = Realtor.objects.filter(
                state__iexact=state,
                district__iexact=district
            )[:6]
            print("STATE:", state)
            print("DISTRICT:", district)
            print("CONTACT COUNT:", contacts.count())

    return render(request, "listings/index.html", {
        "result": result,
        "contacts": contacts
    })



@login_required
def profile(request):
    return render(request, "listings/profile.html")

@login_required
def land_prediction(request):
    result = None
    contacts = []

    if request.method == "POST":

        # Get form data
        state = (request.POST.get("state") or "").strip()
        city = (request.POST.get("city") or "").strip()
        plot_type = request.POST.get("plot_type")
        area = request.POST.get("Area")

        # 🔹 IMPORTANT: use dataset column names
        data = {
            "State": state,
            "District": city,
            "Plot_Type": plot_type
        }

        # Predict price per sqft
        price_per_sqft = predict_land_price(data)
        print("PRICE PER SQFT:", price_per_sqft)
        area = float(area or 0)

        # Calculate total price
        if price_per_sqft is not None:
            result = float(price_per_sqft) * area
            print("FINAL RESULT:", result)
        else:
            result = 0

        # Load matching realtors
        if state and city:
            contacts = Realtor.objects.filter(
                state__iexact=state,
                district__iexact=city
            )[:6]

        # Save to history
        # if result is not None:
            try:
                LandQuery.objects.create(
                    user=request.user,
                    state=state,
                    district=city,
                    land_area=area,
                    soil_type=plot_type or "Unknown",
                    road_width=0.0,
                    land_shape="Residential",
                    predicted_price=float(result)
                )
            except Exception as e:
                print("Land history save failed:", e)

    return render(request, "listings/land.html", {
        "result": result,
        "contacts": contacts
    })
            
             
                    
        

        
                   
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
def land_history(request):
    records = LandQuery.objects.all().order_by("-created_at")

    return render(request, "listings/land_history.html", {
        "records": records
    })
# DASHBOARD (ORM-based aggregations)
# ---------------------------
@login_required
def dashboard(request):
    load_artifacts()

    qs = PropertyQuery.objects.filter(user=request.user)
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
    qs = LandQuery.objects.filter(user=request.user)
    print("Dashboard records:", qs.count())
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
    .order_by("-cnt")   # show most used first
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




@login_required
def login_history(request):
    records = LoginHistory.objects.filter(user=request.user).order_by('-login_time')
    return render(request, "listings/login_history.html", {
        "records": records
    })

