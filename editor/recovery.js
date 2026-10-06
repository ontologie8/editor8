// SPDX-License-Identifier: AGPL-3.0-or-later
"use strict";
// Only unfinished model inputs in this browser tab. No credentials or tokens.
window.EditorRecovery = (() => {
  const prefix="editor8:inputs:v1:";
  const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  const fields=["label","category","status","question","section","detail","owner_role","privacy_class","document_source","contains_personal_data","required_for","options","kind","comment","parent","domain","range"];
  const fieldNames={label:"Bezeichnung",category:"Art",status:"Status",question:"Fachfrage",section:"Kapitel",detail:"Erläuterung",owner_role:"Rolle",privacy_class:"Datenschutzklasse",document_source:"Dokumentquelle",contains_personal_data:"Personendaten-Hinweis",required_for:"Benötigt für",options:"Optionen",kind:"Art",comment:"Erläuterung",parent:"Oberklasse",domain:"Gilt für",range:"Zielklasse oder Datentyp"};
  function merge(base,local,latest,purpose){
    const conflicts=[];const result=structuredClone(latest);
    function value(old,own,current,name){
      if(same(own,old))return current;
      if(same(current,old)||same(current,own))return own;
      conflicts.push(name);return current;
    }
    const collection=purpose==="vocabulary"?"terms":"nodes";
    if(![base,local,latest].every(model=>model&&Array.isArray(model[collection])))throw new Error("Die gesicherten Eingaben sind unvollständig.");
    const maps=[base,local,latest].map(model=>new Map(model[collection].map(item=>[item.id,item])));
    result[collection]=[];
    for(const id of new Set(maps.flatMap(map=>[...map.keys()]))){
      const [old,own,current]=maps.map(map=>map.get(id));
      if(!old||!own||!current){
        const chosen=value(old,own,current,own?.label||current?.label||id);
        if(chosen)result[collection].push(structuredClone(chosen));
      }else{
        const item={...current};
        for(const field of fields){
          const chosen=value(old[field],own[field],current[field],(own.label||id)+" · "+fieldNames[field]);
          if(chosen===undefined)delete item[field];else item[field]=structuredClone(chosen);
        }
        result[collection].push(item);
      }
    }
    if(purpose!=="vocabulary"){
      result.summary=value(base.summary,local.summary,latest.summary,"Kurzbeschreibung");
      result.sources=value(base.sources,local.sources,latest.sources,"Quellen");
      const key=edge=>JSON.stringify([edge.from,edge.type,edge.to]);
      const edgeMaps=[base,local,latest].map(model=>new Map(model.edges.map(edge=>[key(edge),edge])));
      result.edges=[...edgeMaps[2].values()].filter(edge=>!edgeMaps[0].has(key(edge))||edgeMaps[1].has(key(edge)));
      for(const [id,edge] of edgeMaps[1])if(!edgeMaps[0].has(id)&&!result.edges.some(item=>key(item)===id))result.edges.push(structuredClone(edge));
      const ids=new Set(result.nodes.map(node=>node.id));
      if(result.edges.some(edge=>!ids.has(edge.from)||!ids.has(edge.to)))conflicts.push("Eine Beziehung verweist auf einen inzwischen entfernten Baustein.");
    }
    return {model:result,conflicts};
  }
  function create(context){
    let bases={};let candidate=null;let memoryEntry=null;let redirecting=false;let applying=false;
    const dialog=document.getElementById("input-recovery");
    const message=document.getElementById("recovery-message");
    const status=document.getElementById("recovery-status");
    const restore=document.getElementById("restore-inputs");
    const account=()=>context.state().user||"local";
    const repository=()=>context.repository();
    const key=()=>prefix+account().toLowerCase()+":"+repository();
    function clear(){try{sessionStorage.removeItem(key());}catch{} candidate=null;memoryEntry=null;}
    function capture(){
      const state=context.state();const extras=context.extras();
      const hasExtras=Object.values(extras).some(value=>typeof value==="string"&&value.trim());
      if(!state.dirty&&(state.branch==="main"||!hasExtras))return true;
      const purpose=state.purpose==="vocabulary"?"vocabulary":"case";
      const subject=purpose==="vocabulary"?state.vocabulary:state.current;
      if(!subject||!bases[purpose]||state.branch==="main")return false;
      const entry={version:1,user:account(),repository:repository(),branch:state.branch,purpose,
        case:subject.slug||"",base:bases[purpose],model:subject,selected:purpose==="vocabulary"?state.vocabSelected:state.selected,
        extras,updated:Date.now()};
      memoryEntry=structuredClone(entry);
      try{
        const text=JSON.stringify(entry);if(text.length>3000000)throw new Error("too large");
        sessionStorage.setItem(key(),text);return true;
      }catch{
        context.notice("Offene Eingaben konnten in diesem Browser nicht zwischengesichert werden. Halte dieses Fenster geöffnet.","error");return false;
      }
    }
    function offer(){
      try{candidate=JSON.parse(sessionStorage.getItem(key()));}catch{candidate=null;}
      if(!candidate)return;
      if(candidate.version!==1||typeof candidate.user!=="string"||candidate.user.toLowerCase()!==account().toLowerCase()||candidate.repository!==repository()||!Number.isFinite(candidate.updated)||Date.now()-candidate.updated>7*86400000){clear();return;}
      message.textContent="In diesem Browserfenster sind nicht gespeicherte Eingaben für deinen Modellbestand vorhanden. Wiederherstellen öffnet deinen Entwurf und prüft den aktuellen Stand. Deine Eingaben werden erst mit Speichern dauerhaft übernommen.";
      status.textContent="";restore.hidden=false;document.getElementById("reconnect-inputs").hidden=true;dialog.showModal();
    }
    async function apply(){
      if(applying||!candidate)return;applying=true;restore.disabled=true;status.textContent="Entwurf und gespeicherter Stand werden geprüft …";
      try{
        const state=context.state();
        if(state.dirty)throw new Error("Bitte zuerst die aktuell offenen Eingaben speichern oder verwerfen.");
        if(state.branch!==candidate.branch){
          if(state.branch!=="main")throw new Error("Bitte zuerst den geöffneten Entwurf ablegen.");
          if(state.hosted){
            const result=await context.api("/api/drafts/resume",{branch:candidate.branch,case:candidate.case});
            if(result.purpose!==candidate.purpose||(result.case||"")!==candidate.case)throw new Error("Dieser Entwurf gehört zu einem anderen Arbeitsbereich.");
            state.branch=result.branch;state.purpose=result.purpose;state.activeCase=result.case||"";
          }else throw new Error("Öffne zuerst den zugehörigen lokalen Entwurf.");
        }
        if(candidate.purpose==="vocabulary"&&!state.ontologyMaintainer&&state.hosted)throw new Error("Für gemeinsame Begriffe fehlt die fachliche Bearbeitungsberechtigung.");
        const path=candidate.purpose==="vocabulary"?"/api/vocabulary":"/api/cases/"+encodeURIComponent(candidate.case);
        const latest=await context.api(path);
        const proposal=merge(candidate.base,candidate.model,latest,candidate.purpose);
        if(proposal.conflicts.length){
          status.textContent="Der gespeicherte Stand und deine Eingaben ändern dieselben Inhalte. Es wurde nichts überschrieben. Sichere deine Eingaben und kläre den Vergleich: "+proposal.conflicts.join("; ");
          return;
        }
        // Validate through the ordinary preview before adopting recovered inputs.
        const preview=await context.api(path+"/preview",proposal.model);
        bases[candidate.purpose]=structuredClone(latest);
        await context.adopt(proposal.model,candidate);
        dialog.close();candidate=null;
        if(!preview.changed){context.saved();clear();}
        capture();
        context.notice(preview.changed?"Eingaben wiederhergestellt. Prüfe den Vergleich und wähle Speichern.":"Der Modellstand ist bereits gespeichert. Offene Begründung und Quellenstand wurden wiederhergestellt.","success");
      }catch(error){status.textContent=error.message;context.refresh();}
      finally{applying=false;restore.disabled=false;}
    }
    function expired(){
      if(capture()){
        redirecting=true;window.location.assign("/login");
      }else{
        message.textContent="Deine Anmeldung ist abgelaufen. Die offenen Eingaben bleiben hier erhalten. Melde dich über den Link in einem zweiten Fenster erneut an; dieses Arbeitsfenster bleibt geöffnet.";
        restore.hidden=true;document.getElementById("reconnect-inputs").hidden=false;status.textContent="Die automatische Zwischensicherung ist nicht verfügbar.";
        if(!dialog.open)dialog.showModal();
      }
    }
    restore.addEventListener("click",apply);
    document.getElementById("reconnect-inputs").addEventListener("click",async()=>{
      const entry=memoryEntry;if(!entry)return;
      try{
        const response=await fetch("/api/status");if(!response.ok)throw new Error("Bitte zuerst über den Link erneut anmelden.");
        const current=await response.json();
        if((current.user||"local").toLowerCase()!==entry.user.toLowerCase())throw new Error("Bitte mit demselben Konto erneut anmelden.");
        const sourcesResponse=await fetch("/api/repositories");if(!sourcesResponse.ok)throw new Error("Der Modellbestand konnte nicht geprüft werden.");
        const sources=await sourcesResponse.json();if(sources.selected!==entry.repository)throw new Error("Bitte zuerst im zweiten Fenster denselben Modellbestand auswählen.");
        const state=context.state();state.token=current.token;state.branch=current.branch;state.purpose=current.purpose||"case";state.activeCase=current.case||"";state.ontologyMaintainer=!!current.ontology_maintainer;
        candidate=entry;state.dirty=false;restore.hidden=false;await apply();
        if(dialog.open){state.dirty=true;context.refresh();}
      }catch(error){status.textContent=error.message;}
    });
    document.getElementById("discard-inputs").addEventListener("click",()=>{
      if(applying)return;
      if(window.confirm("Zwischengesicherte Eingaben verwerfen? Gespeicherte Entwürfe bleiben erhalten.")){clear();dialog.close();context.discard();}
    });
    document.getElementById("export-inputs").addEventListener("click",()=>{
      const entry=candidate||memoryEntry||(()=>{capture();try{return JSON.parse(sessionStorage.getItem(key()));}catch{return null;}})();
      if(!entry){status.textContent="Die offenen Eingaben konnten nicht gelesen werden.";return;}
      const url=URL.createObjectURL(new Blob([JSON.stringify(entry,null,2)],{type:"application/json"}));
      const link=document.createElement("a");link.href=url;link.download="editor8-eingaben.json";link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    });
    dialog.addEventListener("cancel",event=>{if(applying||candidate)event.preventDefault();});
    document.addEventListener("input",capture);
    window.addEventListener("pagehide",capture);
    function clearAccount(){try{for(const storageKey of Object.keys(sessionStorage))if(storageKey.startsWith(prefix+account().toLowerCase()+":"))sessionStorage.removeItem(storageKey);}catch{} clear();}
    return {capture,clear,clearAccount,offer,expired,merge,setBase:(subject,purpose)=>{bases[purpose]=structuredClone(subject);},get redirecting(){return redirecting;},get hasInputs(){return context.state().dirty||(context.state().branch!=="main"&&Object.values(context.extras()).some(value=>typeof value==="string"&&value.trim()));}};
  }
  return {create,merge};
})();
