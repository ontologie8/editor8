// SPDX-License-Identifier: AGPL-3.0-or-later
"use strict";

// Office-style interaction layer. Commands reuse the editor's guarded workflows.
(() => {
  const tooltip=element("div",undefined,"app-tooltip");
  tooltip.id="app-tooltip";tooltip.setAttribute("role","tooltip");tooltip.hidden=true;
  const menu=element("div",undefined,"app-context-menu");
  menu.id="app-context-menu";menu.setAttribute("role","menu");menu.tabIndex=-1;menu.hidden=true;
  document.body.append(tooltip,menu);
  let tipTarget=null, tipTimer=null, hideTimer=null, suppressed=null, menuContext=null, origin=null, returnFocus=null;

  const hints={
    "navigation-toggle":["Navigation","Blendet den inneren Baum ein oder aus. Die Arbeitsbereiche links bleiben erreichbar."],
    "ribbon-toggle":["Menüband","Zeigt die Befehle dauerhaft oder nur beim Öffnen einer Registerkarte.","Strg+F1"],
    "app-search":["Suchen","Filtert die Vorgangsarten im Baum. Eingabetaste durchsucht auch deren Bausteine.","Strg+K"],
    "repository-select":["Modellbestand","Wählt die Fachmodelle aus, an denen du arbeitest. Offene Änderungen zuerst speichern."],
    "file-open":["Öffnen","Wähle eine Vorgangsart im Baum oder suche sie über das Suchfeld.","Strg+O"],
    "save":["Speichern","Zeigt die Änderungen zum Vergleichen. Erst deine Bestätigung speichert den Arbeitsentwurf.","Strg+S"],
    "save-current":["Speichern","Zeigt die Änderungen zum Vergleichen. Erst deine Bestätigung speichert den Arbeitsentwurf.","Strg+S"],
    "print":["Drucken","Druckt eine Lesefassung der geöffneten Vorgangsart oder Hilfe.","Strg+P"],
    "source-open":["Informationen","Lies Beschreibung, Quellen und frühere Fassungen der geöffneten Vorgangsart."],
    "graph-find":["Baustein suchen","Sucht Fragen, Dokumenttypen und andere Bausteine in der geöffneten Vorgangsart."],
    "start-branch":["Entwurf erstellen","Beginnt deinen eigenen Arbeitsentwurf. Die gemeinsam verwendete Vorlage bleibt bis zur Übernahme erhalten."],
    "saved-drafts":["Arbeitsentwürfe","Öffnet deine gespeicherten, noch nicht eingereichten Entwürfe."],
    "leave-draft":["Entwurf schließen","Kehrt zur gemeinsam verwendeten Vorlage zurück. Gespeicherte Entwürfe kannst du später wieder öffnen."],
    "new-node":["Neuer Baustein","Ergänzt eine Frage oder einen anderen Baustein in deinem Entwurf."],
    "add-node":["Neuer Baustein","Ergänzt eine Frage oder einen anderen Baustein in deinem Entwurf."],
    "edit-node":["Bearbeiten","Öffnet die Felder des ausgewählten Bausteins und beginnt bei Bedarf einen Arbeitsentwurf."],
    "delete-node":["Entfernen","Entfernt einen zusätzlich angelegten Baustein und seine Verbindungen nach deiner Bestätigung."],
    "selection-help":["Hilfe zur Auswahl","Erläutert den fachlichen Kontext des ausgewählten Bausteins."],
    "edit-selection-help":["Hilfe zur Auswahl","Erläutert den fachlichen Kontext des ausgewählten Bausteins."],
    "inspector-close":["Detailansicht schließen","Schließt die Details und zeigt wieder den ganzen Fall."],
    "graph-linked":["Verknüpfte Bausteine","Zeigt nur Bausteine mit einer Verbindung. Weitere Bausteine stehen darunter."],
    "graph-all":["Alle Bausteine","Zeigt auch Bausteine ohne Verbindung."],
    "graph-scope":["Umfeld anzeigen","Wechselt zwischen den direkten Nachbarn der Auswahl und dem ganzen Fall."],
    "graph-zoom-in":["Vergrößern","Vergrößert den Graphen innerhalb des Arbeitsbereichs."],
    "graph-zoom-out":["Verkleinern","Verkleinert den Graphen innerhalb des Arbeitsbereichs."],
    "graph-zoom-reset":["Einpassen","Setzt die Größe des Graphen auf 100 Prozent zurück."],
    "graph-orphans-show":["Alle im Graphen zeigen","Zeigt auch die bisher unverbundenen Bausteine im Graphen."],
    "submit-review":["Zur Fachprüfung einreichen","Gibt deinen gespeicherten Entwurf mit Begründung und Quellenstand an eine andere prüfende Person."],
    "vocab-submit":["Zur Fachprüfung einreichen","Gibt die gespeicherten Änderungen an gemeinsamen Begriffen zur notariellen Prüfung."],
    "approve-review":["Fachlich freigeben","Dokumentiert deine begründete notarielle Prüfung einer Änderung einer anderen Person."],
    "request-changes":["Änderung anfordern","Beschreibt, welche fachliche Korrektur vor einer Freigabe erforderlich ist."],
    "vocab-edit":["Begriff bearbeiten","Ändert einen gemeinsamen Begriff. Prüfe seine Verwendung in anderen Vorgangsarten."],
    "vocab-add":["Neuer Begriff","Ergänzt einen wiederverwendbaren Begriff mit dauerhafter Kennung."],
    "vocab-impact-refresh":["Verwendung aktualisieren","Zeigt, welche Vorgangsarten den ausgewählten Begriff verwenden."],
    "fullscreen":["Vollbild","Nutzt den ganzen Bildschirm für die Arbeitsoberfläche."],
    "logout":["Abmelden","Beendet deine Anmeldung. Offene Änderungen vorher speichern."],
    "confirm-save":["Speichern","Speichert genau die Änderungen, die du in diesem Vergleich geprüft hast."],
    "cancel-preview":["Weiter bearbeiten","Schließt den Vergleich und erhält deine noch nicht gespeicherten Eingaben."],
    "edge-from-choose":["Ausgang wählen","Wählt den Baustein, von dem die Verbindung ausgeht."],
    "edge-to-choose":["Ziel wählen","Wählt den Baustein, zu dem die Verbindung führt."],
    "add-edge":["Hinzufügen","Ergänzt die Verbindung in deinem Arbeitsentwurf. Speichern prüft sie zusammen mit dem Modell."]
  };
  const fieldHints={
    "Kennung":"Dauerhafte Kennung des Bausteins. Sie wird beim Umbenennen nicht verändert.",
    "Bezeichnung":"Lesbarer Name des Begriffs oder Bausteins. Beschreibe die Vorlage, keine konkrete Akte.",
    "Bausteintyp":"Ordnet den Baustein einer fachlichen Kategorie zu, etwa Fragen oder Dokumenttypen.",
    "Art":"Ordnet die Auswahl einer fachlichen Kategorie zu.",
    "Vorgangsart suchen":"Filtert die Vorgangsarten und Bausteine im geöffneten Baum.",
    "Baustein suchen":"Filtert die Bausteine der geöffneten Vorgangsart nach Bezeichnung oder Kennung.",
    "Begriff suchen":"Filtert die gemeinsamen Begriffe nach Bezeichnung, Kennung und Erläuterung.",
    "Pflegestatus des lokalen Entwurfs":"Status des zusätzlich angelegten Bausteins nach den im Modellbestand vereinbarten Angaben.",
    "Status der NaC-Vorlage":"Übernommener Quellenstatus. Diese Angabe bleibt beim Bearbeiten unverändert.",
    "Kurzbeschreibung":"Erklärt Zweck und Inhalt der Vorgangsart als Fachvorlage.",
    "Rechtsquellen":"Quellen für die fachliche Vorlage. Trage eine HTTPS-Adresse je Zeile ein.",
    "Offene Fachfrage":"Hält fest, welche fachliche Bedeutung noch geklärt werden muss.",
    "Abschnitt der Vorlage":"Ordnet den Baustein einem Abschnitt der fachlichen Vorlage zu.",
    "Fachliche Erläuterung":"Beschreibt Bedeutung und Zweck des Bausteins für andere Ontologiepfleger und Notare.",
    "Verantwortliche Rolle":"Benennung der fachlich zuständigen Rolle, keine Person oder Akte.",
    "Datenschutzklasse":"Fachliche Einordnung nach den im Modellbestand vereinbarten Datenschutzklassen.",
    "Benötigt für":"Verwendungszwecke des Bausteins. Trage einen Zweck je Zeile ein.",
    "Entscheidungsoptionen":"Mögliche Auswahlwerte der Fachvorlage. Trage eine Option je Zeile ein.",
    "Dokumentquelle":"Quelle oder Herkunft der vorgesehenen Dokumentart.",
    "Kann Personendaten enthalten?":"Kennzeichnet die mögliche Verwendung. Trage hier keine tatsächlichen Personendaten ein.",
    "Fachlicher Grund":"Erklärt, warum die Modelländerung erforderlich ist und was sie fachlich bewirkt.",
    "Quellenstand":"Benennt die verwendete Fachquelle mit Fassung oder Datum.",
    "Fachlicher Grund / Quellenstand":"Begründe die Änderung und benenne die verwendete Fachquelle.",
    "Warum ist die Änderung nötig?":"Beschreibe die fachliche Änderung und ihre Wirkung auf das Modell.",
    "Welcher Quellenstand wurde verwendet?":"Benenne die verwendete Fachquelle mit Fassung oder Datum.",
    "Deine fachliche Begründung":"Beschreibe deine Prüfung der Bedeutung, Quellen und Beziehungen.",
    "Eindeutige Kennung":"Dauerhafte Kennung des gemeinsamen Begriffs. Bestehende Kennungen bleiben fest.",
    "Erläuterung":"Beschreibt die gemeinsame Bedeutung des Begriffs für alle betroffenen Vorgangsarten.",
    "Oberklasse":"Ordnet die Begriffsklasse einer allgemeineren Klasse zu.",
    "Gilt für":"Bestimmt, für welche Begriffsklasse das Merkmal oder die Verbindung gilt.",
    "Zielklasse oder Datentyp":"Bestimmt die zulässige Zielklasse einer Verbindung oder den Datentyp eines Merkmals.",
    "Beziehung":"Lies die Verbindung als Satz: Ausgangspunkt – Beziehung – Ziel."
  };

  function describe(target) {
    if(target.dataset.hint)return {title:target.dataset.hintTitle||target.textContent,text:target.dataset.hint};
    const node=target.dataset.contextNode && target.dataset.contextCase===state.current?.slug && state.current.nodes.find(item=>item.id===target.dataset.contextNode);
    if(node)return {title:displayNodeLabel(node),text:[groups.find(group=>group[0]===node.category)?.[1],node.detail||node.question||"Rechtsklick öffnet die Befehle für diesen Baustein."].filter(Boolean).join(" · "),shortcut:"Umschalt+F10: Kontextmenü"};
    const term=target.dataset.contextTerm && state.vocabulary?.terms.find(item=>item.id===target.dataset.contextTerm);
    if(term)return {title:term.label,text:term.comment||"Gemeinsamer Begriff. Prüfe seine Bedeutung und Verwendung vor einer Änderung.",shortcut:"Umschalt+F10: Kontextmenü"};
    if(target.dataset.contextCase)return {title:target.textContent,text:"Öffnet die Fachvorlage dieser Vorgangsart. Rechtsklick zeigt die verfügbaren Befehle."};
    let hint=hints[target.id];
    if(hint){
      let text=hint[1];
      if(["save","save-current"].includes(target.id)&&target.disabled)text=saveFlow.pending?"Bitte den laufenden Speichervorgang abwarten.":!state.dirty?"Es gibt noch keine ungespeicherten Änderungen. Bearbeite zuerst einen Baustein in deinem Entwurf.":"Wechsle zum passenden Arbeitsentwurf, um diese Änderungen zu speichern.";
      else if(["new-node","add-node"].includes(target.id)&&target.disabled)text="Erstelle zuerst einen Arbeitsentwurf für die geöffnete Vorgangsart.";
      else if(target.id==="edit-node"&&state.nodeEditing)text="Zeigt den Baustein wieder als Lesefassung. Deine Eingaben bleiben im Entwurf erhalten.";
      else if(target.id==="edit-node"&&target.disabled)text=saveFlow.pending||nodeEditPending?"Bitte den laufenden Vorgang abwarten.":"Schließe zuerst den Entwurf für die andere Vorgangsart.";
      return {title:hint[0],text,shortcut:hint[2]};
    }
    const areas={understand:"Lies die Bedeutung der Bausteine und ihrer Beziehungen.",edit:"Pflege Bausteine und Beziehungen in einem eigenen Arbeitsentwurf.",review:"Reiche deinen Entwurf ein oder prüfe Änderungen anderer Personen."};
    const views={fall:"Zeigt die fachlichen Zusammenhänge als Graph.",bausteine:"Zeigt die Inhalte des ausgewählten Bausteins.",verbindungen:"Zeigt die Verbindungen zwischen den Bausteinen.",vokabular:"Zeigt die gemeinsamen Begriffe und ihre Verwendung.",pruefung:"Reiche deinen gespeicherten Entwurf mit Grund und Quellenstand ein.",fachpruefung:"Prüfe eingereichte Änderungen anderer Personen."};
    const help={start:"Kurze Einführung in die fachliche Arbeit mit editor8.",training:"Geführte Übungen mit vollständig künstlichen Beispielen.",handbook:"Anleitungen zur Ontologiepflege und notariellen Prüfung.",terms:"Erläutert die Begriffe der Oberfläche."};
    const text=areas[target.dataset.area]||views[target.dataset.viewButton]||help[target.dataset.helpTopic];
    if(text)return {title:target.textContent,text};
    if(target.matches("input,select,textarea")){
      const label=target.labels?.[0];
      const name=label && [...label.childNodes].filter(child=>child.nodeType===Node.TEXT_NODE).map(child=>child.textContent).join("").trim();
      const explanation=fieldHints[name?.split(" · ")[0]];
      if(explanation)return {title:name,text:explanation};
    }
    return null;
  }
  const tipSelector="[data-context-node],[data-context-term],[data-context-case],[data-hint],button,input,select,textarea";
  function stopTip() {
    clearTimeout(tipTimer);clearTimeout(hideTimer);
    if(tipTarget){
      const ids=(tipTarget.getAttribute("aria-describedby")||"").split(/\s+/).filter(id=>id&&id!==tooltip.id);
      if(ids.length)tipTarget.setAttribute("aria-describedby",ids.join(" "));else tipTarget.removeAttribute("aria-describedby");
    }
    tooltip.hidden=true;tipTarget=null;
  }
  function fit(popup,x,y) {
    const rect=popup.getBoundingClientRect();
    popup.style.left=Math.max(8,Math.min(x,innerWidth-rect.width-8))+"px";
    popup.style.top=Math.max(8,Math.min(y,innerHeight-rect.height-8))+"px";
  }
  function showTip(target,delay=450) {
    if(target===suppressed||(!menu.hidden&&!menu.contains(target)))return;
    stopTip();const hint=describe(target);if(!hint)return;
    target.removeAttribute("title");tipTarget=target;
    tipTimer=setTimeout(()=>{
      if(!target.isConnected||!target.getClientRects().length){stopTip();return;}
      (target.closest("dialog[open]")||document.body).append(tooltip);
      tooltip.replaceChildren(element("strong",hint.title),element("span",hint.text.slice(0,260)));
      if(hint.shortcut)tooltip.append(element("small",hint.shortcut));
      tooltip.hidden=false;tooltip.style.left="8px";tooltip.style.top="8px";
      const rect=target.getBoundingClientRect(), popup=tooltip.getBoundingClientRect();
      if(menu.contains(target)){
        const bounds=menu.getBoundingClientRect();
        if(bounds.right+4+popup.width<=innerWidth-8)fit(tooltip,bounds.right+4,rect.top);
        else if(bounds.left-popup.width-4>=8)fit(tooltip,bounds.left-popup.width-4,rect.top);
        else fit(tooltip,bounds.left,bounds.bottom+4+popup.height<=innerHeight-8?bounds.bottom+4:bounds.top-popup.height-4);
      }else fit(tooltip,rect.left,rect.bottom+4+popup.height>innerHeight-8?rect.top-popup.height-4:rect.bottom+4);
      const ids=new Set((target.getAttribute("aria-describedby")||"").split(/\s+/).filter(Boolean));ids.add(tooltip.id);target.setAttribute("aria-describedby",[...ids].join(" "));
    },delay);
  }
  document.addEventListener("pointerover",event=>{
    if(tooltip.contains(event.target)){clearTimeout(hideTimer);return;}
    const target=event.target.closest(tipSelector);
    if(target&&!target.contains(event.relatedTarget))showTip(target);
  });
  document.addEventListener("pointerout",event=>{
    if(suppressed?.contains(event.target)&&!suppressed.contains(event.relatedTarget))suppressed=null;
    if((tipTarget?.contains(event.target)||tooltip.contains(event.target))&&!tipTarget?.contains(event.relatedTarget)&&!tooltip.contains(event.relatedTarget)){
      suppressed=null;hideTimer=setTimeout(stopTip,120);
    }
  });
  document.addEventListener("focusin",event=>{
    const target=event.target.closest(tipSelector);if(target?.matches(":focus-visible"))showTip(target,100);
  });
  document.addEventListener("focusout",event=>{if(suppressed?.contains(event.target))suppressed=null;if(tipTarget?.contains(event.target))stopTip();});

  function contextFor(target) {
    if(target.closest("input,textarea,select,[contenteditable]:not([contenteditable=false]),dialog,[role=menu]"))return null;
    const item=target.closest("[data-context-node],[data-context-term],[data-context-case]");
    if(item)return {kind:item.dataset.contextNode?"node":item.dataset.contextTerm?"term":"case",id:item.dataset.contextNode||item.dataset.contextTerm||item.dataset.contextCase,slug:item.dataset.contextCase,trigger:item};
    if(state.current&&target.closest("#graph-stage,#case-list,#node-detail-panel"))return {kind:"case",id:state.current.slug,slug:state.current.slug,trigger:target.closest("#graph-stage,#case-list,#node-detail-panel")};
    return null;
  }
  function actions(context) {
    const waiting=!!saveFlow.pending||nodeEditPending;
    const result=[];
    const add=(id,label,disabled=false,hint="",icon="")=>result.push({id,label,disabled,hint,icon});
    if(context.kind==="node"){
      const node=context.slug===state.current?.slug&&state.current.nodes.find(item=>item.id===context.id);if(!node)return [];
      add("open","Öffnen",waiting||state.view==="vokabular", "Zeigt die Inhalte dieses Bausteins.","file-open");
      const mayEdit=!waiting&&state.view!=="vokabular"&&(state.branch==="main"||caseEditable());
      add("edit","Bearbeiten",!mayEdit,waiting?"Bitte den laufenden Vorgang abwarten.":mayEdit?"Ändert diesen Baustein in deinem Arbeitsentwurf.":"Schließe zuerst den Entwurf für den anderen Arbeitsbereich.","start-branch");
      add("relations","Verbindungen",waiting||state.view==="vokabular","Zeigt die Beziehungen dieses Bausteins.");
      if(node.id.startsWith("local."))add("delete","Entfernen",waiting||!caseEditable(),"Entfernt diesen zusätzlich angelegten Baustein und seine Verbindungen nach deiner Bestätigung.");
      add("separator");
      add("help","Hilfe zur Auswahl",waiting||state.view==="vokabular","Erläutert den fachlichen Kontext dieses Bausteins.","selection-help");
    }else if(context.kind==="term"){
      if(state.view!=="vokabular"||!state.vocabulary?.terms.some(term=>term.id===context.id))return [];
      add("open","Öffnen",waiting,"Zeigt Bedeutung und Verwendung dieses gemeinsamen Begriffs.","file-open");
      const mayEdit=state.ontologyMaintainer&&(state.branch==="main"||state.purpose==="vocabulary");
      add("edit","Bearbeiten",waiting||!mayEdit,waiting?"Bitte den laufenden Vorgang abwarten.":!state.ontologyMaintainer?"Die Pflege gemeinsamer Begriffe benötigt eine zusätzliche fachliche Berechtigung.":mayEdit?"Ändert diesen Begriff in deinem Arbeitsentwurf.":"Schließe zuerst den laufenden Fallentwurf.","start-branch");
      add("help","Hilfe zur Auswahl",waiting,"Erläutert Bedeutung und Pflege gemeinsamer Begriffe.","selection-help");
    }else{
      if(!state.cases.some(item=>item.slug===context.id))return [];
      add("open","Öffnen",waiting,"Öffnet diese Vorgangsart.","file-open");
      add("info","Informationen",waiting,"Zeigt Beschreibung, Quellen und frühere Fassungen.");
      add("print","Drucken",waiting,"Druckt eine Lesefassung dieser Vorgangsart.","print");
    }
    if(context.kind!=="case"||context.id===state.current?.slug){
      add("separator");
      add("save","Speichern",waiting||$("save").disabled,waiting?"Bitte den laufenden Speichervorgang abwarten.":state.dirty?"Prüft und speichert deinen Arbeitsentwurf.":"Es gibt noch keine ungespeicherten Änderungen.","save");
    }
    return result;
  }
  function closeMenu(restore=false) {
    if(menu.hidden)return;
    menu.hidden=true;origin?.removeAttribute("aria-expanded");
    const context=menuContext;menuContext=null;
    if(restore){
      const replacement=[...document.querySelectorAll("[data-context-node],[data-context-term],[data-context-case]")].find(item=>context?.kind==="node"?item.dataset.contextNode===context.id&&item.dataset.contextCase===context.slug:context?.kind==="term"?item.dataset.contextTerm===context.id:item.dataset.contextCase===context?.id&&!item.dataset.contextNode);
      const focus=origin?.isConnected?origin:replacement;
      if(focus?.matches("button,[tabindex]"))focus.focus({preventScroll:true});
      else if(returnFocus?.isConnected)returnFocus.focus({preventScroll:true});
    }
  }
  function showMenu(context,x,y) {
    const commands=actions(context);if(!commands.length)return false;
    stopTip();closeMenu();menuContext=context;origin=context.trigger;returnFocus=document.activeElement;origin.setAttribute("aria-expanded","true");
    const title=context.kind==="node"?nodeLabel(context.id):context.kind==="term"?state.vocabulary.terms.find(term=>term.id===context.id).label:state.cases.find(item=>item.slug===context.id).title;
    menu.setAttribute("aria-label","Befehle für "+title);menu.replaceChildren(element("div",title,"context-heading"));
    commands.forEach(command=>{
      if(command.id==="separator"){const line=element("div",undefined,"context-separator");line.setAttribute("role","separator");menu.append(line);return;}
      const button=element("button",undefined,"context-command");button.type="button";button.setAttribute("role","menuitem");button.setAttribute("aria-label",command.label);button.tabIndex=-1;button.disabled=command.disabled;button.setAttribute("aria-disabled",String(command.disabled));button.dataset.command=command.id;button.dataset.hint=command.hint;button.dataset.hintTitle=command.label;
      const icon=$(command.icon)?.querySelector("svg")?.cloneNode(true)||element("span");icon.classList.add("context-icon");icon.setAttribute("aria-hidden","true");button.append(icon,element("span",command.label));
      if(command.id==="save"){button.append(element("small","Strg+S"));button.setAttribute("aria-keyshortcuts","Control+s");}
      button.addEventListener("click",()=>run(command.id,context).catch(error=>notice(error.message,"error")));menu.append(button);
    });
    menu.hidden=false;menu.style.left="8px";menu.style.top="8px";fit(menu,x,y);
    (menu.querySelector("button:not(:disabled)")||menu).focus({preventScroll:true});return true;
  }
  async function run(id,context) {
    // Re-evaluate permission and draft state when invoking, not just on opening.
    const command=actions(context).find(item=>item.id===id);if(!command||command.disabled){closeMenu(true);return;}
    closeMenu();
    if(id==="save"){await save();return;}
    if(context.kind==="node"){
      if(id==="edit"){await beginNodeEdit(context.id,true);return;}
      if(id==="delete"){
        office.graphEdit=true;selectNode(context.id);state.nodeEditing=true;renderNodeForm();$("delete-node").click();return;
      }
      if(id==="open"){office.graphEdit=false;selectNode(context.id);$("detail-title").tabIndex=-1;$("detail-title").focus({preventScroll:true});}
      if(id==="relations"){office.graphEdit=false;setView("fall");focusGraphNode(context.id);}
      if(id==="help"){state.selected=context.id;state.nodeEditing=false;renderAll();selectionHelp();}
    }else if(context.kind==="term"){
      state.vocabSelected=context.id;state.vocabEditing=false;state.vocabNew=false;renderVocabulary();
      if(id==="edit")await editVocabulary();
      else if(id==="help")selectionHelp();
      else{$("vocab-title").tabIndex=-1;$("vocab-title").focus({preventScroll:true});}
    }else{
      // Switching to a different case retains the existing unsaved-change guard.
      if(context.id!==state.current?.slug){await loadCase(context.id);if(state.current?.slug!==context.id)return;}
      else if(state.dirty&&state.view==="vokabular"){notice("Bitte zuerst die offenen Änderungen an gemeinsamen Begriffen speichern.","error");return;}
      office.graphEdit=false;setView("fall");
      if(id==="info")$("source-open").click();
      if(id==="print")printSelection();
    }
  }
  document.addEventListener("contextmenu",event=>{
    const context=contextFor(event.target);if(!context)return;
    if(showMenu(context,event.clientX,event.clientY))event.preventDefault();
  });
  document.addEventListener("keydown",event=>{
    if(event.key==="Escape"&&!menu.hidden){event.preventDefault();event.stopImmediatePropagation();closeMenu(true);stopTip();return;}
    if(event.key==="Escape"&&!tooltip.hidden){event.preventDefault();event.stopImmediatePropagation();suppressed=tipTarget;stopTip();return;}
    if(event.key==="ContextMenu"||(event.shiftKey&&event.key==="F10")){
      const context=contextFor(event.target);if(!context)return;const rect=context.trigger.getBoundingClientRect();
      if(showMenu(context,rect.left,rect.bottom)){event.preventDefault();event.stopImmediatePropagation();}return;
    }
    if(menu.hidden)return;
    if(event.key==="Tab"){closeMenu(true);return;}
    if(!["ArrowDown","ArrowUp","Home","End"].includes(event.key))return;
    event.preventDefault();event.stopImmediatePropagation();
    const items=[...menu.querySelectorAll("button:not(:disabled)")],current=items.indexOf(document.activeElement);
    const next=event.key==="Home"?0:event.key==="End"?items.length-1:(current+(event.key==="ArrowUp"?-1:1)+items.length)%items.length;
    items[next]?.focus();
  },true);
  document.addEventListener("pointerdown",event=>{stopTip();suppressed=null;if(!menu.contains(event.target))closeMenu();},true);
  document.addEventListener("scroll",event=>{
    stopTip();
    // Text fields can scroll their caret on blur; this does not move the menu's object.
    if(event.target.matches?.("input,textarea,select")||menu.contains(event.target))return;
    closeMenu();
  },true);
  document.addEventListener("editor-state-change",()=>{stopTip();closeMenu();});
  window.addEventListener("resize",()=>{stopTip();closeMenu();});
  window.addEventListener("blur",()=>{stopTip();closeMenu();});
})();
