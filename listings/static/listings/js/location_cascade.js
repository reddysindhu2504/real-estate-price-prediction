document.addEventListener('DOMContentLoaded', function() {
  const stateSel = document.getElementById('id_state');
  const districtSel = document.getElementById('id_district');

  if (!stateSel || !districtSel) return;

  fetch("/static/listings/data/india_states_districts.json")
    .then(r => r.json())
    .then(data => {
      // populate states if not populated
      if (stateSel.options.length <= 1) {
        Object.keys(data).sort().forEach(s => {
          const o = document.createElement('option'); o.value = s; o.text = s;
          stateSel.add(o);
        });
      }

      // if state preselected, populate districts
      if (stateSel.value) populateDistricts(stateSel.value);

      stateSel.addEventListener('change', function() {
        populateDistricts(this.value);
      });

      function populateDistricts(state) {
        districtSel.innerHTML = '<option value="">Select District</option>';
        const ds = data[state] || [];
        ds.sort().forEach(d => {
          const o = document.createElement('option'); o.value = d; o.text = d;
          districtSel.add(o);
        });
      }
    })
    .catch(e => console.error("Failed to load districts JSON:", e));
});

// location_cascade.js
// Usage: page must have #id_state and #id_district (the form fields in your form)
(function(){
  const STATE_ID = 'id_state';
  const DIST_ID = 'id_district';
  const JSON_PATH = '/static/listings/data/india_states_districts.json';

  async function loadData(){
    try{
      const res = await fetch(JSON_PATH);
      if(!res.ok) throw new Error('states JSON not found');
      const data = await res.json();
      return data;
    }catch(e){
      console.warn('Location cascade load error:', e);
      return null;
    }
  }

  function fillSelect(sel, items, placeholder){
    if(!sel) return;
    sel.innerHTML = ''; // clear
    const ph = document.createElement('option');
    ph.value = '';
    ph.textContent = placeholder || 'Select';
    sel.appendChild(ph);
    items.forEach(it => {
      const o = document.createElement('option');
      o.value = it; o.textContent = it;
      sel.appendChild(o);
    });
  }

  async function init(){
    const data = await loadData();
    const stateEl = document.getElementById(STATE_ID);
    const distEl = document.getElementById(DIST_ID);
    if(!stateEl || !distEl) return;

    if(data){
      const states = Object.keys(data).sort();
      fillSelect(stateEl, states, 'Select State');

      stateEl.addEventListener('change', function(){
        const s = this.value;
        if(!s){ fillSelect(distEl, [], 'Select District'); return; }
        const districts = Array.isArray(data[s]) ? data[s].slice().sort() : [];
        fillSelect(distEl, districts, 'Select District');
      });

      // if page had preselected value (edit or after validation), populate districts
      if(stateEl.value){
        const districts = data[stateEl.value] || [];
        fillSelect(distEl, districts, 'Select District');
      }
    }else{
      // fallback: allow free text (we used CharField). No-op
    }
  }

  // init on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

document.addEventListener("DOMContentLoaded", function () {
    const stateSelect = document.getElementById("id_state");
    const districtSelect = document.getElementById("id_district");

    const data = window.locationData || {};

    stateSelect.addEventListener("change", function () {
        const state = this.value;

        districtSelect.innerHTML = "<option value=''>Select district</option>";

        if (data[state]) {
            data[state].forEach(d => {
                let opt = document.createElement("option");
                opt.value = d;
                opt.textContent = d;
                districtSelect.appendChild(opt);
            });
        }
    });
});
