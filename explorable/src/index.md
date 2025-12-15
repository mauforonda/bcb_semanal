---
theme: ["light", "ocean-floor"]
---

<link rel="stylesheet" href="style.css">

```js
import * as hyparquet from "npm:hyparquet";
import * as compressors from "npm:hyparquet-compressors";
```

```js
const dark = Generators.dark();
```

```js
const gh =
  "https://raw.githubusercontent.com/mauforonda/bcb_semanal/refs/heads/main/";
```

```js
const arrayBuffer = await fetch(`${gh}/datos.parquet`).then((d) =>
  d.arrayBuffer()
);

const data = await new Promise((resolve) =>
  hyparquet.parquetRead({
    file: arrayBuffer,
    compressors: compressors.compressors,
    onComplete: (raw) => {
      const processed = raw.map((arr) => ({
        unidad: arr[0],
        categoria: arr[1],
        variable: arr[2],
        subvariable: arr[3],
        fecha: arr[4],
        valor: arr[5],
      }));
      resolve(processed);
    },
  })
);
```

```js
const variables = Object.fromEntries(
  d3.rollup(
    data,
    (v) => [...new Set(v.map((d) => d.variable))],
    (d) => d.categoria
  )
);
```

```js
const categoria_input = Inputs.radio(Object.keys(variables), {
  value: "Operaciones con el exterior",
});
const categoria = Generators.input(categoria_input);
```

```js
const variable_input = Inputs.radio(variables[categoria], {
  value: variables[categoria][0],
});
const variable = Generators.input(variable_input);
```

```js
const light_colors = {
  frame: "#a2a2a2",
  background: "#eff4f4",
  line: "#555555",
  fill: "#d3d8da",
  focus_primary: "#6c95bdff",
  focus_secondary: "#adc0d3ff",
};

const dark_colors = {
  frame: "#757684ff",
  background: "#212132ff",
  line: "#819acaff",
  fill: "#32344aff",
  focus_primary: "#dfe3f8ff",
  focus_secondary: "#9397c6ff",
};

const colors = dark ? dark_colors : light_colors;

const formatoFecha = new Intl.DateTimeFormat("es", {
  year: "numeric",
  month: "long",
  day: "numeric",
  timeZone: "UTC",
});
```

```js
function plot_silueta(desagregado, height) {
  // const desagregado = data.filter((d) => d.variable == variable);
  const unidad = desagregado[0].unidad;
  const serie = d3
    .rollups(
      desagregado,
      (v) => d3.sum(v, (d) => d.valor),
      (d) => d.fecha
    )
    .map(([fecha, valor]) => ({ fecha, valor }));

  const params = {
    axis: {
      fontWeight: 600,
      fontSize: 12,
      tickSize: 0,
      label: null,
    },
    text_secondary: {
      fontWeight: 600,
      fontSize: 12,
      fill: colors.focus_secondary,
    },
    text_primary: {
      fontWeight: 800,
      fontSize: 20,
      fill: colors.focus_primary,
    },
  };

  const miles = Math.max(...serie.map((d) => d.valor)) > 1e4;
  const formatter = miles ? (d) => d / 1e3 : (d) => d;
  const suffix = miles ? "mil" : "";

  const tickFormat = (d, i, _) =>
    i === _.length - 1
      ? `${formatter(d)} ${suffix}`
      : d === 0
      ? ""
      : formatter(d);

  const default_pointer = (
    index,
    scales,
    values,
    dimensions,
    context,
    next
  ) => {
    const i = index.length > 0 ? index[0] : serie.length - 1;
    return next([i], scales, values, dimensions, context);
  };

  const follow_pointer = (index, scales, values, dimensions, context, next) => {
    const i = index.length > 0 ? index[0] : serie.length - 1;
    const X = values.x ?? values.x1;
    const x0 = X[i];
    const newIndex = Array.from(X, (_, i) => i).filter((i) => X[i] <= x0);
    return next(newIndex, scales, values, dimensions, context);
  };

  const plot = Plot.plot({
    className: "plot",
    height: width < 768 ? 350 : 550,
    width: width < 768 ? width : 980,
    marginTop: 70,
    marginLeft: 30,
    marginRight: 40,
    marginBottom: 40,
    style: {
      color: colors.frame,
      background: colors.background,
    },
    x: {
      insetRight: 25,
    },
    y: {
      insetTop: 15,
    },
    marks: [
      Plot.axisX({ ...params.axis }),
      Plot.axisY({
        ...params.axis,
        anchor: "right",
        dx: -24,
        dy: 10,
        lineAnchor: "top",
        tickFormat: tickFormat,
      }),
      Plot.ruleY([0], {
        strokeWidth: 1.5,
      }),
      Plot.areaY(serie, {
        x: "fecha",
        y: "valor",
        fill: colors.fill,
        fillOpacity: 0.5,
      }),
      Plot.areaY(
        serie,
        Plot.pointerX({
          x: "fecha",
          y: "valor",
          fill: colors.fill,
          fillOpacity: 1,
          render: follow_pointer,
        })
      ),
      Plot.gridY({
        strokeOpacity: 0.8,
        strokeWidth: 0.7,
        strokeDasharray: "4 3",
      }),
      Plot.line(
        serie,
        Plot.pointerX({
          x: "fecha",
          y: "valor",
          stroke: colors.line,
          strokeWidth: 3,
          render: follow_pointer,
        })
      ),
      Plot.ruleX(
        serie,
        Plot.pointerX({
          x: "fecha",
          py: "valor",
          stroke: colors.line,
          strokeOpacity: 0.8,
          strokeWidth: 2.5,
          strokeDasharray: "4 3",
          render: default_pointer,
        })
      ),
      Plot.dot(
        serie,
        Plot.pointerX({
          x: "fecha",
          y: "valor",
          fill: colors.focus_primary,
          stroke: colors.line,
          strokeWidth: 3,
          r: 6,
          render: default_pointer,
        })
      ),
      Plot.text(
        serie,
        Plot.pointerX({
          text: (d) => formatoFecha.format(d.fecha),
          px: "fecha",
          dy: -30,
          lineAnchor: "bottom",
          textAnchor: "start",
          frameAnchor: "top-left",
          render: default_pointer,
          ...params.text_secondary,
        })
      ),
      Plot.text(
        serie,
        Plot.pointerX({
          text: (d) => d.valor,
          px: "fecha",
          dy: -30,
          dx: -25,
          lineAnchor: "bottom",
          textAnchor: "end",
          frameAnchor: "top-right",
          render: default_pointer,
          ...params.text_primary,
        })
      ),
      Plot.text(
        serie,
        Plot.pointerX({
          text: (d) => unidad,
          dx: -25,
          dy: -20,
          px: "fecha",
          textAnchor: "end",
          frameAnchor: "top-right",
          lineAnchor: "top",
          stroke: colors.background,
          render: default_pointer,
          ...params.text_secondary,
        })
      ),
    ],
  });
  return plot;
}
```

```js
function download(value, name = "untitled", label = "Save") {
  const a = document.createElement("a");
  const b = a.appendChild(document.createElement("button"));
  b.textContent = label;
  a.download = name;

  async function reset() {
    await new Promise(requestAnimationFrame);
    URL.revokeObjectURL(a.href);
    a.removeAttribute("href");
    b.textContent = label;
    b.disabled = false;
  }

  a.onclick = async (event) => {
    b.disabled = true;
    if (a.href) return reset(); // Already saved.
    b.textContent = "Saving…";
    try {
      const object = await (typeof value === "function" ? value() : value);
      b.textContent = "Download";
      a.href = URL.createObjectURL(object); // eslint-disable-line require-atomic-updates
    } catch (ignore) {
      b.textContent = label;
    }
    if (event.eventPhase) return reset(); // Already downloaded.
    b.disabled = false;
  };

  return a;
}
```

```js
function descarga(data, filename, mensaje) {
  const downloadData = new Blob([d3.csvFormat(data)], { type: "text/csv" });
  return download(downloadData, filename, mensaje);
}
```

```js
const desagregado = data.filter((d) => d.variable == variable);
const silueta = plot_silueta(desagregado);
const table = Inputs.table(desagregado, {
  sort: "fecha",
  columns:
    width < 768
      ? ["subvariable", "fecha", "valor", "unidad"]
      : ["variable", "subvariable", "fecha", "valor", "unidad"],
  reverse: true,
  select: false,
});
```

<cuerpo>
  <header>Reportes del Banco Central del Bolivia</header>
  <menu>
    <categorias>${categoria_input}</categorias>
    <variables>${variable_input}</variables>
  </menu>
  <grafico>
    <titulo>${variable}</titulo>
    <card>${silueta}</card>
  </grafico>
  <tabla>${table}</tabla>
  <descargas>${descarga(desagregado, "data.csv", "Descarga esta tabla en formato CSV")}</descargas>
</cuerpo>
