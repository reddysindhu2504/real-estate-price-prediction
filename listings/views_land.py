from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .forms_land import LandForm
from .land_predictor import predict_land_price

@login_required
def land_prediction(request):
    result = None
    form = LandForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data

        model_input = {
            "State": data["state"],
            "District": data["district"],
            "Land_Area": data["land_area"],
            "Soil_Type": data["soil_type"],
            "Road_Width": data["road_width"],
            "Land_Shape": data["land_shape"],
        }

        result = predict_land_price(model_input)

    return render(request, "listings/land.html", {
        "form": form,
        "result": result
    })
