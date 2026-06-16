# indi-allsky UI Rewrite
## Aim
To migrate indi-allsky from Bootstrap to Tailwind CSS using DaisyUI as a component library

## Plan
1: Move the bulk of each template from Bootstrap to Tailwind.
2: Clean up remaining Bootstrap code, Remove imports of Bootstrap CSS
3: Go through each template removing hacks used to bypass Bootstrap overrides
3.5: Finalise new overall design language
4: Review each template for themeing consistency
5: Final fixes based on known issues and items identified in 4.
6: Enhancements include custom theme CSS, Default theme selection, etc
7: Page design reworks as needed

## Progress tracker

**Currently working on: 1 - Move the bulk of each template from Bootstrap to Tailwind.**

- [x] adu.html
- [x] astropanel.html
- [x] base.html
- [x] camera_simulator.html
- [x] cameraLens.html
- [x] cameras.html
- [x] chart.html
- [x] config.html
  - [x] admin.html
  - [x] camera.html
  - [x] filetransfer.html
  - [x] location.html
  - [x] overlays.html
  - [x] s3.html
  - [x] sensors.html
  - [x] timelapse.html
  - [x] adsb.html
  - [x] devices.html
  - [x] image.html
  - [x] mqtt.html
  - [x] processing.html
  - [x] sat_track.html
  - [x] syncapi.html
  - [x] youtube.html
- [x] config_list.html
- [x] config_restore.html
- [x] darks.html
- [x] drive_manager.html
- [x] filespaceusage.html
- [x] fitsimageviewer.html
- [x] focus.html
- [x] gallery.html
- [x] generate.html
- [x] imagecirclehelper.html
- [x] imageprocessing.html
- [x] imageviewer.html
- [x] index_canvas.html
- [x] index_img.html
- [x] lag.html
- [x] log.html
- [x] login.html
- [x] longterm_keogram.html
- [x] loop_canvas.html
- [x] loop_img.html
- [x] manual_gpio.html
- [x] mask.html
- [x] mini_generate.html
- [x] minivideoviewer.html
- [x] network.html
- [x] notifications.html
- [x] realtime_keogram.html
- [x] sensor_panel.html
- [x] sqm.html
- [x] support_info.html
- [x] system.html
- [x] taskqueue.html
- [x] user.html
- [x] users.html
- [x] videoviewer.html
- [x] view_image.html
- [x] virtualsky.html
- [x] watch_video.html

## To Test
Clone my fork `git clone https://github.com/TN-1/indi-allsky`, `git checkout ui-upgrade`, run `./misc/dev_run.sh` to spin up a local UI only server, access at `http://localhost:5000/indi-allsky/` Not all features will be available
Otherwise, install as normal. **Not ready for use in an actual deployment**

## Known issues
- Mobile layout responsive sidebar doesnt close
- Mobile pages BG colour
- Objects styled inside script tags are still bootstrap themed
- Images not centred in index_img (and index_canvas??)

## Things that need doing
- Remove bootstrap CSS includes
- Fix hardcoded styling
- Fix CSS inside script tags
- Test styling hacks in base.html for removal
- Theme consistency check
- Allow users to choose from the built in DaisyUI themes for default Light and Dark themes
- Change temp theme selector to L/D toggle
- Allow users to insert custom theme CSS

## FYI's
- Icons can be used like so: `<i class="tw:icon-[lucide--download] tw:w-4 tw:h-4 tw:text-primary"></i>` https://icon-sets.iconify.design/lucide/