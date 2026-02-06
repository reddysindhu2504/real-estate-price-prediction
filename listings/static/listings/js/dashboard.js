// static/listings/js/dashboard.js
(function () {
  function safeNumber(v) { var n = Number(v); return isNaN(n) ? 0 : n; }

  var raw = window.avgByLocation || [];
  var dataList = Array.isArray(raw) ? raw : [];
  var labels = dataList.map(function(r) { return r[0]; });
  var values = dataList.map(function(r) { return safeNumber(r[1]); });

  var ctx = document.getElementById('avgLocationChart');
  if (!ctx) return;

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Avg Predicted Price (₹)',
        data: values,
        backgroundColor: labels.map(() => 'rgba(13,110,253,0.75)'),
        borderColor: labels.map(() => 'rgba(13,110,253,1)'),
        borderWidth: 1
      }]
    },
    options: {
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function(value) { return value.toLocaleString(); }
          }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) { return '₹' + Number(context.parsed.y).toLocaleString(); }
          }
        }
      }
    }
  });
})();
// dashboard.js
(function(){
  function safeParseScriptId(id){
    const el = document.getElementById(id);
    if(!el) return null;
    try{ return JSON.parse(el.textContent || el.innerText); }catch(e){ console.error('JSON parse',id,e); return null; }
  }

  document.addEventListener('DOMContentLoaded', function(){
    const avg_by_location = safeParseScriptId('avg_by_location_data'); // [[loc,avg],...]
    const cluster_stats = safeParseScriptId('cluster_stats_data');     // [{cluster,cnt,avg_price},...]

    // loc bar chart (horizontal)
    if(Array.isArray(avg_by_location) && avg_by_location.length>0){
      const labels = avg_by_location.map(i=>String(i[0]));
      const data = avg_by_location.map(i=>Number(i[1]||0));
      const ctx = document.getElementById('locBarChart');
      if(ctx && window.Chart){
        new Chart(ctx, {
          type:'bar',
          data:{labels, datasets:[{label:'Avg price (₹)', data, borderWidth:1}]},
          options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
            plugins:{legend:{display:false}, tooltip:{callbacks:{label:ctx=> '₹'+Number(ctx.parsed.x).toLocaleString('en-IN')}}},
            scales:{ x:{ticks:{callback:v=>Number(v).toLocaleString('en-IN')}}}
          }
        });
      }
    }

    // cluster count chart
    if(Array.isArray(cluster_stats) && cluster_stats.length>0){
      const labels = cluster_stats.map(s=>'Cluster '+s.cluster);
      const values = cluster_stats.map(s=>Number(s.cnt || 0));
      const ctx2 = document.getElementById('clusterCountChart');
      if(ctx2 && window.Chart){
        new Chart(ctx2, {
          type:'bar',
          data:{labels, datasets:[{label:'# records', data:values, borderWidth:1}]},
          options:{responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}}}
        });
      }
    }
  });
})();
