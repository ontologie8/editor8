// SPDX-License-Identifier: AGPL-3.0-or-later
"use strict";
window.EditorComparison = (() => {
  const names={added:"Hinzugefügt",removed:"Entfernt",changed:"Geändert",unchanged:"Unverändert"};
  const ns="http://www.w3.org/2000/svg";
  const el=(tag,text,cls)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(cls)node.className=cls;return node;};
  const svg=(tag,attrs={})=>{const node=document.createElementNS(ns,tag);for(const [key,value]of Object.entries(attrs))node.setAttribute(key,value);return node;};
  function render(root,comparison,relations={}){
    root.replaceChildren();root.hidden=!comparison;if(!comparison)return;
    const relationLabels={parent:"ist Unterklasse von",domain:"gilt für",range:"hat Zielklasse",...relations};
    root.append(el("h3","Vorher / Nachher"));
    const counts=comparison.node_changes;const edges=comparison.edge_changes;
    root.append(el("p",`${counts.added} Bausteine hinzugefügt · ${counts.removed} entfernt · ${counts.changed} geändert · ${edges.added} Beziehungen hinzugefügt · ${edges.removed} entfernt`,"comparison-summary"));
    const legend=el("div",undefined,"comparison-legend");
    for(const [status,label]of Object.entries(names))legend.append(el("span",label,"diff-"+status));root.append(legend);
    const panes=el("div",undefined,"comparison-panes");const detail=el("div","Wähle einen Baustein, um seine Angaben vor und nach der Änderung zu vergleichen.","comparison-detail");detail.setAttribute("aria-live","polite");
    const all=new Map([...comparison.before.nodes,...comparison.after.nodes].map(node=>[node.id,node]));
    const columns=new Map();const positions=new Map();
    const categoryColumn={required_information:0,documents:1,evidence:1,decisions:2,gates:2,class:0,object_property:1,datatype_property:2};
    [...all.values()].sort((a,b)=>a.id.localeCompare(b.id)).forEach(node=>{const column=categoryColumn[node.category]??0;const row=columns.get(column)||0;positions.set(node.id,{x:12+column*188,y:12+row*82});columns.set(column,row+1);});
    function inspect(id){
      detail.replaceChildren();const before=comparison.before.nodes.find(node=>node.id===id),after=comparison.after.nodes.find(node=>node.id===id);
      detail.append(el("strong",(after||before).label));
      const labels={label:"Bezeichnung",category:"Art",status:"Status",question:"Fachfrage",detail:"Erläuterung",section:"Kapitel",owner_role:"Rolle",privacy_class:"Datenschutzklasse",required_for:"Benötigt für",options:"Optionen",document_source:"Dokumentquelle",contains_personal_data:"Personendaten-Hinweis",comment:"Erläuterung",parent:"Oberklasse",domain:"Gilt für",range:"Zielklasse oder Datentyp",kind:"Art"};
      for(const [field,label]of Object.entries(labels)){const a=before?.[field],b=after?.[field];if(JSON.stringify(a)===JSON.stringify(b))continue;detail.append(el("p",label+": "+(Array.isArray(a)?a.join(", "):a??"(leer)")+" → "+(Array.isArray(b)?b.join(", "):b??"(leer)")));}
      for(const side of [comparison.before,comparison.after])for(const edge of side.edges.filter(edge=>edge.change!=="unchanged"&&(edge.from===id||edge.to===id)))detail.append(el("p",names[edge.change]+": "+all.get(edge.from)?.label+" → "+(relationLabels[edge.type]||edge.type)+" → "+all.get(edge.to)?.label));
    }
    for(const [side,label]of [["before","Vorher"],["after","Nachher"]]){
      const data=comparison[side];const panel=el("section",undefined,"comparison-pane");panel.append(el("h4",label));
      const scroll=el("div",undefined,"comparison-scroll");scroll.tabIndex=0;scroll.setAttribute("role","region");scroll.setAttribute("aria-label",label+": Änderungsgraph");
      if(!data.nodes.length)scroll.append(el("p","Keine Baustein- oder Beziehungsänderung. Prüfe Beschreibung, Quellen oder weitere Angaben im Textvergleich."));
      else{
        const canvas=svg("svg",{viewBox:`0 0 576 ${Math.max(112,...[...columns.values()].map(count=>count*82+12))}`,role:"group","aria-label":label+": Bausteine und Beziehungen"});
        canvas.style.height=Math.max(112,...[...columns.values()].map(count=>count*82+12))+"px";
        const ids=new Set(data.nodes.map(node=>node.id));
        for(const edge of data.edges){if(!ids.has(edge.from)||!ids.has(edge.to))continue;const a=positions.get(edge.from),b=positions.get(edge.to);const path=svg("path",{d:`M ${a.x+160} ${a.y+28} C ${a.x+190} ${a.y+28}, ${b.x-24} ${b.y+28}, ${b.x} ${b.y+28}`,class:"comparison-edge diff-"+edge.change});const title=svg("title");title.textContent=names[edge.change]+": "+all.get(edge.from).label+" → "+edge.type+" → "+all.get(edge.to).label;path.append(title);canvas.append(path);canvas.append(svg("path",{d:`M ${b.x-7} ${b.y+24} L ${b.x} ${b.y+28} L ${b.x-7} ${b.y+32}`,class:"comparison-edge diff-"+edge.change}));}
        for(const node of data.nodes){const p=positions.get(node.id);const button=svg("g",{role:"button",tabindex:"0","aria-label":names[node.change]+": "+node.label,class:"comparison-node diff-"+node.change,"data-node-id":node.id});
          button.append(svg("rect",{x:p.x,y:p.y,width:164,height:62,rx:3}));
          const text=svg("text",{x:p.x+8,y:p.y+20});const first=svg("tspan",{x:p.x+8});first.textContent=names[node.change];text.append(first);const second=svg("tspan",{x:p.x+8,dy:20});second.textContent=node.label.length>21?node.label.slice(0,20)+"…":node.label;text.append(second);button.append(text);
          const title=svg("title");title.textContent=node.label;button.append(title);
          button.addEventListener("click",()=>inspect(node.id));button.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();inspect(node.id);}});canvas.append(button);}
        scroll.append(canvas);
      }
      panel.append(scroll,el("p",`${data.nodes.length} von ${data.total_nodes} Bausteinen: Änderung und direktes Umfeld.`,"context-help"));panes.append(panel);
    }
    root.append(panes,detail,el("p",`${comparison.rdf_added} Modellaussagen hinzugefügt, ${comparison.rdf_removed} entfernt. Fachliche Folgen sind zu prüfen.`,"context-help"));
  }
  return {render};
})();
