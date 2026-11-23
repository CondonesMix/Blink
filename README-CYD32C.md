# Blink · port a la CYD 3,2" (ESP32-2432S032C)

Fork personal de [KfirLevy258/Blink](https://github.com/KfirLevy258/Blink) (v1.5.0) adaptado a la
*Cheap Yellow Display* de **3,2" con táctil capacitivo** (ESP32-2432S032C), con una vista que
muestra Claude y Codex a la vez. Todo está en la rama `cyd32c`; `main` es el original intacto.

> Required Notice: Copyright 2026 Kfir Levy (https://blink-buddy.com)
>
> Licencia: PolyForm Noncommercial 1.0.0 (ver `LICENSE`). Uso no comercial; no se vende.

## Qué cambia respecto al original

| Área | Original (CYD 2,8", ESP32-2432S028) | Este fork (CYD 3,2" C) |
|---|---|---|
| Pantalla | ILI9341 | ST7789 IPS, MADCTL `0x60` (horizontal, derecha en la caja), inversión ON |
| Bus de pantalla | 32 MHz | 32 MHz → 26,7 MHz real (con 40 MHz el ESP32 rechaza la configuración: pines por la matriz GPIO) |
| Retroiluminación | GPIO 21 | GPIO 27 (MOSFET) |
| Táctil | XPT2046 resistivo, SPI | GT911 capacitivo, I²C: SDA 33, SCL 32, RST 25, INT 21; **modo sondeo** a 10 ms (con interrupción no llegaban eventos) |
| Mapeo táctil | — | `screen_x = ABS_Y`, `screen_y = 240 − ABS_X` (`swap-xy` + `invert-y`) |
| Pantalla principal | Una página por proveedor | **Vista combinada**: aro izquierdo = semanal de Claude, derecho = semanal de Codex, y una barra **Fable** abajo |
| Ajustes | Botón *Update* | Botón **View** (Both / Pages); las ofertas OTA se ignoran |
| App del Mac | — | Envía una línea `{"t":"models","fable_pct":…,"fable_w_in_s":…}` leída de `cachedUsageUtilization` de Claude Code |

Archivos tocados:

- `firmware/boards/cyd32c.overlay`, `firmware/cyd32c.conf`: el hardware de la 3,2".
- `firmware/Kconfig`: opciones `BLINK_BOARD_CYD32C` y `BLINK_DUAL_WEEKLY`.
- `firmware/src/main.c`: sin la corrección de MADCTL del ILI9341; registra si el GT911 está listo.
- `firmware/src/ui_swipe.c`: lee el GT911 y corrige el eje Y.
- `firmware/src/usage_view.c/.h`: vista combinada, barra Fable y conmutador View.
- `firmware/src/ui_settings.c`: botón View en lugar de Update.
- `firmware/src/proto.c`: mensaje `models` y rechazo de `ota_avail`/`ota_begin`.
- `pc/bridge.py`: envío de la línea `models`.
- `tools/panel_render/render_main.c`: escenas 98/99 para ver la vista combinada en el ordenador.

## Por qué no hay actualizaciones

Las imágenes oficiales son para la 2,8" y van firmadas con la clave del autor. El MCUboot de esta
placa usa otra clave, así que una actualización oficial no arrancaría. Por eso el firmware ignora
las ofertas y **no debe ejecutarse `blink update`** en el Mac (reinstalaría la app oficial, sin la
línea de Fable). Las actualizaciones se hacen recompilando y flasheando por cable.

## Flashear sin compilar

Binarios en `release/1.5.0-cyd32c/` (firmados con la clave del dueño del fork). Necesitas
`esptool.py` y `espefuse.py` (`pip install esptool==5.3.1 bitstring==4.4.0 pyserial==3.5`) y un
**cable USB-A a USB-C de datos**: con un cable C a C la placa no se enciende, porque le faltan las
resistencias CC.

```sh
tools/cyd32c/flash_new.sh /dev/cu.usbserial-XXXX     # placa nueva (borra y escribe todo)
tools/cyd32c/reflash_app.sh /dev/cu.usbserial-XXXX   # placa que ya lleva este Blink (solo la app)
```

`flash_new.sh` comprueba antes que la placa no tenga cifrado de flash. `reflash_app.sh` solo
escribe si el MCUboot de la placa coincide con el de la release, para no dejar a medias una placa
de fábrica.

## Instalar la app del Mac

1. Instala la oficial: `curl -fsSL https://github.com/KfirLevy258/Blink/releases/latest/download/blink-macos-arm64.tar.gz | tar xz && ./blink/blink`
2. Para tener la barra de Fable, cambia el servicio por el de este fork: `tools/cyd32c/install_mac_app.sh`
   (deja la oficial en `~/.blink/bin/blink.release`).
3. Si la cifra de Claude se congela: `~/.blink/bin/blink status`. Si el refresco falla, haz `/login`
   en Claude Code; con la sesión caducada, `/usage` no descarga los límites del plan.

## Compilar

Zephyr **v4.3.1** con SDK **0.17.4** (no 4.4.0; ver `firmware/README.md`), con los blobs de
`hal_espressif`.

```sh
. tools/lib_zephyr.sh && blink_zephyr_activate
cd firmware
west build --sysbuild -d build-sb -b esp32_devkitc/esp32/procpu . -- \
  -DSB_CONFIG_BOOTLOADER_MCUBOOT=y -DUSE_CCACHE=0 \
  -DSB_CONFIG_BOOT_SIGNATURE_KEY_FILE="\"$HOME/.blink/ota_signing_key_p256.pem\"" \
  -Dfirmware_DTC_OVERLAY_FILE=boards/cyd32c.overlay \
  -Dfirmware_EXTRA_CONF_FILE=cyd32c.conf
```

Salida: `build-sb/mcuboot/zephyr/zephyr.bin` → `0x1000` y
`build-sb/firmware/zephyr/zephyr.signed.bin` → `0x20000`.

La clave de firma **no está en el repo**. Sin la clave original no se puede firmar una app que
acepte el MCUboot ya flasheado. Solución: generar otra (`imgtool keygen -t ecdsa-p256`) y flashear
la placa entera con `flash_new.sh`.

## Carcasa

Los STL de la caja Blink original están en MakerWorld y su licencia **no permite volver a
publicarlos**, así que aquí solo están los scripts que los transforman:

- `hardware/cyd32c/adapt_front_28_to_32.py`: adapta `blink_front.stl` (2,8") a la 3,2". Amplía
  el hueco, mueve los pines a 86,7 × 48 mm, y ajusta el rebaje del cristal, la ventana y el alivio
  para el LED y el LDR. Uso: `python3 adapt_front_28_to_32.py blink_front.stl blink_front_CYD32.stl [grosor_cristal_mm]`.
- `hardware/cyd32c/mascots.py`: genera las carcasas-mascota (A, B, C y D, el robot simétrico) a
  partir del frontal adaptado (`BLINK_FRONT_32=… OUT_DIR=… python3 mascots.py`).
  `verify_robot.py` comprueba la simetría.

Cotas de la placa 3,2" (plano del fabricante): 93,7 × 55,0 mm. Agujeros de Ø3,2 a 3,5 mm del
borde, separados 86,7 × 48,0 mm. Área activa de 64,8 × 48,6 mm, desplazada unos 2,8 mm hacia el
lado opuesto al flex.
