import { build } from "esbuild";
import { mkdir, copyFile } from "node:fs/promises";
await mkdir("dist", { recursive: true });
await build({
  entryPoints: ["web/app.jsx"],
  bundle: true,
  format: "esm",
  outfile: "dist/app.js",
  minify: true,
  define: { "process.env.NODE_ENV": '"production"' },
  logLevel: "info",
});
await copyFile("web/style.css", "dist/style.css");
