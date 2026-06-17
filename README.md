# indi-allsky UI Rewrite
## Aim
To migrate indi-allsky from Bootstrap to Tailwind CSS using DaisyUI as a component library

## Plan
1: Move the bulk of each template from Bootstrap to Tailwind. - DONE
2: Clean up remaining Bootstrap code, Remove imports of Bootstrap CSS - DONE
3: Go through each template removing hacks used to bypass Bootstrap overrides
3.5: Finalise new overall design language
4: Review each template for themeing consistency
5: Final fixes based on known issues and items identified in 4.
6: Enhancements include custom theme CSS, Default theme selection, etc
7: Page design reworks as needed

## Progress tracker

**Currently working on: 3: Go through each template removing hacks used to bypass Bootstrap overrides**

- [ ] adu.html
- [ ] astropanel.html
- [x] base.html
- [ ] camera_simulator.html
- [ ] cameraLens.html
- [ ] cameras.html
- [ ] chart.html
- [ ] config.html
  - [ ] admin.html
  - [ ] adsb.html
  - [ ] camera.html
  - [ ] devices.html
  - [ ] filetransfer.html
  - [ ] image.html
  - [ ] location.html
  - [ ] mqtt.html
  - [ ] overlays.html
  - [ ] processing.html
  - [ ] s3.html
  - [ ] sat_track.html
  - [ ] sensors.html
  - [ ] syncapi.html
  - [ ] timelapse.html
  - [ ] youtube.html
- [ ] config_list.html
- [ ] config_restore.html
- [ ] darks.html
- [ ] drive_manager.html
- [ ] filespaceusage.html
- [ ] fitsimageviewer.html
- [ ] focus.html
- [ ] gallery.html
- [ ] generate.html
- [ ] imagecirclehelper.html
- [ ] imageprocessing.html
- [ ] imageviewer.html
- [ ] index_canvas.html
- [ ] index_img.html
- [ ] lag.html
- [ ] log.html
- [ ] login.html
- [ ] longterm_keogram.html
- [ ] loop_canvas.html
- [ ] loop_img.html
- [ ] manual_gpio.html
- [ ] mask.html
- [ ] mini_generate.html
- [ ] minivideoviewer.html
- [ ] network.html
- [ ] notifications.html
- [ ] realtime_keogram.html
- [ ] sensor_panel.html
- [ ] sqm.html
- [ ] support_info.html
- [ ] system.html
- [ ] taskqueue.html
- [ ] user.html
- [ ] users.html
- [ ] videoviewer.html
- [ ] view_image.html
- [ ] virtualsky.html
- [ ] watch_video.html

## To Test
Clone my fork `git clone https://github.com/TN-1/indi-allsky`, `git checkout ui-upgrade`, run `./misc/dev_run.sh` to spin up a local UI only server, access at `http://localhost:5000/indi-allsky/` Not all features will be available
Otherwise, install as normal. **Not ready for use in an actual deployment**

## Known issues
- Mobile layout responsive sidebar doesnt close (Fixed in design.html)
- Mobile pages BG colour
- Images not centred in index_img (and index_canvas??)

## Things that need doing
- Test styling hacks in base.html for removal
- Theme consistency check
- Allow users to choose from the built in DaisyUI themes for default Light and Dark themes
- Change temp theme selector to L/D toggle
- Allow users to insert custom theme CSS

## FYI's
- Icons can be used like so: `<i class="tw:icon-[lucide--download] tw:w-4 tw:h-4 tw:text-primary"></i>` https://icon-sets.iconify.design/lucide/