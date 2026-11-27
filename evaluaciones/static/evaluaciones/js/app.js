const CSRF_TOKEN = document.querySelector("[name=csrfmiddlewaretoken]").value;
const NOMBRES_NIVEL = ["", "Irrelevante", "Opcional", "Importante", "Fundamental"];

async function enviarJson(url, contenido) {
  const respuesta = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF_TOKEN },
    body: JSON.stringify(contenido),
  });
  return respuesta.json();
}

function mostrarPorque(fila) {
  const panel = document.getElementById("porque");
  const filasMarcadas = document.querySelectorAll("tr.marcado");
  for (const filaMarcada of filasMarcadas) {
    filaMarcada.classList.remove("marcado");
  }
  fila.classList.add("marcado");
  const factor = fila.dataset;
  const valoresPanel = { ie: factor.ie, il: NOMBRES_NIVEL[factor.il], is: NOMBRES_NIVEL[factor.is], id: NOMBRES_NIVEL[factor.id], ir: NOMBRES_NIVEL[factor.ir] };
  panel.querySelector("h3").textContent = factor.nombre;
  for (const campo in valoresPanel) {
    const celda = panel.querySelector(`[data-campo=${campo}]`);
    celda.textContent = valoresPanel[campo];
  }
}

async function guardarFactor(fila) {
  const alcance = fila.querySelector("select");
  const importancia = await enviarJson(fila.dataset.url, { imp_decisor: fila.dataset.id, alcance: alcance.value });
  const etiquetaRelativa = fila.querySelector(".ir");
  fila.dataset.ir = importancia.ir;
  etiquetaRelativa.className = `pildora ir n${importancia.ir}`;
  etiquetaRelativa.textContent = importancia.ir_texto;
  document.getElementById("relevantes").textContent = importancia.relevantes;
  mostrarPorque(fila);
}

function elegirImportancia(evento) {
  const botonElegido = evento.currentTarget;
  const fila = botonElegido.closest("tr");
  const botones = fila.querySelectorAll(".segmento button");
  for (const boton of botones) {
    boton.classList.toggle("activo", boton === botonElegido);
  }
  fila.dataset.id = botonElegido.value;
  guardarFactor(fila);
}

function cambiarAlcance(evento) {
  const fila = evento.currentTarget.closest("tr");
  guardarFactor(fila);
}

function verPorque(evento) {
  evento.preventDefault();
  const fila = evento.currentTarget.closest("tr");
  mostrarPorque(fila);
}

async function calificarSubfactor(evento) {
  const opcion = evento.currentTarget;
  const bloque = opcion.closest("details");
  const avance = await enviarJson(bloque.dataset.url, { subfactor: opcion.dataset.sub, valor: opcion.value });
  const estado = bloque.querySelector(".estado");
  const barra = document.getElementById("barra");
  bloque.querySelector(".respondidos").textContent = avance.respondidos;
  bloque.querySelector(".pm").textContent = avance.pm || "–";
  estado.className = `pildora estado ${avance.foda}`;
  estado.textContent = avance.foda || "Pendiente";
  document.getElementById("hechos").textContent = avance.hechos;
  barra.style.width = `${(100 * avance.hechos) / avance.total}%`;
  document.getElementById("ver-resultado").disabled = avance.hechos < avance.total;
}

function verResultado(evento) {
  location.href = evento.currentTarget.dataset.url;
}

function seleccionadas() {
  const marcadas = document.querySelectorAll("#comparar input[type=checkbox]:checked");
  const identificadores = [];
  for (const marcada of marcadas) {
    identificadores.push(marcada.value);
  }
  return identificadores;
}

function actualizarComparacion() {
  const evaluaciones = seleccionadas();
  document.getElementById("btn-comparar").disabled = evaluaciones.length !== 2;
}

function comparar(evento) {
  evento.preventDefault();
  const evaluaciones = seleccionadas();
  location.href = `${evento.currentTarget.action}?a=${evaluaciones[0]}&b=${evaluaciones[1]}`;
}

function escuchar(selector, tipoEvento, manejador) {
  const elementos = document.querySelectorAll(selector);
  for (const elemento of elementos) {
    elemento.addEventListener(tipoEvento, manejador);
  }
}

function iniciar() {
  escuchar("tr[data-ef] .segmento button", "click", elegirImportancia);
  escuchar("tr[data-ef] select", "change", cambiarAlcance);
  escuchar("tr[data-ef] .ver-porque", "click", verPorque);
  escuchar("details[data-ef] input[type=radio]", "change", calificarSubfactor);
  escuchar("#ver-resultado", "click", verResultado);
  escuchar("#comparar input[type=checkbox]", "change", actualizarComparacion);
  escuchar("#comparar", "submit", comparar);
}

const Guios = { enviarJson, mostrarPorque, guardarFactor, calificarSubfactor, comparar, iniciar };
Guios.iniciar();
export default Guios;
