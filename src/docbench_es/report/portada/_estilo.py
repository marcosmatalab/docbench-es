"""La hoja de estilo de la portada. **Un fichero aparte, y con una razón.**

Son ~200 líneas de CSS que no cambian cuando cambia un número, mezcladas con la
plantilla harían imposible leer dónde entra cada cifra — y la plantilla es justo el sitio
donde este proyecto no quiere que se pueda esconder nada.

**Va en línea en el HTML, no en un `.css` aparte**, porque la página tiene que poder
abrirse desde el sistema de ficheros de quien clone el repo, sin servidor. Un `<link>` a
un fichero hermano funciona en GitHub Pages y falla en un `file://` con la carpeta a
medias; una portada que se ve rota es peor que una fea.

Las tipografías sí van por `<link>` y **con pila de reserva completa**: si no cargan
—sin red, o el clon en un tren— la página sale en Georgia y en la mono del sistema, con
la misma retícula. Ninguna cifra depende de ellas.
"""

from __future__ import annotations

__all__ = ["ESTILO", "FUENTES"]

FUENTES = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    "family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700"
    '&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">'
)

ESTILO = """:root{
  --paper:#F1F2F0; --panel:#FFFFFF; --ink:#15181A; --ink-soft:#59626A;
  --ink-faint:#8A9299; --rule:#D2D6D3; --rule-soft:#E3E6E3;
  --errata:#96271F; --errata-wash:#F7EAE8; --gauge:#37596B; --gauge-wash:#E9EFF2;
  --sans:"IBM Plex Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  --serif:"Source Serif 4",Georgia,"Times New Roman",serif;
  --mono:"IBM Plex Mono",ui-monospace,"SF Mono",Menlo,monospace;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --paper:#131618; --panel:#191D20; --ink:#E5E7E4; --ink-soft:#8B949B;
    --ink-faint:#6B747B; --rule:#282D31; --rule-soft:#202528;
    --errata:#D9695B; --errata-wash:#241A19; --gauge:#7FA5B7; --gauge-wash:#181F23;
  }
}
:root[data-theme="dark"]{
  --paper:#131618; --panel:#191D20; --ink:#E5E7E4; --ink-soft:#8B949B;
  --ink-faint:#6B747B; --rule:#282D31; --rule-soft:#202528;
  --errata:#D9695B; --errata-wash:#241A19; --gauge:#7FA5B7; --gauge-wash:#181F23;
}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--ink);font-family:var(--serif);font-size:17px;
  line-height:1.62;margin:0;-webkit-font-smoothing:antialiased}
.wrap{max-width:860px;margin:0 auto;padding:0 28px 96px}
@media(max-width:640px){.wrap{padding:0 18px 64px}}
p{margin:0 0 1.05em;max-width:66ch}
a{color:var(--gauge);text-decoration:none;
  border-bottom:1px solid color-mix(in srgb,var(--gauge) 35%,transparent)}
a:hover{border-bottom-color:var(--gauge)}
a:focus-visible{outline:2px solid var(--gauge);outline-offset:3px;border-radius:2px}
strong{font-weight:600}
code,.mono{font-family:var(--mono);font-size:.88em;font-variant-numeric:tabular-nums}
.masthead{border-bottom:2px solid var(--ink);padding:64px 0 20px;margin-bottom:8px}
@media(max-width:640px){.masthead{padding-top:40px}}
.wordmark{font-family:var(--sans);font-weight:700;font-size:clamp(34px,6vw,52px);
  letter-spacing:-.025em;line-height:1;margin:0 0 14px;text-wrap:balance}
.wordmark span{color:var(--ink-faint);font-weight:500}
.standfirst{font-family:var(--serif);font-size:clamp(17px,2.2vw,20px);
  color:var(--ink-soft);max-width:58ch;margin:0 0 22px}
.strip{display:flex;flex-wrap:wrap;gap:0 26px;font-family:var(--mono);font-size:12px;
  color:var(--ink-faint);padding-bottom:2px}
.strip b{color:var(--ink-soft);font-weight:500}
section{padding-top:52px}
.eyebrow{font-family:var(--sans);font-size:11.5px;font-weight:600;letter-spacing:.13em;
  text-transform:uppercase;color:var(--ink-faint);margin:0 0 10px}
h2{font-family:var(--sans);font-weight:600;font-size:clamp(21px,3vw,26px);
  letter-spacing:-.015em;line-height:1.22;margin:0 0 16px;text-wrap:balance}
.figure{background:var(--panel);border:1px solid var(--rule);padding:26px 28px;margin:0 0 18px}
.figure .n{font-family:var(--mono);font-weight:600;font-variant-numeric:tabular-nums;
  font-size:clamp(38px,7vw,58px);line-height:1;letter-spacing:-.03em;display:block;
  margin-bottom:12px}
.figure .q{font-family:var(--sans);font-size:15px;line-height:1.5;color:var(--ink);
  max-width:54ch;margin:0}
.figure .q em{font-style:normal;color:var(--ink-soft)}
.bind{margin-top:16px;padding-top:14px;border-top:1px solid var(--rule-soft);
  font-family:var(--sans);font-size:13.5px;line-height:1.55;color:var(--ink-soft);max-width:60ch}
.bind b{color:var(--ink);font-weight:600}
.nota{font-family:var(--sans);font-size:14px;color:var(--ink-soft);max-width:64ch}
.scroll{overflow-x:auto;margin:0 0 12px;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;min-width:560px;font-family:var(--sans);font-size:14px}
caption{caption-side:top;text-align:left;font-family:var(--sans);font-size:13.5px;
  color:var(--ink-soft);padding:0 0 12px;line-height:1.5;max-width:64ch}
caption b{color:var(--ink);font-weight:600}
th{font-weight:600;font-size:11.5px;letter-spacing:.07em;text-transform:uppercase;
  color:var(--ink-faint);text-align:right;padding:0 0 8px 18px;
  border-bottom:1px solid var(--ink);white-space:nowrap;vertical-align:bottom}
th:first-child{text-align:left;padding-left:0}
td{padding:9px 0 9px 18px;border-bottom:1px solid var(--rule-soft);text-align:right;
  font-variant-numeric:tabular-nums}
td:first-child{text-align:left;padding-left:0;font-family:var(--mono);font-size:13px}
tbody tr:last-child td{border-bottom:1px solid var(--rule)}
.cov{color:var(--ink-faint);font-family:var(--mono);font-size:12px}
.lead{font-weight:600}
.errata{border-left:3px solid var(--errata);background:var(--errata-wash);
  padding:24px 26px;margin:20px 0 18px}
.errata .tag{font-family:var(--sans);font-size:11.5px;font-weight:600;letter-spacing:.13em;
  text-transform:uppercase;color:var(--errata);margin:0 0 14px}
.swap{display:flex;flex-wrap:wrap;align-items:baseline;gap:0 18px;margin:0 0 16px}
.swap .was{font-family:var(--mono);font-size:clamp(24px,4.5vw,34px);font-weight:500;
  color:var(--ink-faint);text-decoration:line-through;text-decoration-color:var(--errata);
  text-decoration-thickness:2px}
.swap .arrow{font-family:var(--sans);color:var(--ink-faint);font-size:18px}
.swap .now{font-family:var(--mono);font-size:clamp(24px,4.5vw,34px);font-weight:600;
  color:var(--ink)}
.errata p{font-size:15.5px;max-width:62ch}
.errata p:last-child{margin-bottom:0}
.limits{list-style:none;padding:0;margin:0;display:grid;gap:1px;background:var(--rule-soft);
  border-top:1px solid var(--rule-soft);border-bottom:1px solid var(--rule-soft)}
.limits li{background:var(--paper);padding:13px 0;font-family:var(--sans);font-size:14.5px;
  line-height:1.5;color:var(--ink-soft)}
.limits li b{color:var(--ink);font-weight:600;font-family:var(--sans)}
.method{display:grid;gap:0;margin:6px 0 0}
.method div{display:grid;grid-template-columns:132px 1fr;gap:20px;padding:14px 0;
  border-bottom:1px solid var(--rule-soft)}
.method div:first-child{border-top:1px solid var(--rule)}
.method dt{font-family:var(--mono);font-size:12px;color:var(--gauge);letter-spacing:.02em;
  padding-top:2px}
.method dd{margin:0;font-family:var(--sans);font-size:14.5px;line-height:1.55;color:var(--ink-soft)}
.method dd b{color:var(--ink);font-weight:600}
@media(max-width:600px){.method div{grid-template-columns:1fr;gap:5px}.method dt{padding-top:0}}
.doors{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:1px;
  background:var(--rule);border:1px solid var(--rule);margin-top:6px}
.door{background:var(--panel);padding:18px 20px;display:block;border-bottom:none}
.door:hover{background:var(--gauge-wash);border-bottom:none}
.door .f{font-family:var(--mono);font-size:13px;font-weight:500;color:var(--gauge);
  display:block;margin-bottom:5px}
.door .d{font-family:var(--sans);font-size:13px;color:var(--ink-soft);line-height:1.45;
  display:block}
footer{margin-top:60px;padding-top:20px;border-top:1px solid var(--rule);
  font-family:var(--mono);font-size:12px;color:var(--ink-faint);line-height:1.7}
"""
