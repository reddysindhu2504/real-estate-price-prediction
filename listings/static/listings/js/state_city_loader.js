document.addEventListener("DOMContentLoaded", function () {

  const stateSelect = document.getElementById("stateSelect");
  const citySelect = document.getElementById("citySelect");

  fetch("/static/listings/data/states_cities.json")
    .then(res => res.json())
    .then(statesData => {

      // load states
      Object.keys(statesData).forEach(state => {
        const opt = document.createElement("option");
        opt.value = state;
        opt.textContent = state;
        stateSelect.appendChild(opt);
      });

      // load cities
      stateSelect.addEventListener("change", function () {
        citySelect.innerHTML = `<option value="">Select City</option>`;
        statesData[this.value]?.forEach(city => {
          const opt = document.createElement("option");
          opt.value = city;
          opt.textContent = city;
          citySelect.appendChild(opt);
        });
      });

    })
    .catch(err => {
      console.error("FAILED TO LOAD STATES JSON", err);
    });

});
