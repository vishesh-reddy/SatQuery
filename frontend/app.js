const API_BASE="http://127.0.0.1:5000";
let files=[];
const $=id=>document.getElementById(id);
const input=$("fileInput"),drop=$("drop"),list=$("files"),img=$("mainImage"),placeholder=$("placeholder");
function picker(){input.click()}
$("topUpload").onclick=picker;$("mainUpload").onclick=picker;drop.onclick=picker;
input.onchange=e=>addFiles([...e.target.files]);
drop.ondragover=e=>{e.preventDefault();drop.classList.add("drag")};drop.ondragleave=()=>drop.classList.remove("drag");drop.ondrop=e=>{e.preventDefault();drop.classList.remove("drag");addFiles([...e.dataTransfer.files])};
function addFiles(fs){const ok=fs.filter(f=>/\.(jpg|jpeg|png|webp|tif|tiff)$/i.test(f.name));if(!ok.length){alert("Use JPG, PNG, WEBP, TIFF or GeoTIFF files.");return}files=files.concat(ok);render();show();meta(files[0])}
function render(){list.innerHTML="";files.forEach((f,i)=>{const x=document.createElement("div");x.className="file";x.innerHTML="<div><b>"+esc(f.name)+"</b><small>"+size(f.size)+"</small></div><button>×</button>";x.querySelector("button").onclick=()=>{files.splice(i,1);render();show()};list.appendChild(x)})}
function show(){if(!files.length){img.classList.add("hidden");placeholder.classList.remove("hidden");return}const f=files[0];if(f.type.startsWith("image/")&&!/\.tiff?$/i.test(f.name)){img.src=URL.createObjectURL(f);img.classList.remove("hidden");placeholder.classList.add("hidden")}else{img.classList.add("hidden");placeholder.classList.remove("hidden");placeholder.querySelector("h2").textContent="GeoTIFF loaded";placeholder.querySelector("p").textContent=f.name+" is ready for geospatial processing."}}
function meta(f){$("mf").textContent=f.name.split(".").pop().toUpperCase();$("ms").textContent=size(f.size);const n=f.name.toLowerCase();$("mm").textContent=n.includes("sar")||n.includes("risat")||n.includes("sentinel-1")?"SAR":n.includes("multispectral")||n.includes("sentinel-2")||n.includes("landsat")?"Multispectral":"Optical"}
function size(n){return n<1024?n+" B":n<1048576?(n/1024).toFixed(1)+" KB":(n/1048576).toFixed(1)+" MB"}function esc(s){return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;")}
function tab(n){document.querySelectorAll(".tab").forEach(t=>t.classList.toggle("active",t.dataset.tab===n));["analysis","execution","metadata","chat"].forEach(x=>document.getElementById(x+"Tab").classList.toggle("hidden",x!==n))}
document.querySelectorAll(".tab").forEach(t=>t.onclick=()=>tab(t.dataset.tab));
document.querySelectorAll(".quick button").forEach(b=>b.onclick=()=>{const t=b.dataset.type;if(t==="query"){tab("chat");$("chatInput").focus()}else{$("type").value=t;tab("analysis");$("query").focus()}});
$("newAnalysis").onclick=()=>{files=[];input.value="";list.innerHTML="";$("query").value="";$("chatInput").value="";img.classList.add("hidden");placeholder.classList.remove("hidden");tab("analysis")};
async function analyze(q){if(!files.length){result("Please upload a satellite image first.");return}if(!q){result("Please enter an analysis query.");return}const fd=new FormData();fd.append("image",files[0]);fd.append("question",q);$("run").disabled=true;$("run").textContent="⟳ Running Analysis...";$("execStatus").textContent="RUNNING";tab("execution");try{const r=await fetch(API_BASE+"/analyze",{method:"POST",body:fd});const d=await r.json().catch(()=>({}));if(!r.ok||!d.success)throw new Error(d.error||"Analysis failed.");result(d.answer||"No analysis returned.");tab("chat")}catch(e){result("⚠ "+e.message);tab("chat")}finally{$("run").disabled=false;$("run").textContent="▶ Run Analysis";$("execStatus").textContent="READY"}}
function result(t){$("result").innerHTML="<div style='width:100%;padding:12px;border:1px solid #19313d;border-radius:8px;background:#0a1921;color:#c5d7dd;font-size:9px;line-height:1.65;white-space:pre-wrap'>"+esc(t)+"</div>"}
$("run").onclick=()=>analyze($("query").value.trim());$("send").onclick=()=>{const q=$("chatInput").value.trim();$("chatInput").value="";analyze(q)};$("chatInput").onkeydown=e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();$("send").click()}};
$("zin").onclick=()=>img.style.transform="scale(1.15)";$("zout").onclick=()=>img.style.transform="scale(1)";$("fit").onclick=()=>img.style.transform="scale(1)";
document.querySelectorAll(".nav").forEach(n=>n.onclick=()=>{document.querySelectorAll(".nav").forEach(x=>x.classList.remove("active"));n.classList.add("active")});
fetch(API_BASE+"/health").catch(()=>console.info("SatQuery backend is offline. Start Flask on port 5000."));
