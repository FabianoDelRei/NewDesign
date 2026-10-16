const express = require("express");
const app = express();
const port = 3000;

// Converte o parâmetro para inteiro ou retorna null se for inválido
function parseDecimal(value) {
  return /^-?\d+$/.test(value) ? parseInt(value, 10) : null;
}

// Decimal para binário
app.get("/to-binary/:decimal", (req, res) => {
  const decimal = parseDecimal(req.params.decimal);
  if (decimal === null) {
    return res.status(400).json({ error: "Invalid decimal number" });
  }
  res.json({ decimal, binary: decimal.toString(2) });
});

// Decimal para hexadecimal (maiúsculas)
app.get("/to-hex/:decimal", (req, res) => {
  const decimal = parseDecimal(req.params.decimal);
  if (decimal === null) {
    return res.status(400).json({ error: "Invalid decimal number" });
  }
  res.json({ decimal, hex: decimal.toString(16).toUpperCase() });
});

app.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
});
