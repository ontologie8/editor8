// SPDX-License-Identifier: AGPL-3.0-or-later
"use strict";

const groups = [
  ["required_information", "Fragen", "#e8f2ff", "#4b77a7"],
  ["documents", "Dokumenttypen", "#eef8ee", "#4d8a55"],
  ["decisions", "Entscheidungen", "#fff4df", "#ac7a21"],
  ["gates", "Prüfschritte", "#fdebec", "#b45c64"],
  ["evidence", "Nachweistypen", "#f3edff", "#8060aa"]
];
const relations = {
  erfordert: "erfordert",
  informiert: "informiert",
  blockiertBisVollstaendig: "wartet auf vollständige Angaben",
  blockiertBisGeprueft: "wartet auf Prüfung",
  erfordertEntscheidung: "erfordert Entscheidung",
  belegtDurch: "belegt durch",
  fuellt: "füllt",
  bestimmt: "bestimmt"
};
const $ = id => document.getElementById(id);
const svgNS = "http://www.w3.org/2000/svg";
let state = { token: "", branch: "", purpose: "case", activeCase: "", hosted: false, user: "", notaryReviewer: false, ontologyMaintainer: false, reviewDetail: null, current: null, cases: [], selected: null, nodeEditing: false, dirty: false, graphFocused: false, graphMode: "linked", graphZoom: 1, graphSearchTarget: "node", view: "fall", vocabulary: null, vocabSelected: null, vocabEditing: false, vocabNew: false, vocabularyImpact: null, impactLoading: false, impactError: "", caseIndex: null, caseIndexPromise: null, caseHistory: null, historyTarget: "", drafts: [] };
const saveFlow = {pending: "", preview: null};
let caseLoadSequence = 0;
let viewSequence = 0;
let nodeEditPending = false;
const recovery=window.EditorRecovery.create({state:()=>state,repository:()=>$("repository-name").textContent||"local",api,notice,refresh:refreshBranch,
  discard:()=>{state.dirty=false;window.location.reload();},
  saved:()=>{state.dirty=false;refreshBranch();},
  extras:()=>state.purpose==="vocabulary"?{vocabReason:$("vocab-reason").value,vocabSource:$("vocab-source").value}:{reason:$("change-reason").value,source:$("change-source").value},
  adopt:async(model,entry)=>{
    if(entry.purpose==="vocabulary"){
      state.vocabulary=model;state.vocabSelected=entry.selected;state.vocabEditing=true;state.vocabNew=!entry.base.terms.some(term=>term.id===entry.selected);setView("vokabular");renderVocabulary();
    }else{
      state.current=model;state.selected=entry.selected;state.nodeEditing=true;$("case-title").textContent=model.title;$("case-select").value=model.slug;$("summary").value=model.summary;$("sources").value=model.sources.join("\n");setView("bausteine");renderAll();renderNodeForm();
    }
    for(const [key,id]of Object.entries({reason:"change-reason",source:"change-source",vocabReason:"vocab-reason",vocabSource:"vocab-source"}))$(id).value=entry.extras?.[key]||"";
    dirty();
  }
});

function element(tag, text, className) {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = text;
  if (className) el.className = className;
  return el;
}
function svg(tag, attrs = {}) {
  const el = document.createElementNS(svgNS, tag);
  for (const [name, value] of Object.entries(attrs)) el.setAttribute(name, value);
  return el;
}
function notice(message, type = "") {
  $("notice").textContent = message;
  $("notice").className = "notice " + type;
}
async function api(path, body) {
  const options = body === undefined ? {} : {
    method: "POST",
    headers: {"Content-Type": "application/json", "X-Editor-Token": state.token},
    body: JSON.stringify(body)
  };
  let response;
  try{response=await fetch(path,options);}
  catch{throw new Error("Die Verbindung zum Editor ist fehlgeschlagen. Bitte erneut versuchen.");}
  let result;
  try{result=await response.json();}
  catch{throw new Error("Der Editor hat keine gültige Antwort geliefert. Bitte erneut versuchen.");}
  if (response.status === 401) {
    recovery.expired();
    throw new Error("Anmeldung erforderlich");
  }
  if (!response.ok) throw new Error(result.error || "Anfrage fehlgeschlagen");
  return result;
}
function dirty() {
  caseLoadSequence++;
  if(state.current)$("case-select").value=state.current.slug;
  state.dirty = true;
  recovery.capture();
  refreshBranch();
  renderCaseList();
  notice("Änderungen sind noch nicht gespeichert.");
}
function displayNodeLabel(node) {
  const prefix={documents:/^Dokument:\s*/i,decisions:/^Entscheidung:\s*/i,gates:/^Prüfgate:\s*/i,evidence:/^Nachweis:\s*/i}[node.category];
  return prefix ? node.label.replace(prefix,"") : node.label;
}
function nodeLabel(id) {
  const node=state.current.nodes.find(item => item.id === id);
  return node ? displayNodeLabel(node) : id;
}
function caseEditable() {
  return state.branch !== "main" && state.purpose === "case" && (!state.hosted || state.activeCase === state.current?.slug);
}
function refreshBranch() {
  $("branch").textContent = state.branch && state.branch!=="main" ? (state.hosted && state.purpose==="case" && !caseEditable() ? "Anderen Fall ansehen" : "Mein Entwurf") : "Lesemodus";
  const activeTitle=state.cases.find(item=>item.slug===state.activeCase)?.title || state.activeCase;
  $("branch").title = state.branch && state.branch!=="main" ? `GitHub-Zweig: ${state.branch}${activeTitle ? " · Entwurf für " + activeTitle : ""}` : "Aktueller Katalogstand";
  $("draft-panel").hidden = state.branch !== "main" || !state.drafts.length;
  $("start-branch").hidden = state.branch !== "main" || (state.view==="vokabular" && !state.ontologyMaintainer);
  $("start-branch").disabled = !state.current;
  $("leave-draft").hidden = !state.hosted || state.branch === "main";
  $("save").hidden = false;
  $("save").disabled = !!saveFlow.pending || !state.dirty || (state.view==="vokabular" ? state.purpose!=="vocabulary" : !caseEditable());
  $("add-node").hidden=!caseEditable();
  $("edge-create").hidden=!caseEditable();
  for(const id of ["add-node","add-edge","submit-review"]) $(id).disabled=!caseEditable();
  $("edit-overview").disabled=state.branch!=="main" && !caseEditable();
  $("edit-node").disabled=nodeEditPending || !!saveFlow.pending || (state.branch!=="main" && !caseEditable());
  $("vocab-add").hidden=!state.ontologyMaintainer || (state.branch!=="main" && state.purpose!=="vocabulary");
  $("vocab-submit").disabled=state.branch==="main" || state.purpose!=="vocabulary";
  renderOffice();
  document.dispatchEvent(new Event("editor-state-change"));
}
function renderCaseList() {
  const root=$("case-list");root.replaceChildren();
  const query=$("case-search").value.trim().toLocaleLowerCase("de");
  let count=0;
  state.cases.forEach(item=>{
    const current=state.current?.slug===item.slug;
    const nodes=current?state.current.nodes:[];
    const matching=nodes.filter(node=>[node.label,node.question,node.id].join(" ").toLocaleLowerCase("de").includes(query));
    if(query&&!item.title.toLocaleLowerCase("de").includes(query)&&!matching.length)return;
    count++;
    const branch=element("details",undefined,"tree-case");branch.open=current&&!office.closedCases.has(item.slug);
    const summary=element("summary");const button=element("button",item.title,"case-item"+(current?" active":""));button.type="button";button.setAttribute("aria-current",current?"page":"false");
    button.dataset.contextCase=item.slug;
    button.setAttribute("aria-haspopup","menu");
    button.addEventListener("click",event=>{event.preventDefault();loadCase(item.slug).catch(error=>notice(error.message,"error"));});summary.append(button);branch.append(summary);
    branch.addEventListener("toggle",()=>{if(branch.open)office.closedCases.delete(item.slug);else office.closedCases.add(item.slug);});
    if(current){groups.forEach(([key,title])=>{
      const matches=(query&&!item.title.toLocaleLowerCase("de").includes(query)?matching:nodes).filter(node=>node.category===key).sort((a,b)=>a.label.localeCompare(b.label,"de"));if(!matches.length)return;
      const category=element("details",undefined,"tree-category");const categoryKey=item.slug+":"+key;category.open=!office.closedGroups.has(categoryKey);category.append(element("summary",title+" · "+matches.length));
      category.addEventListener("toggle",()=>{if(category.open)office.closedGroups.delete(categoryKey);else office.closedGroups.add(categoryKey);});
      matches.forEach(node=>{const leaf=element("button",displayNodeLabel(node),"tree-node"+(state.selected===node.id?" active":""));leaf.type="button";nodeContext(leaf,node);leaf.setAttribute("aria-pressed",String(state.selected===node.id));leaf.addEventListener("click",()=>{if(office.area==='edit')selectNode(node.id);else{setView('fall');focusGraphNode(node.id);}renderCaseList();});category.append(leaf);});branch.append(category);
    });}
    root.append(branch);
  });
  if(!count)root.append(element("p","Kein Eintrag gefunden.","empty"));
}
function renderCaseIndex() {
  const root=$("case-index-results");root.replaceChildren();
  const query=$("case-index-query").value.trim().toLocaleLowerCase("de");
  if(query.length<2){$("case-index-status").textContent="Mindestens zwei Zeichen eingeben. Die Suche zeigt fachliche Bausteine aus dem aktuellen Katalogstand.";return;}
  if(!state.caseIndex){$("case-index-status").textContent="Bausteine werden geladen …";return;}
  const words=query.split(/\s+/).filter(Boolean);
  const matches=state.caseIndex.entries.filter(item=>{
    const content=[item.case_title,item.label,item.question,item.detail,item.node_id].join(" ").toLocaleLowerCase("de");
    return words.every(word=>content.includes(word));
  });
  const source=state.caseIndex.source_ref;
  $("case-index-status").textContent=`${matches.length} Treffer in ${state.caseIndex.case_count} Fällen · Katalogstand ${/^[0-9a-f]{40}$/.test(source) ? source.slice(0,12) : source}`;
  matches.slice(0,40).forEach(item=>{
    const button=element("button",undefined,"case-index-result");button.type="button";
    button.append(element("strong",displayNodeLabel(item)),element("small",`${item.case_title} · ${groups.find(group=>group[0]===item.category)?.[1] || item.category}`));
    if(item.question)button.append(element("span",item.question));
    button.addEventListener("click",async()=>{
      try{
        await loadCase(item.slug);
        if(state.current.slug!==item.slug)return;
        $("node-search").value="";$("node-category").value="";
        selectNode(item.node_id);
        $("catalog-search").close();
      }catch(error){notice(error.message,"error");}
    });
    root.append(button);
  });
  if(matches.length>40)root.append(element("p","Die ersten 40 Treffer werden angezeigt. Suche bitte genauer.","context-help"));
  if(!matches.length)root.append(element("p","Kein passender Baustein gefunden.","empty"));
}
async function loadCaseIndex() {
  if(!state.caseIndexPromise){
    state.caseIndexPromise=api("/api/case-index").then(result=>{state.caseIndex=result;renderCaseIndex();return result;}).catch(error=>{state.caseIndexPromise=null;$("case-index-status").textContent="Suche konnte nicht geladen werden: "+error.message;throw error;});
  }
  return state.caseIndexPromise;
}
function renderOverview() {
  $("summary-read").textContent=state.current.summary;
  const sources=$("source-links");sources.replaceChildren();
  state.current.sources.forEach(source=>{
    try{
      const url=new URL(source);
      if(url.protocol!=="https:") throw new Error("Ungültige Quelle");
      const link=element("a",url.hostname + url.pathname,"source-link");link.href=url.href;link.target="_blank";link.rel="noopener noreferrer";
      sources.append(link);
    }catch{sources.append(element("span","Quelle benötigt eine HTTPS-Adresse","source-invalid"));}
  });
}
function renderGraphSearch() {
  const root=$("graph-results");root.replaceChildren();
  if(!state.current)return;
  const words=$("graph-query").value.trim().toLocaleLowerCase("de").split(/\s+/).filter(Boolean);
  let count=0;
  groups.forEach(([category,title])=>{
    const matches=state.current.nodes.filter(node=>node.category===category && words.every(word=>[node.label,node.question,node.detail].join(" ").toLocaleLowerCase("de").includes(word))).sort((a,b)=>a.label.localeCompare(b.label,"de"));
    if(!matches.length)return;
    const section=element("section",undefined,"graph-result-group");section.append(element("h3",title));
    matches.forEach(node=>{
      const button=element("button",displayNodeLabel(node),"graph-result");button.type="button";
      button.addEventListener("click",()=>{
        $("case-node-search").close();
        if(state.graphSearchTarget==="edge-from" || state.graphSearchTarget==="edge-to"){
          $(state.graphSearchTarget).value=node.id;fillNodeSelects();
        }else focusGraphNode(node.id);
      });
      section.append(button);
    });
    count+=matches.length;root.append(section);
  });
  $("graph-search-count").textContent=count+" "+(count===1?"Baustein":"Bausteine");
  if(!count)root.append(element("p","Kein Treffer.","empty"));
}
function openGraphSearch(target="node") {
  state.graphSearchTarget=target;
  $("case-node-search-title").textContent=target==="edge-from" ? "Ausgang wählen" : target==="edge-to" ? "Ziel wählen" : "Baustein suchen";
  $("graph-query").value="";
  renderGraphSearch();
  $("case-node-search").showModal();
  $("graph-query").focus();
}
function enableSearchKeyboard(queryId,resultsId) {
  const query=$(queryId),results=$(resultsId);
  query.addEventListener("keydown",event=>{
    if(event.key!=="ArrowDown" && event.key!=="Enter")return;
    const first=results.querySelector("button");
    if(!first)return;
    event.preventDefault();
    if(event.key==="Enter")first.click();else first.focus();
  });
  results.addEventListener("keydown",event=>{
    if(event.key!=="ArrowDown" && event.key!=="ArrowUp")return;
    const buttons=[...results.querySelectorAll("button")];
    const index=buttons.indexOf(document.activeElement);
    if(index<0)return;
    event.preventDefault();
    if(event.key==="ArrowUp" && index===0)query.focus();
    else buttons[Math.max(0,Math.min(buttons.length-1,index+(event.key==="ArrowDown"?1:-1)))].focus();
  });
}
async function loadCaseHistory() {
  const slug=state.current.slug;
  const root=$("history-list");root.replaceChildren(element("p","Änderungen werden geladen …","empty"));
  const history=await api("/api/cases/"+encodeURIComponent(slug)+"/history");
  if(state.current.slug!==slug)return;
  state.caseHistory=history;root.replaceChildren();
  if(!history.entries.length){root.append(element("p","Noch keine gespeicherte Änderung gefunden.","empty"));return;}
  history.entries.forEach(item=>{
    const row=element("div",undefined,"history-item");
    const info=element("div");
    info.append(element("strong",item.message || "Änderung der Fallvorlage"));
    const date=item.date ? new Date(item.date).toLocaleDateString("de-DE") : "Datum unbekannt";
    info.append(element("small",`${date} · ${item.author} · ${item.sha.slice(0,10)}`));
    const actions=element("div",undefined,"history-actions");
    const link=element("a","Auf GitHub ansehen ↗");link.href=item.url;link.target="_blank";link.rel="noopener noreferrer";
    const button=element("button","Fassung prüfen");button.type="button";
    button.disabled=state.branch!=="main";
    button.addEventListener("click",()=>previewCaseHistory(item).catch(error=>notice(error.message,"error")));
    actions.append(link,button);row.append(info,actions);root.append(row);
  });
  if(state.branch!=="main")root.prepend(element("p","Eine frühere Fassung kann erst nach Abschluss des laufenden Arbeitszweigs übernommen werden.","context-help"));
}
async function previewCaseHistory(item) {
  if(!state.caseHistory || state.branch!=="main")throw new Error("Bitte Fall und Historie neu laden.");
  const result=await api("/api/cases/"+encodeURIComponent(state.current.slug)+"/restore-preview",{
    target_sha:item.sha,expected_main:state.caseHistory.main_ref
  });
  state.historyTarget=item.sha;
  $("history-preview").hidden=false;
  $("history-target").textContent=`Frühere Fassung ${item.sha.slice(0,10)} von ${item.author}. Der aktuelle Fall wird dadurch nicht direkt geändert.`;
  const list=$("history-changes");list.replaceChildren();
  result.changes.forEach(change=>list.append(element("li",change)));
  if(!result.changed)list.append(element("li","Diese Fassung entspricht bereits dem aktuellen Fall."));
  $("history-apply").disabled=!result.changed;
}
async function applyCaseHistory() {
  try{
    if(!state.caseHistory || !state.historyTarget || state.branch!=="main")throw new Error("Bitte die frühere Fassung erneut prüfen.");
    const slug=state.current.slug;
    const result=await api("/api/cases/"+encodeURIComponent(slug)+"/restore",{
      target_sha:state.historyTarget,expected_main:state.caseHistory.main_ref
    });
    state.branch=result.branch;state.purpose="case";refreshBranch();
    await loadCase(slug);setView("pruefung");
    notice("Frühere Fassung als neuer Arbeitsentwurf gespeichert. Bitte Grund und Quellenstand angeben und zur notariellen Prüfung einreichen.","success");
  }catch(error){notice(error.message,"error");}
}
async function loadReviewQueue() {
  const root=$("review-list");root.replaceChildren(element("p","Änderungen werden geladen …","empty"));
  const reviews=await api("/api/reviews");root.replaceChildren();
  if(!reviews.length){root.append(element("p","Derzeit liegt keine einzelne Änderung zur Prüfung vor.","empty"));notice("Prüfkorb geladen.","quiet");return;}
  reviews.forEach(item=>{
    const card=element("button",undefined,"review-item"+(state.reviewDetail?.number===item.number ? " active" : ""));card.type="button";
    const caseTitle=item.case==="vocabulary" ? "Gemeinsames Vokabular" : state.cases.find(entry=>entry.slug===item.case)?.title || item.case;
    card.append(element("strong",caseTitle),element("span",`#${item.number} · von ${item.author} · ${item.draft ? "noch in Arbeit" : "zur Prüfung"}`));
    card.addEventListener("click",()=>loadReview(item.number).catch(error=>notice(error.message,"error")));root.append(card);
  });
  notice("Prüfkorb geladen.","quiet");
}
async function loadReview(number) {
  const detail=await api("/api/reviews/"+number);state.reviewDetail=detail;
  $("review-detail").hidden=false;$("review-title").textContent=detail.title;
  $("review-meta").textContent=`${detail.case==="vocabulary" ? "Gemeinsames Vokabular" : "Fall: " + (state.cases.find(item=>item.slug===detail.case)?.title || detail.case)} · erstellt von ${detail.author} · ${detail.draft ? "noch in Arbeit" : "zur Prüfung bereit"}`;
  $("review-pr-link").href=detail.url;
  const body=$("review-body");body.replaceChildren();
  const sections=(detail.body || "").split(/^## /m);
  if(sections[0].trim())body.append(element("p",sections[0].trim()));
  sections.slice(1).forEach(section=>{
    const [title,...lines]=section.split("\n");
    body.append(element("h5",title.trim()),element("p",lines.join("\n").trim() || "Keine Angabe."));
  });
  if(!body.childNodes.length)body.append(element("p","Keine Begründung im Pull Request angegeben."));
  const list=$("review-changes");list.replaceChildren();
  detail.changes.forEach(change=>list.append(element("li",change)));
  window.EditorComparison.render($("review-comparison"),detail.comparison,relations);
  if(!detail.changes.length)list.append(element("li","Keine erklärbare fachliche Änderung vorhanden."));
  $("review-problem").hidden=!detail.problem;$("review-problem").textContent=detail.problem;
  $("request-changes").disabled=!detail.can_review;
  $("approve-review").disabled=!detail.can_approve;
  $("review-checklist").hidden=!detail.can_approve;
  $("review-permission").textContent=detail.draft ? "Diese Änderung ist noch in Arbeit." :
    !detail.can_review ? "Eigene Änderungen können hier nicht selbst geprüft werden." :
    detail.problem ? "Eine Freigabe ist erst nach Klärung der angezeigten Abweichung möglich." :
    !detail.can_approve ? "Fachliche Freigaben sind nur für eingetragene Notarkonten möglich." :
    "Prüfe Begriffe, Quellen und Beziehungen. Deine Entscheidung wird deinem GitHub-Konto zugeordnet.";
  $("review-comment").value="";$("review-result").hidden=true;
  for(const id of ["review-terms","review-sources","review-relations"])$(id).checked=false;
  await loadReviewQueue();
}
async function submitCaseReview(event) {
  try{
    const detail=state.reviewDetail;
    if(!detail)throw new Error("Bitte zuerst eine Änderung auswählen.");
    const body=$("review-comment").value.trim();
    if(body.length<15)throw new Error("Bitte deine fachliche Begründung in mindestens 15 Zeichen festhalten.");
    const checks={terms:$("review-terms").checked,sources:$("review-sources").checked,relations:$("review-relations").checked};
    if(event==="APPROVE" && !Object.values(checks).every(Boolean))throw new Error("Bitte zuerst Begriffe, Quellen und Beziehungen als geprüft markieren.");
    const result=await api(`/api/reviews/${detail.number}/review`,{head_sha:detail.head_sha,event,body,checks});
    $("review-result").href=result.url;$("review-result").hidden=false;
    notice(event==="APPROVE" ? "Fachliche Freigabe in GitHub dokumentiert." : "Änderungswunsch in GitHub dokumentiert.","success");
  }catch(error){notice(error.message,"error");}
}
async function beginBranch(purpose="case") {
  if(state.dirty) throw new Error("Bitte ungespeicherte Änderungen vor einem neuen Arbeitszweig prüfen.");
  const result=await api("/api/start-branch",{purpose,case:purpose==="case" ? state.current.slug : ""});state.branch=result.branch;state.purpose=result.purpose || purpose;state.activeCase=result.case || "";refreshBranch();
  if(purpose==="vocabulary") await loadVocabulary(true);
  else await loadCase(state.current.slug);
  notice("Änderung begonnen. Du bearbeitest jetzt deinen eigenen Arbeitszweig.","success");
}
async function loadDrafts() {
  if(state.branch!=="main")return;
  const drafts=await api("/api/drafts");state.drafts=drafts;
  const root=$("draft-list");root.replaceChildren();
  drafts.forEach(draft=>{
    const title=draft.purpose==="vocabulary" ? "Gemeinsame Begriffe" : draft.case ? state.cases.find(item=>item.slug===draft.case)?.title || draft.case : "Begonnener Fallentwurf";
    const button=element("button",`${title} weiterbearbeiten`);button.type="button";
    if(!draft.case)button.title="Noch keine fachliche Änderung gespeichert";
    button.addEventListener("click",()=>resumeDraft(draft).catch(error=>notice(error.message,"error")));
    root.append(button);
  });
  refreshBranch();
}
async function resumeDraft(draft) {
  if(state.dirty || state.branch!=="main")throw new Error("Bitte die laufende Änderung zuerst abschließen.");
  const result=await api("/api/drafts/resume",{branch:draft.branch,case:state.current.slug});
  state.branch=result.branch;state.purpose=result.purpose;state.activeCase=result.case || "";refreshBranch();
  if(result.purpose==="vocabulary") {await loadVocabulary(true);setView("vokabular");}
  else {await loadCase(result.case);setView("bausteine");}
  notice("Gespeicherten Entwurf wieder geöffnet. Du kannst die Änderung weiterbearbeiten oder zur Prüfung geben.","success");
}
async function leaveDraft() {
  if(saveFlow.pending)throw new Error("Bitte den laufenden Speichervorgang abwarten.");
  if(recovery.hasInputs && !window.confirm("Ungespeicherte Eingaben verwerfen? Bereits auf GitHub gespeicherte Änderungen bleiben erhalten."))return;
  const slug=state.current.slug;
  await api("/api/drafts/leave",{});
  recovery.clear();
  for(const id of ["change-reason","change-source","vocab-reason","vocab-source"])$(id).value="";
  state.branch="main";state.purpose="case";state.activeCase="";state.dirty=false;
  state.vocabulary=null;
  await loadCase(slug);
  await loadDrafts();
  notice("Entwurf abgelegt. Du kannst ihn unter „Meine Arbeitsentwürfe“ wieder öffnen.","success");
}
const vocabularyKinds={class:"Begriffsklasse",object_property:"Verbindung",datatype_property:"Merkmal"};
function selectedTerm(){return state.vocabulary?.terms.find(item=>item.id===state.vocabSelected);}
async function loadVocabulary(force=false){
  if(state.dirty && force)throw new Error("Bitte offene Änderungen zuerst speichern.");
  if(!state.vocabulary || force){state.vocabulary=await api("/api/vocabulary");recovery.setBase(state.vocabulary,"vocabulary");state.vocabSelected=state.vocabulary.terms[0]?.id || null;state.vocabEditing=false;state.vocabNew=false;}
  renderVocabulary();
  if((force || !state.vocabularyImpact) && !state.impactLoading)loadVocabularyImpact().catch(error=>{state.impactError=error.message;state.impactLoading=false;renderVocabularyImpact();});
  if(state.view==="vokabular")notice("Gemeinsame Begriffe geladen. Wähle einen Begriff, um seine fachliche Bedeutung zu lesen.","quiet");
}
async function loadVocabularyImpact(){
  state.impactLoading=true;state.impactError="";renderVocabularyImpact();
  try{
    const result=await api("/api/vocabulary/impact");
    if(result.case_count!==state.cases.length || !result.terms)throw new Error("Der Fallabgleich ist unvollständig.");
    state.vocabularyImpact=result;
  }catch(error){state.impactError=error.message;throw error;}
  finally{state.impactLoading=false;renderVocabularyImpact();}
}
function renderVocabularyImpact(){
  const root=$("vocab-impact-content");if(!root)return;root.replaceChildren();
  const term=selectedTerm();
  if(!term){root.append(element("p","Wähle zuerst einen Begriff aus.","empty"));return;}
  if(state.impactLoading){root.append(element("p","Verwendung im aktuellen Katalogstand wird ermittelt …","empty"));return;}
  if(state.impactError){root.append(element("p","Die Verwendung konnte nicht geladen werden: "+state.impactError,"review-problem"));return;}
  if(!state.vocabularyImpact){root.append(element("p","Die Verwendung wurde noch nicht geladen.","empty"));return;}
  const records=state.vocabularyImpact.terms[term.id] || [];
  const total=records.reduce((sum,item)=>sum+item.count,0);
  root.append(element("strong",records.length===0 ? "Noch in keinem Fallmodul verwendet" : `${records.length} von ${state.cases.length} Fällen · ${total} technische Verwendungen`,"impact-summary"));
  const sha=state.vocabularyImpact.source_ref;
  root.append(element("p",/^[0-9a-f]{40}$/.test(sha) ? "Berechnet aus dem aktuellen Katalogstand." : "Berechnet aus der lokalen Fallvorlage.","impact-source"));
  root.append(element("p","Gezählt werden Begriffe und Beziehungen in den Fallvorlagen. Diese Übersicht ersetzt keine notarielle Bewertung der Folgen.","context-help"));
  if(records.length){
    const list=element("div",undefined,"impact-cases");
    records.sort((a,b)=>(state.cases.find(item=>item.slug===a.slug)?.title || a.slug).localeCompare(state.cases.find(item=>item.slug===b.slug)?.title || b.slug,"de"));
    records.forEach(item=>{
      const title=state.cases.find(entry=>entry.slug===item.slug)?.title || item.slug;
      const button=element("button",undefined,"impact-case");button.type="button";
      button.append(element("span",title),element("small",`${item.count} ${item.count===1 ? "Verwendung" : "Verwendungen"} · Fall öffnen →`));
      button.addEventListener("click",()=>loadCase(item.slug).catch(error=>notice(error.message,"error")));
      list.append(button);
    });
    root.append(list);
  }
}
function vocabularyReference(value){
  if(!value)return "";
  if(value==="skos:Concept")return "Allgemeiner Fachbegriff";
  const datatypes={"xsd:string":"Text","xsd:boolean":"Ja oder Nein","xsd:integer":"Ganze Zahl","xsd:date":"Datum","xsd:dateTime":"Datum und Uhrzeit","xsd:anyURI":"Webadresse"};
  if(datatypes[value])return datatypes[value];
  if(value.startsWith("n8:"))return state.vocabulary.terms.find(item=>item.id===value.slice(3))?.label || value;
  return value;
}
function renderVocabulary(updateForm=true){
  if(!state.vocabulary)return;
  const root=$("vocab-list");root.replaceChildren();
  const query=$("vocab-search").value.trim().toLocaleLowerCase("de");
  const terms=state.vocabulary.terms.filter(item=>!query || (item.label+" "+item.id+" "+item.comment).toLocaleLowerCase("de").includes(query));
  const headings={class:"Begriffsklassen",object_property:"Verbindungen",datatype_property:"Merkmale"};
  for(const kind of ["class","object_property","datatype_property"]){
    const matches=terms.filter(item=>item.kind===kind).sort((a,b)=>a.label.localeCompare(b.label,"de"));
    if(!matches.length)continue;
    root.append(element("h4",headings[kind]));
    matches.forEach(item=>{
      const button=element("button",item.label,"vocab-item"+(item.id===state.vocabSelected?" active":""));button.type="button";
      button.dataset.contextTerm=item.id;
      button.setAttribute("aria-haspopup","menu");
      button.append(element("small",item.id));button.addEventListener("click",()=>{state.vocabSelected=item.id;state.vocabEditing=false;state.vocabNew=false;renderVocabulary();});root.append(button);
    });
  }
  if(!terms.length)root.append(element("p","Kein Begriff gefunden.","empty"));
  if(updateForm)renderVocabularyDetail();
}
function option(select,value,label){const item=element("option",label);item.value=value;select.append(item);}
function setVocabularyOptions(term){
  const classes=state.vocabulary.terms.filter(item=>item.kind==="class").sort((a,b)=>a.label.localeCompare(b.label,"de"));
  const choices=[["","Keine Angabe"],["skos:Concept","Allgemeiner Fachbegriff"],...classes.map(item=>["n8:"+item.id,item.label])];
  for(const id of ["vocab-parent","vocab-domain","vocab-range"]){
    const select=$(id);select.replaceChildren();
    const entries=id==="vocab-range" && term.kind==="datatype_property" ? [["","Keine Angabe"],...["string","boolean","integer","date","dateTime","anyURI"].map(name=>["xsd:"+name,name])] : choices;
    entries.forEach(([value,label])=>option(select,value,label));
    select.value=term[id.replace("vocab-","")] || "";
  }
  for(const [id,hidden] of [["vocab-parent",term.kind!=="class"],["vocab-domain",term.kind==="class"],["vocab-range",term.kind==="class"]]){
    $(id).hidden=hidden;$(id).previousElementSibling.hidden=hidden;
  }
}
function renderVocabularyDetail(){
  const term=selectedTerm(), read=$("vocab-read");read.replaceChildren();
  $("vocab-form").hidden=!state.vocabEditing;
  $("vocab-edit").hidden=!term || !state.ontologyMaintainer || state.vocabEditing || (state.branch!=="main" && state.purpose!=="vocabulary");
  if(!term){$("vocab-title").textContent="Begriff auswählen";renderVocabularyImpact();return;}
  $("vocab-title").textContent=term.label;
  if(!state.vocabEditing){
    read.append(element("span",vocabularyKinds[term.kind],"node-meta"));
    const facts=[["Erläuterung",term.comment],["Oberklasse",term.parent],["Gilt für",term.domain],["Ziel oder Datentyp",term.range]];
    facts.filter(([,value])=>value).forEach(([name,value])=>{const box=element("div",undefined,"node-fact");box.append(element("strong",name),element("p",name==="Erläuterung"?value:vocabularyReference(value)));read.append(box);});
    read.append(element("p","Kennung: "+term.id,"node-provenance"));
    renderVocabularyImpact();
    return;
  }
  $("vocab-id").value=term.id;$("vocab-id").readOnly=!state.vocabNew;
  $("vocab-kind").value=term.kind;$("vocab-kind").disabled=!state.vocabNew;
  $("vocab-label").value=term.label;$("vocab-comment").value=term.comment;
  setVocabularyOptions(term);
  renderVocabularyImpact();
}
async function editVocabulary(newTerm=false){
  if(!state.ontologyMaintainer)throw new Error("Die Pflege gemeinsamer Begriffe benötigt eine zusätzliche fachliche Berechtigung für diesen Modellbestand.");
  const selected=state.vocabSelected;
  if(state.branch==="main")await beginBranch("vocabulary");
  if(state.purpose!=="vocabulary")throw new Error("Bitte die laufende Falländerung zuerst zur Prüfung einreichen.");
  if(selected && state.vocabulary.terms.some(item=>item.id===selected))state.vocabSelected=selected;
  if(newTerm){
    let index=1;while(state.vocabulary.terms.some(item=>item.id===`NeuerBegriff${index}`))index++;
    const term={id:`NeuerBegriff${index}`,kind:"class",label:"Neuer Begriff",comment:"",parent:"",domain:"",range:""};
    state.vocabulary.terms.push(term);state.vocabSelected=term.id;state.vocabNew=true;dirty();
  }else state.vocabNew=false;
  state.vocabEditing=true;renderVocabulary();
}
async function submitVocabulary(){
  try{
    if(state.dirty)throw new Error("Bitte zuerst die Änderung speichern.");
    const result=await api("/api/vocabulary/review",{reason:$("vocab-reason").value,source:$("vocab-source").value});
    recovery.clear();$("vocab-reason").value="";$("vocab-source").value="";
    $("vocab-pr-link").href=result.url;$("vocab-pr-link").hidden=false;
    state.branch=result.branch;state.purpose=result.purpose;state.vocabulary=null;await loadVocabulary(true);refreshBranch();
    notice("Vokabularänderung zur notariellen Fachprüfung eingereicht.","success");
  }catch(error){notice(error.message,"error");}
}
function setView(view) {
  if(state.dirty && (view==="vokabular") !== (state.view==="vokabular")) {notice("Bitte zuerst die offenen Änderungen speichern.","error");return;}
  if(view!=="fall")office.graphEdit=false;
  if(view!=="hilfe")office.lastView=view;
  state.view=view;
  viewSequence++;
  if(view!=="fall")closeGraphInspector();
  document.body.classList.toggle("review-mode",view==="fachpruefung" || view==="vokabular");
  if(view==="bausteine" && state.current && !state.selected){
    state.selected=state.current.nodes[0]?.id || null;
    renderNodes();renderNodeForm();renderGraph();renderGraphList();renderRelationContext();
  }
  if(view==="verbindungen" && state.current){renderRelationContext();fillNodeSelects();renderGraph();}
  if(view==="fachpruefung" && state.user)loadReviewQueue().catch(error=>notice(error.message,"error"));
  if(view==="vokabular" && !state.vocabulary)loadVocabulary().catch(error=>notice(error.message,"error"));
  if(state.current) window.history.replaceState(null,"",`?case=${encodeURIComponent(state.current.slug)}#${view}`);
  document.querySelectorAll("[data-view]").forEach(panel=>{panel.hidden=panel.dataset.view!==view;});
  document.querySelectorAll("[data-view-button]").forEach(button=>{
    if(button.dataset.viewButton===view) button.setAttribute("aria-current","page");
    else button.removeAttribute("aria-current");
  });
  refreshBranch();
  renderCaseList();
}
async function loadCase(slug, view="fall", navigation=viewSequence) {
  if(saveFlow.pending){$("case-select").value=state.current.slug;notice("Bitte den laufenden Speichervorgang abwarten.");return;}
  if (recovery.hasInputs && !window.confirm("Ungespeicherte Eingaben verwerfen und anderen Fall öffnen?")) {
    $("case-select").value = state.current.slug;
    return;
  }
  const sequence=++caseLoadSequence;
  let model;
  try{model=await api("/api/cases/" + encodeURIComponent(slug));}
  catch(error){if(sequence!==caseLoadSequence)return;if(state.current)$("case-select").value=state.current.slug;throw error;}
  if(sequence!==caseLoadSequence)return;
  if(recovery.hasInputs){recovery.clear();$("change-reason").value="";$("change-source").value="";}
  state.current = model;
  recovery.setBase(model,"case");
  state.selected = null;
  state.graphFocused=false;
  state.graphMode="linked";
  state.graphZoom=1;
  closeGraphInspector();
  $("graph-scope").setAttribute("aria-pressed","false");
  $("graph-scope").textContent="Umfeld zeigen";
  state.nodeEditing = false;
  state.dirty = false;
  $("overview-editor").hidden=true;
  $("edit-overview").textContent="Beschreibung und Quellen bearbeiten";
  $("review-link").hidden=true;
  $("case-history").open=false;state.caseHistory=null;state.historyTarget="";$("history-preview").hidden=true;
  if($("case-sources").open)$("case-sources").close();
  if($("case-node-search").open)$("case-node-search").close();
  $("graph-query").value="";
  $("edge-from").value="";$("edge-to").value="";
  if(viewSequence===navigation)setView(view);
  else refreshBranch();
  $("case-title").textContent = state.current.title;
  $("summary").value = state.current.summary;
  $("sources").value = state.current.sources.join("\n");
  $("nac-source").href = state.current.nac_source;
  $("bpmn-source").href = state.current.bpmn_source;
  $("case-select").value=slug;
  renderCaseList();renderOverview();
  renderAll();
  notice(state.hosted && state.branch!=="main" && state.purpose==="case" && !caseEditable() ? "Dieser Fall ist im Lesemodus. Lege den geöffneten Entwurf ab, um hier eine Änderung zu beginnen." : "Fall geladen. Die fachlichen Zusammenhänge sind direkt sichtbar.","quiet");
}
function renderAll() {
  renderCaseList();
  renderGraph();
  renderGraphList();
  renderGraphSearch();
  renderNodes();
  renderNodeForm();
  renderEdges();
  renderRelationContext();
  fillNodeSelects();
}
function nodeContext(control,node) {
  if(!node)return;
  control.dataset.contextNode=node.id;
  control.dataset.contextCase=state.current.slug;
  control.setAttribute("aria-haspopup","menu");
}
async function beginNodeEdit(id=state.selected, graph=office.graphEdit) {
  if(nodeEditPending || saveFlow.pending)return;
  const slug=state.current?.slug;
  if(!state.current?.nodes.some(node=>node.id===id))return;
  if(state.dirty && state.view==="vokabular")throw new Error("Bitte zuerst die offenen Änderungen an gemeinsamen Begriffen speichern.");
  nodeEditPending=true;refreshBranch();
  try {
    if(state.branch==="main")await beginBranch();
    if(state.current?.slug!==slug || !caseEditable())throw new Error("Dieser Entwurf gehört zu einem anderen Fall. Lege ihn zuerst ab.");
    office.graphEdit=graph;
    selectNode(id);state.nodeEditing=true;renderNodeForm();renderOffice();
    $("node-form").querySelector("input:not([readonly]):not([disabled])")?.focus({preventScroll:true});
  } finally {nodeEditPending=false;refreshBranch();}
}
function renderRelationContext() {
  const root=$("relation-context");root.replaceChildren();
  const node=state.current.nodes.find(item=>item.id===state.selected);
  if(!node){root.append(element("p","Bitte einen Baustein wählen.","empty"));return;}
  $("inspector-title").textContent=displayNodeLabel(node);
  const panel=element("div",undefined,"relation-focus-card");
  const type=groups.find(([key])=>key===node.category)?.[1] || "Baustein";
  panel.append(element("p",type,"relation-type"));
  if(node.question)panel.append(element("p",node.question,"relation-question"));
  const open=element("button","Inhalt ansehen →","relation-open");open.type="button";
  open.addEventListener("click",()=>{closeGraphInspector();selectNode(node.id);});panel.append(open);
  root.append(panel);
  const relevant=state.current.edges.filter(edge=>edge.from===node.id || edge.to===node.id);
  const links=element("section",undefined,"relation-links");root.append(links);
  links.append(element("h3",`Direkte Verbindungen · ${relevant.length}`));
  if(!relevant.length){links.append(element("p","Für diesen Baustein sind noch keine direkten Verbindungen erfasst.","empty"));return;}
  relevant.forEach(edge=>{
    const other=edge.from===node.id ? edge.to : edge.from;
    const outgoing=edge.from===node.id;
    const row=element("div",undefined,"relation-card");
    row.append(element("span",outgoing ? "Geht von diesem Baustein aus" : "Führt zu diesem Baustein","relation-direction"));
    row.append(element("strong",relations[edge.type] || edge.type));
    const button=element("button",nodeLabel(other),"relation-target");button.type="button";
    nodeContext(button,state.current.nodes.find(item=>item.id===other));
    button.addEventListener("click",()=>{state.selected=other;renderAll();$("inspector-title").focus({preventScroll:true});});
    row.append(button);links.append(row);
  });
}
function renderGraph() {
  const canvas = $("graph");
  canvas.replaceChildren();
  if(!state.current.edges.length)state.graphMode="all";
  const linked=new Set(state.current.edges.flatMap(edge=>[edge.from,edge.to]));
  const orphans=state.current.nodes.filter(node=>!linked.has(node.id));
  $("graph-status").textContent=state.current.edges.length ? state.current.edges.length+" Verbindungen · "+linked.size+" verknüpfte Bausteine"+(orphans.length ? " · "+orphans.length+" ohne Verbindung" : "") : state.current.nodes.length+" Bausteine · noch keine Verbindungen";
  $("graph-linked").setAttribute("aria-pressed",String(state.graphMode==="linked"));
  $("graph-all").setAttribute("aria-pressed",String(state.graphMode==="all"));
  $("graph-linked").disabled=!state.current.edges.length;
  $("graph-zoom-reset").textContent=Math.round(state.graphZoom*100)+" %";
  $("graph-zoom-out").disabled=state.graphZoom<=0.85;
  $("graph-zoom-in").disabled=state.graphZoom>=1.5;
  renderGraphOrphans(orphans);
  const selected=$("graph-inspector").hidden ? null : state.current.nodes.find(node=>node.id===state.selected);
  $("graph-scope").hidden=!selected;
  const focused=!!(state.graphFocused && selected);
  const positions=new Map();
  let nodes, edges, width, height, nodeWidth;
  if(focused){
    edges=state.current.edges.filter(edge=>edge.from===selected.id || edge.to===selected.id);
    const byId=new Map(state.current.nodes.map(node=>[node.id,node]));
    const incoming=[...new Set(edges.filter(edge=>edge.to===selected.id).map(edge=>edge.from))].map(id=>byId.get(id)).filter(Boolean).sort((a,b)=>a.label.localeCompare(b.label,"de"));
    const incomingIds=new Set(incoming.map(node=>node.id));
    const outgoing=[...new Set(edges.filter(edge=>edge.from===selected.id).map(edge=>edge.to))].filter(id=>!incomingIds.has(id)).map(id=>byId.get(id)).filter(Boolean).sort((a,b)=>a.label.localeCompare(b.label,"de"));
    nodes=[...incoming,selected,...outgoing];
    nodeWidth=210;
    const centerX=incoming.length ? 275 : 20;
    const rightX=centerX+255;
    width=outgoing.length ? rightX+nodeWidth+20 : centerX+nodeWidth+20;
    const rows=Math.max(incoming.length,outgoing.length,1);
    height=Math.max(160,138+(rows-1)*76);
    positions.set(selected.id,{x:centerX,y:50+(rows-1)*38});
    incoming.forEach((node,index)=>positions.set(node.id,{x:20,y:50+index*76}));
    outgoing.forEach((node,index)=>positions.set(node.id,{x:rightX,y:50+index*76}));
  }else{
    nodes=state.graphMode==="linked" && state.current.edges.length ? state.current.nodes.filter(node=>linked.has(node.id)) : state.current.nodes;
    edges=state.current.edges;
    width=1000;nodeWidth=180;
    const ordered=groups.map(([key])=>nodes.filter(node=>node.category===key).sort((a,b)=>a.label.localeCompare(b.label,"de")));
    height=Math.max(230,105+Math.max(...ordered.map(group=>group.length),1)*72);
    ordered.forEach((list,column)=>{
      const x=20+column*195;
      const heading=svg("text",{x,y:28,class:"graph-heading"});
      heading.textContent=groups[column][1]+" ("+list.length+")";
      canvas.append(heading);
      list.forEach((node,row)=>positions.set(node.id,{x,y:52+row*72}));
    });
  }
  canvas.dataset.scope=focused?"focused":"all";
  canvas.setAttribute("viewBox","0 0 "+width+" "+height);
  canvas.style.height=Math.round(height*state.graphZoom)+"px";
  canvas.style.width=Math.round(width*state.graphZoom)+"px";
  canvas.style.minWidth="0";
  const defs=svg("defs");
  const marker=svg("marker",{id:"arrow",markerWidth:"8",markerHeight:"8",refX:"7",refY:"4",orient:"auto"});
  marker.append(svg("path",{d:"M 0 0 L 8 4 L 0 8 z",fill:"#6b929f"}));
  defs.append(marker);canvas.append(defs);
  edges.forEach(edge=>{
    const a=positions.get(edge.from),b=positions.get(edge.to);
    if(!a||!b)return;
    let pathData;
    if(focused){
      const forward=b.x>=a.x;
      const sx=a.x+(forward?nodeWidth:0),sy=a.y+28;
      const tx=b.x+(forward?0:nodeWidth),ty=b.y+28;
      const bend=(tx-sx)/2;
      pathData="M "+sx+" "+sy+" C "+(sx+bend)+" "+sy+", "+(tx-bend)+" "+ty+", "+tx+" "+ty;
    }else{
      const sx=a.x+nodeWidth,sy=a.y+28,tx=b.x,ty=b.y+28;
      const bend=Math.max(35,Math.abs(tx-sx)/2);
      pathData="M "+sx+" "+sy+" C "+(sx+bend)+" "+sy+", "+(tx-bend)+" "+ty+", "+tx+" "+ty;
    }
    const active=!selected || edge.from===selected.id || edge.to===selected.id;
    const path=svg("path",{d:pathData,class:"graph-edge"+(active?"":" dimmed"),"marker-end":"url(#arrow)"});
    const title=svg("title");
    title.textContent=nodeLabel(edge.from)+" "+(relations[edge.type]||edge.type)+" "+nodeLabel(edge.to);
    path.append(title);canvas.append(path);
  });
  nodes.forEach(node=>{
    const position=positions.get(node.id);
    if(!position)return;
    const groupIndex=groups.findIndex(([key])=>key===node.category);
    const category=groups[groupIndex<0?0:groupIndex];
    const chosen=node.id===state.selected;
    const connectedToSelection=!selected || chosen || state.current.edges.some(edge=>(edge.from===selected.id && edge.to===node.id)||(edge.to===selected.id && edge.from===node.id));
    const group=svg("g",{class:"graph-node"+(chosen?" selected":"")+(linked.has(node.id)?"":" disconnected")+(connectedToSelection?"":" dimmed"),tabindex:"0",role:"button","aria-label":displayNodeLabel(node)+"; "+category[1]+(linked.has(node.id)?"":"; bisher ohne Verbindung")});
    nodeContext(group,node);
    group.append(svg("rect",{x:position.x,y:position.y,width:nodeWidth,height:56,rx:4,fill:category[2],stroke:category[3]}));
    const caption=svg("text",{x:position.x+10,y:position.y+22});
    const limit=focused?26:20;
    const lines=[""];
    displayNodeLabel(node).split(/\s+/).forEach(word=>{
      const line=lines.length-1;
      const candidate=lines[line] ? lines[line]+" "+word : word;
      if(candidate.length>limit && lines[line])lines.push(word);
      else lines[line]=candidate;
    });
    const visibleLines=lines.slice(0,2);
    if(lines.length>2)visibleLines[1]=visibleLines[1].slice(0,limit-1)+"…";
    visibleLines.forEach((line,index)=>{
      const tspan=svg("tspan",{x:position.x+10,dy:index?17:0});
      tspan.textContent=line.length>limit?line.slice(0,limit-1)+"…":line;
      caption.append(tspan);
    });
    group.append(caption);
    group.addEventListener("click",()=>focusGraphNode(node.id));
    group.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();focusGraphNode(node.id);}});
    canvas.append(group);
  });
}
function renderGraphOrphans(orphans) {
  const section=$("graph-orphans");
  section.hidden=!orphans.length || state.graphMode==="all" || !state.current.edges.length;
  if(section.hidden)return;
  $("graph-orphans-title").textContent=orphans.length+" Bausteine ohne Verbindung";
  const list=$("graph-orphans-list");list.replaceChildren();
  orphans.forEach(node=>{
    const button=element("button",displayNodeLabel(node),"graph-orphan");button.type="button";
    nodeContext(button,node);
    button.addEventListener("click",()=>focusGraphNode(node.id));list.append(button);
  });
}
function renderGraphList() {
  const root=$("graph-list");root.replaceChildren();
  const selected=state.current.nodes.find(node=>node.id===state.selected);
  const linked=new Set(state.current.edges.flatMap(edge=>[edge.from,edge.to]));
  const visible=state.graphFocused && selected ? new Set([selected.id,...state.current.edges.filter(edge=>edge.from===selected.id || edge.to===selected.id).map(edge=>edge.from===selected.id?edge.to:edge.from)]) : state.graphMode==="linked" && state.current.edges.length ? linked : null;
  groups.forEach(([key,label,fill,border])=>{
    const nodes=state.current.nodes.filter(node=>node.category===key && (!visible || visible.has(node.id))).sort((a,b)=>a.label.localeCompare(b.label,"de"));
    if(!nodes.length)return;
    const section=element("section",undefined,"graph-list-group");
    section.style.setProperty("--group-fill",fill);section.style.setProperty("--group-border",border);
    section.append(element("h3",label+" · "+nodes.length));
    nodes.forEach(node=>{
      const connections=state.current.edges.filter(edge=>edge.from===node.id || edge.to===node.id).length;
      const button=element("button",undefined,"graph-list-node"+(node.id===state.selected?" selected":""));button.type="button";
      nodeContext(button,node);
      button.append(element("span",displayNodeLabel(node)),element("small",connections+" "+(connections===1?"Verbindung":"Verbindungen")+" · Details ansehen →"));
      button.addEventListener("click",()=>focusGraphNode(node.id));section.append(button);
    });root.append(section);
  });
}
function renderNodes() {
  const root = $("node-list"); root.replaceChildren();
  const query = $("node-search").value.trim().toLocaleLowerCase("de");
  const category = $("node-category").value;
  let count = 0;
  groups.forEach(([key,title]) => {
    const list = state.current.nodes.filter(node => node.category === key && (!category || category === key) && (!query || (node.label + " " + node.id + " " + node.question).toLocaleLowerCase("de").includes(query))).sort((a,b) => a.label.localeCompare(b.label,"de"));
    if (!list.length) return;
    count += list.length;
    const box = element("div",undefined,"node-group");
    box.append(element("h3",title + " · " + list.length));
    list.forEach(node => {
      const button = element("button",displayNodeLabel(node),"node-row" + (state.selected === node.id ? " active" : ""));
      button.type = "button";
      nodeContext(button,node);
      button.addEventListener("click",() => selectNode(node.id));
      box.append(button);
    });
    root.append(box);
  });
  $("node-count").textContent = `${count} von ${state.current.nodes.length} Bausteinen`;
  if (!count) root.append(element("p","Keine Bausteine gefunden. Suche oder Art ändern.","empty"));
}
function selectNode(id) {
  state.selected = id;
  state.nodeEditing = false;
  setView(office.graphEdit?"fall":"bausteine");
  renderNodes(); renderNodeForm(); renderGraph(); renderGraphList(); renderRelationContext(); fillNodeSelects();
}
function closeGraphInspector() {
  $("graph-inspector").hidden=true;
  $("graph-stage").classList.remove("has-selection");
  state.graphFocused=false;
}
function focusGraphNode(id) {
  state.selected=id;
  state.nodeEditing=false;
  const linked=new Set(state.current.edges.flatMap(edge=>[edge.from,edge.to]));
  if(!linked.has(id))state.graphMode="all";
  state.graphFocused=true;
  $("graph-scope").setAttribute("aria-pressed","true");
  $("graph-scope").textContent="Ganzen Fall zeigen";
  $("graph-inspector").hidden=false;
  $("graph-stage").classList.add("has-selection");
  renderAll();
  $("graph-stage").querySelector(".graph-wrap").scrollTop=0;
  renderCaseList();
  $("inspector-title").focus({preventScroll:true});
}
function field(root, label, value, onChange, multiline = false, hint = "") {
  const wrap = element("div");
  const caption = element("label",label + (hint ? " · " + hint : ""));
  const control = element(multiline ? "textarea" : "input");
  control.value = value ?? "";
  control.disabled=!caseEditable();
  if (multiline) control.rows = 3;
  control.addEventListener("input",() => {onChange(control.value);dirty();});
  caption.append(control); wrap.append(caption); root.append(wrap);
  return control;
}
function renderNodeForm() {
  const root = $("node-form"); root.replaceChildren();
  const read = $("node-read"); read.replaceChildren();
  const node = state.current.nodes.find(item => item.id === state.selected);
  root.hidden = !node || !state.nodeEditing;
  read.hidden = !!node && state.nodeEditing;
  $("edit-node").hidden = !node;
  $("edit-node").textContent = state.nodeEditing ? "Lesen" : "Bearbeiten";
  $("delete-node").hidden = !node || !state.nodeEditing || !node.id.startsWith("local.");
  $("detail-title").textContent = node ? displayNodeLabel(node) : "Baustein auswählen";
  if (!node) {read.append(element("p","Wähle links oder im Bild einen Baustein aus.","empty"));return;}
  const type=groups.find(([key])=>key===node.category)?.[1] || "Baustein";
  read.append(element("p",type + " · " + (node.id.startsWith("local.") ? "Neu ergänzter Baustein" : "Aus der NaC-Vorlage übernommen"),"node-meta"));
  const facts=[
    ["Fachfrage",node.question],
    ["Abschnitt der Vorlage",node.section],
    ["Erläuterung",node.detail],
    ["Dokumentquelle",node.document_source]
  ];
  let shown=0;
  for(const [label,value] of facts){if(!value) continue; const block=element("div",undefined,"node-fact");block.append(element("strong",label),element("p",value));read.append(block);shown++;}
  if(node.options.length){
    const block=element("div",undefined,"node-fact");block.append(element("strong","Auswahlwerte der NaC-Vorlage"));
    block.append(element("p","Für diese Auswahl fehlen derzeit fachlich geprüfte, lesbare Bezeichnungen."));read.append(block);shown++;
  }
  if(node.contains_personal_data===true){const block=element("div",undefined,"node-fact");block.append(element("strong","Datenschutz"),element("p","Dieser Baustein kann Personendaten betreffen."));read.append(block);shown++;}
  if(!shown) read.append(element("p","Zu diesem Baustein sind noch keine weiteren fachlichen Angaben erfasst.","empty"));
  if(node.owner_role || node.privacy_class || node.required_for.length){
    const extra=element("details",undefined,"node-provenance");extra.append(element("summary","Weitere Angaben aus der NaC-Vorlage"));
    if(node.owner_role)extra.append(element("p","Rollenkennung: "+node.owner_role));
    if(node.privacy_class)extra.append(element("p","Datenschutzkennung: "+node.privacy_class));
    if(node.required_for.length)extra.append(element("p","Benötigt für: "+node.required_for.join(", ")));
    read.append(extra);
  }
  const id=field(root,"Kennung",node.id,()=>{});id.readOnly=true;
  const label = field(root,"Bezeichnung",node.label,value => {
    node.label=value; $("detail-title").textContent=displayNodeLabel(node);renderNodes();renderGraph();renderGraphList();renderGraphSearch();renderEdges();renderRelationContext();fillNodeSelects();
  });
  label.maxLength=2000;
  const categoryWrap=element("div");
  const categoryLabel=element("label","Bausteintyp");
  const categorySelect=element("select");
  groups.forEach(([key,title])=>{const option=element("option",title);option.value=key;categorySelect.append(option);});
  categorySelect.value=node.category;
  categorySelect.disabled=!caseEditable();
  categorySelect.addEventListener("change",()=>{node.category=categorySelect.value;dirty();renderNodes();renderGraph();renderGraphList();});
  categoryLabel.append(categorySelect);categoryWrap.append(categoryLabel);root.append(categoryWrap);
  const status=field(root,node.id.startsWith("local.") ? "Pflegestatus des lokalen Entwurfs" : "Status der NaC-Vorlage",node.status,value=>node.status=value);
  if (!node.id.startsWith("local.")) status.readOnly=true;
  field(root,"Offene Fachfrage",node.question,value=>node.question=value,true);
  field(root,"Abschnitt der Vorlage",node.section,value=>node.section=value);
  field(root,"Fachliche Erläuterung",node.detail,value=>node.detail=value,true);
  const advanced=element("details",undefined,"advanced-fields");
  advanced.append(element("summary","Weitere Angaben für die Datenpflege"));
  root.append(advanced);
  const grid=element("div",undefined,"grid");advanced.append(grid);
  field(grid,"Verantwortliche Rolle",node.owner_role,value=>node.owner_role=value);
  field(grid,"Datenschutzklasse",node.privacy_class,value=>node.privacy_class=value);
  field(advanced,"Benötigt für",node.required_for.join("\n"),value=>node.required_for=value.split("\n").map(v=>v.trim()).filter(Boolean),true,"eine Angabe pro Zeile");
  field(advanced,"Entscheidungsoptionen",node.options.join("\n"),value=>node.options=value.split("\n").map(v=>v.trim()).filter(Boolean),true,"eine Option pro Zeile");
  field(advanced,"Dokumentquelle",node.document_source,value=>node.document_source=value);
  const privacy=element("label","Kann Personendaten enthalten?");
  const select=element("select");
  select.disabled=!caseEditable();
  [["","Keine Angabe"],["true","Ja"],["false","Nein"]].forEach(([value,text])=>{const option=element("option",text);option.value=value;select.append(option);});
  select.value=node.contains_personal_data === null ? "" : String(node.contains_personal_data);
  select.addEventListener("change",()=>{node.contains_personal_data=select.value === "" ? null : select.value === "true";dirty();});
  privacy.append(select);advanced.append(privacy);
  $("delete-node").disabled=!caseEditable();
}
function fillNodeSelects() {
  for (const id of ["edge-from","edge-to"]) {
    const node=state.current.nodes.find(item=>item.id===$(id).value);
    if(!node)$(id).value="";
    $(id+"-choose").textContent=node ? displayNodeLabel(node) : id==="edge-from" ? "Ausgang wählen" : "Ziel wählen";
  }
}
function renderEdges() {
  const root=$("edge-list");root.replaceChildren();
  $("edge-count").textContent=state.current.edges.length+" "+(state.current.edges.length===1?"Verbindung":"Verbindungen");
  if(!state.current.edges.length)root.append(element("p","Für diesen Fall sind noch keine Verbindungen erfasst.","empty"));
  state.current.edges.forEach((edge,index)=>{
    const editable=caseEditable();
    const row=element(editable ? "div" : "button",undefined,"edge-row"+(editable ? "" : " edge-open-row"));
    if(!editable){row.type="button";row.addEventListener("click",()=>{setView("fall");focusGraphNode(edge.from);});}
    row.append(element("span",nodeLabel(edge.from)));
    row.append(element("span",relations[edge.type],"edge-type"));
    row.append(element("span",nodeLabel(edge.to)));
    if(editable){
      const remove=element("button","Entfernen","danger");remove.type="button";
      remove.addEventListener("click",()=>{state.current.edges.splice(index,1);dirty();renderEdges();renderGraph();renderGraphList();});
      row.append(remove);
    }else row.append(element("span","Im Graphen ↗","edge-open-label"));
    root.append(row);
  });
}
function setSavePending(phase) {
  saveFlow.pending=phase;
  $("change-preview").setAttribute("aria-busy",String(phase==="save"));
  $("confirm-save").disabled=!!phase || !saveFlow.preview?.changed;
  $("confirm-save").textContent=phase==="save" ? "Wird gespeichert …" : "Speichern";
  for(const id of ["close-preview","cancel-preview"])$(id).disabled=phase==="save";
  refreshBranch();
}
function closeSavePreview() {
  if(saveFlow.pending==="save")return;
  $("change-preview").close();saveFlow.preview=null;
  if(state.dirty)notice("Änderungen sind noch nicht gespeichert.");
}
function previewStatus(message, error=false) {
  $("preview-status").hidden=!message;
  $("preview-status").textContent=message;
  $("preview-status").className=error ? "notice error" : "";
}
function previewIsCurrent(preview) {
  return state.branch===preview.branch && (preview.vocabulary ? state.vocabulary : state.current)===preview.subject && JSON.stringify(preview.subject)===JSON.stringify(preview.snapshot);
}
async function save() {
  if(saveFlow.pending || $("change-preview").open || $("input-recovery").open)return;
  try {
    if (state.branch === "main") throw new Error("Bitte zuerst unter Bearbeiten einen Entwurf erstellen.");
    if(state.view!=="vokabular" && !caseEditable())throw new Error("Dieser Entwurf gehört zu einem anderen Fall. Lege ihn zuerst ab.");
    const vocabulary=state.view==="vokabular";
    if((vocabulary && state.purpose!=="vocabulary") || (!vocabulary && state.purpose!=="case"))throw new Error("Dieser Arbeitszweig gehört zu einem anderen Arbeitsbereich.");
    const subject=vocabulary ? state.vocabulary : state.current;
    const preview={vocabulary,subject,branch:state.branch,snapshot:structuredClone(subject),path:vocabulary ? "/api/vocabulary" : "/api/cases/" + state.current.slug};
    saveFlow.preview=null;previewStatus("");caseLoadSequence++;
    setSavePending("preview");
    notice("Änderungsvorschau wird vorbereitet …");
    const result=await api(preview.path+"/preview",preview.snapshot);
    if(!previewIsCurrent(preview))throw new Error("Die Eingaben haben sich während der Vorschau geändert. Bitte erneut Speichern wählen.");
    saveFlow.preview={...preview,changed:result.changed};
    $("preview-description").textContent="Prüfe die fachlichen Änderungen vor dem Speichern. Danach kannst du sie zur notariellen Fachprüfung einreichen.";
    const list=$("preview-list");list.replaceChildren();
    result.changes.forEach(change=>list.append(element("li",change)));
    window.EditorComparison.render($("preview-comparison"),result.comparison,relations);
    if(!result.changed) list.append(element("li","Keine fachliche Änderung erkannt."));
    $("confirm-save").disabled=!result.changed;
    $("change-preview").showModal();
    notice("Bitte die Vorschau prüfen und Speichern bestätigen.");
  } catch (error) {notice(error.message,"error");}
  finally{setSavePending("");}
}
async function confirmSave() {
  const preview=saveFlow.preview;
  if(saveFlow.pending || !preview?.changed)return;
  if(!previewIsCurrent(preview)){closeSavePreview();notice("Die Eingaben haben sich geändert. Bitte erneut Speichern wählen und die aktuelle Vorschau prüfen.","error");return;}
  setSavePending("save");previewStatus("Änderungen werden gespeichert …");
  notice("Änderungen werden gespeichert …");
  try {
    const {vocabulary,subject}=preview;
    const result=await api(preview.path+"/save",preview.snapshot);
    const unchanged=previewIsCurrent(preview);
    subject.revision=result.revision;
    if(result.expected_ref) subject.expected_ref=result.expected_ref;
    if(unchanged)state.dirty=false;
    recovery.setBase({...preview.snapshot,revision:result.revision,expected_ref:result.expected_ref||preview.snapshot.expected_ref},vocabulary?"vocabulary":"case");
    if(unchanged)recovery.clear();recovery.capture();
    if(result.changed && !vocabulary){
      state.caseIndex=null;state.caseIndexPromise=null;
      if($("case-index-query").value.trim().length>=2)loadCaseIndex().catch(()=>{});
    }
    $("change-preview").close();
    saveFlow.preview=null;
    notice(!unchanged ? "Geprüfte Fassung gespeichert. Neuere Eingaben sind noch nicht gespeichert." : result.changed ? (vocabulary ? "Gemeinsame Begriffe gespeichert. Reiche die Änderung nun zur Fachprüfung ein." : "Fallvorlage gespeichert. Reiche die Änderung nun zur Fachprüfung ein.") : "Keine Änderungen zu speichern.","success");
  } catch (error) {previewStatus("Speichern fehlgeschlagen: "+error.message,true);notice(error.message,"error");}
  finally{setSavePending("");if($("change-preview").open)$("confirm-save").focus();}
}
async function logout() {
  if(saveFlow.pending){notice("Bitte den laufenden Speichervorgang abwarten.");return;}
  if(recovery.hasInputs && !window.confirm("Ungespeicherte Eingaben verwerfen und abmelden? Bereits gespeicherte Entwürfe bleiben erhalten."))return;
  try{await api("/api/logout",{});recovery.clearAccount();for(const id of ["change-reason","change-source","vocab-reason","vocab-source"])$(id).value="";state.dirty=false;window.location.assign("/login");}
  catch(error){notice(error.message,"error");}
}
async function submitReview() {
  try {
    if (state.dirty) throw new Error("Bitte die Änderung zuerst speichern und prüfen.");
    const result=await api("/api/cases/" + state.current.slug + "/review",{
      reason:$("change-reason").value,source:$("change-source").value
    });
    recovery.clear();$("change-reason").value="";$("change-source").value="";
    $("review-link").href=result.url;
    $("review-link").hidden=false;
    if(result.branch){
      const slug=state.current.slug;
      state.branch=result.branch;state.activeCase="";refreshBranch();
      await loadCase(slug);
      setView("pruefung");
      $("review-link").href=result.url;$("review-link").hidden=false;
      loadDrafts().catch(error=>notice(error.message,"error"));
    }
    notice("Pull Request eingereicht. Jetzt folgt die notarielle Fachprüfung.","success");
  } catch(error){notice(error.message,"error");window.scrollTo({top:0,behavior:"smooth"});}
}
async function init() {
  try {
    const initialNavigation=viewSequence;
    const initialView=window.location.hash.slice(1);
    const requestedCase=new URLSearchParams(window.location.search).get("case");
    const status=await api("/api/status");state.token=status.token;state.branch=status.branch;state.purpose=status.purpose || "case";state.activeCase=status.case || "";state.hosted=!!status.hosted;state.ontologyMaintainer=!!status.ontology_maintainer;refreshBranch();
    if(status.user){state.user=status.user;state.notaryReviewer=!!status.notary_reviewer;$("session-user").textContent=status.user;$("logout").hidden=false;$("review-nav").hidden=false;}
    if (state.hosted) {
      const sources = await api("/api/repositories");
      const select = $("repository-select");
      for (const entry of sources.repositories) {
        const option = element("option", entry.label);
        option.value = entry.repository;
        select.append(option);
      }
      select.value = sources.selected;
      $("data-brand").hidden = sources.selected.toLowerCase() !== "notariat8/ontology";
      $("repository-name").textContent = sources.selected;
      $("repository-picker").hidden = false;
      select.addEventListener("change", async () => {
        const repository = select.value;
        select.disabled = true;
        try {
          if (state.dirty) throw new Error("Bitte zuerst ungespeicherte Änderungen speichern oder verwerfen.");
          if (state.branch !== "main") throw new Error("Bitte zuerst den geöffneten Entwurf ablegen.");
          await api("/api/repositories/select", {repository});
          window.location.assign("/");
        } catch (error) {
          select.value = sources.selected;
          notice(error.message, "error");
          select.disabled = false;
        }
      });
    }
    $("logout").addEventListener("click",logout);
    $("leave-draft").addEventListener("click",()=>leaveDraft().catch(error=>notice(error.message,"error")));
    const cases=await api("/api/cases");state.cases=cases;$("case-count").textContent=String(cases.length);
    cases.forEach(item=>{const option=element("option",item.title);option.value=item.slug;$("case-select").append(option);});
    for(const [key,label] of Object.entries(relations)){const option=element("option",label);option.value=key;$("edge-type").append(option);}
    $("case-select").addEventListener("change",event=>loadCase(event.target.value).catch(error=>notice(error.message,"error")));
    $("case-search").addEventListener("input",renderCaseList);
    $("case-history").addEventListener("toggle",()=>{if($("case-history").open)loadCaseHistory().catch(error=>notice(error.message,"error"));});
    $("history-apply").addEventListener("click",applyCaseHistory);
    $("case-index-query").addEventListener("input",()=>{renderCaseIndex();if($("case-index-query").value.trim().length>=2)loadCaseIndex().catch(()=>{});});
    enableSearchKeyboard("case-index-query","case-index-results");
    enableSearchKeyboard("graph-query","graph-results");
    $("vocab-search").addEventListener("input",renderVocabulary);
    $("vocab-impact-refresh").addEventListener("click",()=>loadVocabularyImpact().catch(error=>notice(error.message,"error")));
    $("vocab-edit").addEventListener("click",()=>editVocabulary().catch(error=>notice(error.message,"error")));
    $("vocab-add").addEventListener("click",()=>editVocabulary(true).catch(error=>notice(error.message,"error")));
    $("vocab-submit").addEventListener("click",submitVocabulary);
    for(const [id,key] of [["vocab-label","label"],["vocab-comment","comment"],["vocab-parent","parent"],["vocab-domain","domain"],["vocab-range","range"]]){
      $(id).addEventListener("input",event=>{const term=selectedTerm();if(!term)return;term[key]=event.target.value;dirty();if(key==="label"){$("vocab-title").textContent=term.label;renderVocabulary(false);}});
    }
    $("vocab-id").addEventListener("input",event=>{const term=selectedTerm();if(!term || !state.vocabNew)return;term.id=event.target.value;state.vocabSelected=term.id;dirty();renderVocabulary(false);});
    $("vocab-kind").addEventListener("change",event=>{const term=selectedTerm();if(!term || !state.vocabNew)return;term.kind=event.target.value;term.parent="";term.domain="";term.range="";dirty();renderVocabulary();});
    $("node-search").addEventListener("input",renderNodes);
    $("node-category").addEventListener("change",renderNodes);
    document.querySelectorAll("[data-view-button]").forEach(button=>button.addEventListener("click",()=>setView(button.dataset.viewButton)));
    document.querySelectorAll("[data-go-view]").forEach(button=>button.addEventListener("click",()=>setView(button.dataset.goView)));
    $("graph-scope").addEventListener("click",()=>{
      state.graphFocused=!state.graphFocused;
      $("graph-scope").setAttribute("aria-pressed",String(state.graphFocused));
      $("graph-scope").textContent=state.graphFocused ? "Ganzen Fall zeigen" : "Umfeld zeigen";
      renderGraph();renderGraphList();
    });
    for(const [id,mode] of [["graph-linked","linked"],["graph-all","all"]]){
      $(id).addEventListener("click",()=>{
        state.graphMode=mode;
        if(mode==="linked" && state.selected && !state.current.edges.some(edge=>edge.from===state.selected || edge.to===state.selected)){
          closeGraphInspector();state.selected=null;
        }
        renderGraph();renderGraphList();
      });
    }
    $("graph-orphans-show").addEventListener("click",()=>{$("graph-all").click();});
    for(const [id,change] of [["graph-zoom-out",-.15],["graph-zoom-in",.15],["graph-zoom-reset",0]]){
      $(id).addEventListener("click",()=>{state.graphZoom=change ? Math.max(.85,Math.min(1.5,Math.round((state.graphZoom+change)*100)/100)) : 1;renderGraph();});
    }
    $("graph-find").addEventListener("click",()=>openGraphSearch());
    $("edge-from-choose").addEventListener("click",()=>openGraphSearch("edge-from"));
    $("edge-to-choose").addEventListener("click",()=>openGraphSearch("edge-to"));
    $("graph-query").addEventListener("input",renderGraphSearch);
    $("case-node-search-close").addEventListener("click",()=>$("case-node-search").close());
    $("summary").addEventListener("input",event=>{state.current.summary=event.target.value;renderOverview();dirty();});
    $("sources").addEventListener("input",event=>{state.current.sources=event.target.value.split("\n").map(v=>v.trim()).filter(Boolean);renderOverview();dirty();});
    $("edit-overview").addEventListener("click",async()=>{
      try{
        if(state.branch==="main") await beginBranch();
        if(!caseEditable())throw new Error("Dieser Entwurf gehört zu einem anderen Fall. Lege ihn zuerst ab.");
        if(!$("case-sources").open)$("case-sources").showModal();
        $("overview-editor").hidden=!$("overview-editor").hidden;
        $("edit-overview").textContent=$("overview-editor").hidden ? "Beschreibung und Quellen bearbeiten" : "Bearbeitungsfelder schließen";
      }catch(error){notice(error.message,"error");}
    });
    $("edit-node").addEventListener("click",async()=>{
      try{
        if(!state.nodeEditing)await beginNodeEdit();
        else{state.nodeEditing=false;renderNodeForm();}
      }catch(error){notice(error.message,"error");}
    });
    $("add-node").addEventListener("click",()=>{
      let counter=1;while(state.current.nodes.some(node=>node.id===`local.${counter}`)) counter++;
      const node={id:`local.${counter}`,category:"required_information",label:"Neuer Baustein",status:"local-draft",question:"",section:"",detail:"",owner_role:"",privacy_class:"",document_source:"",contains_personal_data:null,required_for:[],options:[]};
      state.current.nodes.push(node);dirty();renderAll();selectNode(node.id);state.nodeEditing=true;renderNodeForm();
    });
    $("delete-node").addEventListener("click",()=>{
      const node=state.current.nodes.find(item=>item.id===state.selected);
      if (saveFlow.pending || !caseEditable() || !node || !node.id.startsWith("local.") || !window.confirm(`„${node.label}“ und seine Beziehungen entfernen?`)) return;
      state.current.nodes=state.current.nodes.filter(item=>item.id!==node.id);
      state.current.edges=state.current.edges.filter(edge=>edge.from!==node.id && edge.to!==node.id);
      state.selected=null;state.nodeEditing=false;dirty();renderAll();
    });
    $("add-edge").addEventListener("click",()=>{
      const edge={from:$("edge-from").value,type:$("edge-type").value,to:$("edge-to").value};
      if(!edge.from || !edge.to){notice("Bitte Ausgang und Ziel auswählen.","error");return;}
      if(state.current.edges.some(item=>item.from===edge.from && item.type===edge.type && item.to===edge.to)){notice("Diese Beziehung besteht bereits.","error");return;}
      state.current.edges.push(edge);$("edge-from").value="";$("edge-to").value="";fillNodeSelects();dirty();renderEdges();renderGraph();renderGraphList();
    });
    $("start-branch").addEventListener("click",async()=>{
      try{await beginBranch(state.view==="vokabular" ? "vocabulary" : "case");}
      catch(error){notice(error.message,"error");}
    });
    $("save").addEventListener("click",save);
    $("confirm-save").addEventListener("click",confirmSave);
    $("submit-review").addEventListener("click",submitReview);
    $("refresh-reviews").addEventListener("click",()=>loadReviewQueue().catch(error=>notice(error.message,"error")));
    $("request-changes").addEventListener("click",()=>submitCaseReview("REQUEST_CHANGES"));
    $("approve-review").addEventListener("click",()=>submitCaseReview("APPROVE"));
    $("source-open").addEventListener("click",()=>$("case-sources").showModal());
    $("source-close").addEventListener("click",()=>$("case-sources").close());
    $("inspector-close").addEventListener("click",()=>{closeGraphInspector();state.selected=null;renderAll();$("graph-find").focus({preventScroll:true});});
    $("global-search").addEventListener("click",()=>{$("catalog-search").showModal();$("case-index-query").focus();});
    document.addEventListener("keydown",event=>{
      if(event.key==="Escape" && !$("graph-inspector").hidden && !document.querySelector("dialog[open]")){$("inspector-close").click();return;}
      if((event.ctrlKey || event.metaKey) && event.key.toLowerCase()==="k"){
        event.preventDefault();
        if(!$("catalog-search").open){$("catalog-search").showModal();$("case-index-query").focus();}
      }
    });
    $("catalog-search-close").addEventListener("click",()=>$("catalog-search").close());
    for(const id of ["close-preview","cancel-preview"]) $(id).addEventListener("click",closeSavePreview);
    $("change-preview").addEventListener("cancel",event=>{if(saveFlow.pending==="save")event.preventDefault();});
    $("change-preview").addEventListener("close",()=>{if(!saveFlow.pending && !$("change-preview").open)saveFlow.preview=null;});
window.addEventListener("beforeunload",event=>{recovery.capture();if(recovery.hasInputs&&!recovery.redirecting){event.preventDefault();event.returnValue="";}});
    const firstView=["fall","bausteine","verbindungen","pruefung","vokabular"].includes(initialView) || (initialView==="fachpruefung" && state.user) ? initialView : "fall";
    await loadCase(cases.some(item=>item.slug===requestedCase) ? requestedCase : cases[0].slug,firstView,initialNavigation);
    if(state.user)loadDrafts().catch(error=>notice(error.message,"error"));
    recovery.offer();
  } catch(error){notice(error.message,"error");}
}
async function loadRelease() {
  try {
    const response = await fetch("/api/release", {cache: "no-store"});
    if (!response.ok) throw new Error("Release nicht verfügbar");
    const release = await response.json();
    if (/^[0-9a-f]{40}$/.test(release.commit || "")) {
      const link = $("release-link");
      link.textContent = release.commit.slice(0, 12);
      link.href = "https://github.com/ontologie8/editor8/commit/" + release.commit;
      link.title = "Ausgelieferter Softwarestand: " + release.commit;
      link.hidden = false;
      $("release-status").hidden = true;
    } else {
      $("release-status").textContent = "Entwicklung";
    }
  } catch (error) {
    $("release-status").textContent = "Nicht verfügbar";
  }
}


// Office shell: presentation only; mutations continue through the existing API.
const office={graphEdit:false,area:"understand",menu:"home",pinned:true,open:true,tree:true,lastView:"fall",closedCases:new Set(),closedGroups:new Set()};
function renderOffice(){
  office.area=["pruefung","fachpruefung"].includes(state.view)?"review":["bausteine","verbindungen"].includes(state.view)||state.vocabEditing||office.graphEdit?"edit":"understand";
  $("office-app").classList.toggle("office-edit-graph",office.graphEdit&&state.view==='fall');
  const detail=$("node-detail-panel");if(office.graphEdit&&state.view==='fall'){if(detail.parentElement!==$("graph-stage"))$("graph-stage").append(detail);}else if(detail.parentElement===$("graph-stage"))$("node-detail-slot").before(detail);
  $("office-app").classList.toggle("ribbon-collapsed",!office.pinned);$("office-app").classList.toggle("ribbon-floating",!office.pinned&&office.open);
  $("office-ribbon").hidden=!office.open;
  $("ribbon-toggle").setAttribute("aria-expanded",String(office.open));$("ribbon-toggle").setAttribute("aria-label",office.pinned?"Menüband reduzieren":"Menüband immer anzeigen");$("ribbon-toggle").title=(office.pinned?"Menüband reduzieren":"Menüband immer anzeigen")+" (Strg+F1)";
  $("workspace-shell").classList.toggle("tree-collapsed",!office.tree);$("navigation-toggle").setAttribute("aria-expanded",String(office.tree));$("navigation-toggle").setAttribute("aria-label",office.tree?"Navigationsbereich ausblenden":"Navigationsbereich einblenden");
  document.querySelectorAll("[data-menu]").forEach(button=>button.setAttribute("aria-selected",String(button.dataset.menu===office.menu)));
  document.querySelectorAll("[data-area]").forEach(button=>{button.setAttribute("aria-pressed",String(button.dataset.area===office.area));button.disabled=!state.current;});
  const commands=office.menu==='home'?'home-'+office.area:office.menu;
  document.querySelectorAll("[data-command-group]").forEach(group=>group.hidden=group.dataset.commandGroup!==commands);
  $("save-current").disabled=$("save").disabled;$("new-node").disabled=!state.current||!caseEditable();
  const tasks=$("task-navigation");tasks.replaceChildren();
  const taskMode=state.view==='hilfe'||office.area==='review';tasks.hidden=!taskMode;$("case-list").hidden=taskMode;
  // Keep the count element attached: the catalog and repository remain discoverable.
  $("navigation-heading").firstChild.textContent=state.view==='hilfe'?'Dokumentation ':office.area==='review'?'Änderungen ':'Vorgangsarten ';
  if(state.view==='hilfe'){
    const sections=$("learning-frame")?.contentDocument?.querySelectorAll('#sections button');
    if(sections?.length){
      $("navigation-heading").firstChild.textContent=office.helpTopic==='handbook'?'Kapitel ':'Lektionen ';
      sections.forEach(section=>{const b=element('button',section.textContent);b.type='button';if(section.getAttribute('aria-current')==='page')b.setAttribute('aria-current','page');b.addEventListener('click',()=>{section.click();renderOffice();});tasks.append(b);});
    }else $("help-content").querySelectorAll('h3').forEach(heading=>{const b=element('button',heading.textContent);b.type='button';b.addEventListener('click',()=>heading.scrollIntoView({block:'start'}));tasks.append(b);});
  }else if(office.area==='review'){
    [['pruefung','Meine Änderung'],['fachpruefung','Fachprüfung']].filter(([view])=>view!=='fachpruefung'||state.user).forEach(([view,label])=>{const b=element('button',label);b.type='button';b.setAttribute('aria-current',view===state.view?'page':'false');b.addEventListener('click',()=>setView(view));tasks.append(b);});
    if(state.branch!=='main')tasks.append(element('p','Geöffneter Arbeitsentwurf · '+(state.cases.find(item=>item.slug===state.activeCase)?.title||state.activeCase||'Gemeinsame Begriffe'),'context-help'));
  }
  $("case-count").hidden=taskMode;
}
function toggleRibbon(){office.pinned=!office.pinned;office.open=office.pinned;renderOffice();}
function showHelp(topic='start'){
  if(state.view!=='hilfe')office.lastView=state.view;
  setView('hilfe');if(state.view!=='hilfe')return;
  office.menu='help';office.helpTopic=topic;renderOffice();const root=$("help-content");root.replaceChildren();
  root.parentElement.classList.toggle('learning-workspace',['training','handbook'].includes(topic));
  if(['training','handbook'].includes(topic)){
    const frame=document.createElement('iframe');frame.id='learning-frame';frame.title=topic==='training'?'Training: Ontologien verstehen und pflegen':'Handbuch für Ontologiepflege und notarielle Prüfung';frame.src='/learning/?embedded=1&mode='+topic;frame.addEventListener('load',()=>{if($("learning-frame")!==frame)return;renderOffice();frame.contentDocument.addEventListener('learning-change',()=>renderOffice());});root.append(frame);return;
  }
  renderOffice();
  root.append(element('h2',topic==='example'?'Beispiel':topic==='terms'?'Begriffe':'Kurzanleitung'));
  const blocks=topic==='example'?[
    ['Künstliches Beispiel','Eine Angabenfrage „Angabe A“ ist mit einem Dokumenttyp „Nachweis A“ verbunden. Beide Namen sind ausschließlich ein künstliches Beispiel.'],
    ['Verstehen','Wähle im Datenbaum den Vorgang und anschließend einen Baustein. Der Graph zeigt die Verbindungen, rechts stehen die Details.'],
    ['Bearbeiten','Erstelle einen Arbeitsentwurf, ändere die Bezeichnung und wähle Speichern. Prüfe die angezeigten Unterschiede, bevor du das Speichern bestätigst.'],
    ['Prüfen','Beschreibe Grund und Quellenstand. Reiche die gespeicherte Änderung ein. Eine andere berechtigte Person prüft sie; eine notarielle Freigabe braucht das entsprechende Konto.']
  ]:topic==='terms'?[
    ['Modellbestand','Die ausgewählten Fachmodelle, etwa „Notar-Fachmodelle“. Deine Entwürfe und Prüfentscheidungen gehören zu diesem Bestand.'],
    ['Vorgangsart','Eine wiederverwendbare Fachvorlage mit Bausteinen und Beziehungen. Sie beschreibt, was benötigt wird; eine konkrete Akte wird dadurch nicht angelegt.'],
    ['Baustein','Eine Frage, ein Dokumenttyp, eine Entscheidung, ein Prüfschritt oder ein Nachweistyp im Fachmodell.'],
    ['Arbeitsentwurf','Deine eigene Fassung einer Modelländerung. Speichern sichert sie getrennt von der gemeinsam verwendeten Vorlage. Danach kannst du sie zur Fachprüfung einreichen.'],
    ['Fachprüfung','Prüfung einer eingereichten Änderung einschließlich fachlicher Wirkung und Quellenstand. Speichern allein erteilt keine Freigabe.']
  ]:[
    ['Deine Aufgabe','Als Ontologiepfleger oder Notar pflegst und prüfst du Fachmodelle: Begriffe, Angaben, Dokumenttypen und ihre Beziehungen. Training und Handbuch erklären diese fachliche Arbeit mit künstlichen Beispielen.'],
    ['Öffnen und Suchen','Wähle links den Fachmodellbestand und die Vorgangsart im Baum. Das Suchfeld oben filtert die aktuelle Auswahl. Mit Eingabetaste oder Strg+K durchsuchst du Bausteine im gesamten ausgewählten Bestand.'],
    ['Verstehen','Wähle einen Baustein im Baum oder Graphen. Rechts erscheinen die Details. Das Fragezeichen öffnet Hilfe zur aktuellen Auswahl. Informationen zeigt die Quellen und den Änderungsverlauf.'],
    ['Bearbeiten und Speichern','Wähle links Bearbeiten. Erstelle einen Entwurf oder wähle beim Baustein Bearbeiten. Speichern zeigt zuerst einen Vergleich. Erst deine Bestätigung schreibt die Änderung in den Datenentwurf.'],
    ['Prüfen','Unter Meine Änderung reichst du den gespeicherten Entwurf mit Grund und Quellenstand ein. Unter Fachprüfung beurteilst du Änderungen anderer Personen. Fachlich freigeben benötigt die entsprechende notarielle Berechtigung.'],
    ['Ansicht und Drucken','Unter Ansicht wechselst du zwischen Zusammenhängen, Bausteinen, Verbindungen und gemeinsamen Begriffen. Datei → Drucken erstellt eine Lesefassung der aktuellen Auswahl.'],
    ['Menüband','Strg+F1 oder Doppelklick reduziert das Menüband. Ein Klick auf eine Registerkarte öffnet die Befehle vorübergehend. Der Schalter rechts hält sie dauerhaft sichtbar. Die Baum-Navigation wird unabhängig über das Menü-Symbol links gesteuert.'],
    ['Hinweise und Kontextmenü','Halte den Mauszeiger kurz über einen Befehl, ein Feld oder einen Baustein, um einen Hinweis zu lesen. Rechtsklick auf einen Baustein öffnet Öffnen, Bearbeiten, Verbindungen und Hilfe zur Auswahl. Mit Umschalt+F10 öffnest du das Menü auch per Tastatur; Escape schließt es.']
  ];blocks.forEach(([title,text])=>root.append(element('h3',title),element('p',text)));
  root.append(element('h3','Herkunft und Lizenz'),element('p','Based on NaC: Notariat as Code by funktion8 / ofunk. Code: AGPL-3.0-or-later; Dokumentation: CC-BY-4.0.'));
  const attribution=element('p');const source=element('a','NaC-Originalprojekt');source.href='https://github.com/notariat8/NaC';const license=element('a','Lizenz und Markenhinweise');license.href='https://github.com/ontologie8/editor8/blob/main/LICENSES/README.md';attribution.append(source,document.createTextNode(' · '),license);root.append(attribution);
  renderOffice();
}
function selectionHelp(){
  const root=$("selection-help-content");root.replaceChildren();const node=state.current?.nodes.find(item=>item.id===state.selected);
  if(state.view==='vokabular'){
    const term=selectedTerm();$("selection-help-title").textContent=term?'Hilfe zu '+term.label:'Hilfe zu gemeinsamen Begriffen';root.append(element('p','Gemeinsame Begriffe gelten für mehrere Vorgangsarten des ausgewählten Modellbestands. Prüfe ihre Bedeutung und Verwendung, bevor du sie in einem eigenen Entwurf änderst. Die Pflege benötigt eine zusätzliche fachliche Berechtigung; anschließend folgt die Fachprüfung.'));
  }else{$("selection-help-title").textContent=node?'Hilfe zu '+displayNodeLabel(node):'Hilfe zur Auswahl';root.append(element('p',node?(groups.find(item=>item[0]===node.category)?.[1]||'Baustein')+' im Vorgang „'+state.current.title+'“.':'Wähle zuerst einen Baustein im Baum oder im Graphen.'));if(node){root.append(element('p',node.detail||node.question||'Zu diesem Baustein liegt keine weitere Erläuterung im Datenmodell vor.'));root.append(element('p','Links Bearbeiten wählen, um die Inhalte in einem Arbeitsentwurf zu ändern. Verbindungen zeigt die Beziehungen zu anderen Bausteinen.'));}}
  $("selection-help-dialog").showModal();
}
function printSelection(){
  if(state.view==='hilfe'&&$("learning-frame")){const print=$("learning-frame").contentDocument?.getElementById('print');if(print)print.click();return;}
  const root=$("print-document");root.replaceChildren();
  if(state.view==='hilfe'){const copy=$("help-content").cloneNode(true);copy.removeAttribute('id');root.append(copy);}
  else if(state.view==='vokabular'&&state.vocabulary){root.append(element('h1','Gemeinsame Begriffe'));state.vocabulary.terms.forEach(term=>root.append(element('h2',term.label),element('p',term.comment||'')));}
  else if(state.reviewDetail&&state.view==='fachpruefung'){root.append(element('h1',state.reviewDetail.title),element('p',state.reviewDetail.body));state.reviewDetail.changes.forEach(change=>root.append(element('p',change)));}
  else if(state.current){root.append(element('h1',state.current.title),element('p',state.current.summary));state.current.nodes.forEach(node=>root.append(element('h2',displayNodeLabel(node)),element('p',[node.question,node.detail].filter(Boolean).join('\n'))));root.append(element('h2','Verbindungen'));state.current.edges.forEach(edge=>root.append(element('p',nodeLabel(edge.from)+' '+(relations[edge.type]||edge.type)+' '+nodeLabel(edge.to))));}
  else{notice('Bitte zuerst einen Vorgang öffnen.','error');return;}
  root.append(element('p','Datenquelle: '+($("repository-name").textContent||'Lokales Datenziel')+' · '+$("branch").textContent));window.print();
}
function initOffice(){
  $("navigation-toggle").addEventListener('click',()=>{office.tree=!office.tree;renderOffice();});$("ribbon-toggle").addEventListener('click',toggleRibbon);
  document.querySelectorAll('[data-menu]').forEach(tab=>{tab.addEventListener('click',()=>{office.menu=tab.dataset.menu;if(!office.pinned)office.open=true;if(office.menu==='help')showHelp();else if(state.view==='hilfe')setView(office.lastView);renderOffice();});tab.addEventListener('dblclick',toggleRibbon);});
  document.querySelectorAll('[data-area]').forEach(button=>button.addEventListener('click',()=>{office.menu='home';office.graphEdit=button.dataset.area==='edit';setView(button.dataset.area==='review'?'pruefung':'fall');if(office.graphEdit&&state.current&&!state.selected)selectNode(state.current.nodes[0]?.id);}));
  document.querySelectorAll('[data-help-topic]').forEach(button=>button.addEventListener('click',()=>showHelp(button.dataset.helpTopic)));
  $("file-open").addEventListener('click',()=>{office.tree=true;office.graphEdit=false;office.menu='home';setView('fall');$("app-search").focus();});
  $("app-search").addEventListener('input',event=>{$("case-search").value=event.target.value;renderCaseList();});
  $("app-search").addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();$("global-search").click();$("case-index-query").value=event.target.value;renderCaseIndex();if(event.target.value.trim().length>=2)loadCaseIndex().catch(()=>{});}});
  $("save-current").addEventListener('click',()=>$("save").click());$("new-node").addEventListener('click',()=>$("add-node").click());
  $("print").addEventListener('click',printSelection);$("fullscreen").addEventListener('click',async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch{notice('Vollbild kann mit F11 geöffnet werden.');}});
  for(const id of ['selection-help','edit-selection-help'])$(id).addEventListener('click',selectionHelp);$("selection-help-close").addEventListener('click',()=>$("selection-help-dialog").close());
  $("saved-drafts").addEventListener('click',()=>{office.tree=true;renderOffice();if(state.branch==='main')loadDrafts().catch(error=>notice(error.message,'error'));else notice('Schließe den geöffneten Entwurf, um andere Arbeitsentwürfe zu öffnen.');});
  document.addEventListener('pointerdown',event=>{if(!office.pinned&&office.open&&!event.target.closest('.menubar,.office-ribbon')){office.open=false;renderOffice();}});
  document.addEventListener('keydown',event=>{if(event.ctrlKey&&event.key==='F1'){event.preventDefault();toggleRibbon();}else if(event.key==='Escape'&&!office.pinned&&office.open){office.open=false;renderOffice();}else if(event.ctrlKey&&!event.altKey&&['s','o','p'].includes(event.key.toLowerCase())){event.preventDefault();const key=event.key.toLowerCase();if(key==='s'&&!$("save").disabled)save();if(key==='o')$("file-open").click();if(key==='p')printSelection();}});
  renderOffice();
}
initOffice();
loadRelease();
init();
