// SPDX-License-Identifier: AGPL-3.0-or-later
// Shared display tools. The data adapter owns field meanings and validation.
"use strict";
window.EditorGuidance = (() => {
  function field(root, label, value, onChange, options = {}) {
    const wrap = document.createElement("div");
    const caption = document.createElement("label");
    caption.textContent = label + (options.hint ? " · " + options.hint : "");
    const control = document.createElement(options.multiline ? "textarea" : "input");
    control.value = value ?? "";
    control.disabled = !!options.disabled;
    if (options.multiline) control.rows = 3;
    control.addEventListener("input", () => onChange(control.value));
    caption.append(control); wrap.append(caption);
    if (options.description) {
      const hint = document.createElement("p");
      hint.className = "field-guidance";
      hint.textContent = options.description;
      hint.id = "field-guidance-" + (++field.count);
      control.setAttribute("aria-describedby", hint.id);
      wrap.append(hint);
    }
    root.append(wrap);
    return control;
  }
  field.count = 0;

  function connection(nodes, edge, labels, metadata = {}) {
    const source = nodes.find(node => node.id === edge.from);
    const target = nodes.find(node => node.id === edge.to);
    if (!source || !target) return {ready: false, sentence: "Wähle Ausgang und Ziel. Prüfe anschließend die Richtung der Verbindung."};
    if (!Object.hasOwn(labels, edge.type)) return {ready: false, sentence: "Wähle eine Beziehung aus dem Fachmodell."};
    const sentence = `„${source.label}“ ${labels[edge.type]} „${target.label}“.`;
    const info = metadata[edge.type] || {};
    const hints = [];
    if (info.description) hints.push(info.description);
    if (info.domain?.length) hints.push("Im Vokabular beschrieben für: " + info.domain.map(item => item.label).join(", ") + ".");
    if (info.range?.length) hints.push("Im Vokabular beschriebenes Ziel: " + info.range.map(item => item.label).join(", ") + ".");
    if (!hints.length) hints.push("Zu dieser Beziehung ist im Vokabular keine zusätzliche Erläuterung hinterlegt.");
    hints.push("Die Hinweise ersetzen keine fachliche Prüfung.");
    return {ready: true, sentence, hints: hints.join(" ")};
  }
  return {field, connection};
})();
