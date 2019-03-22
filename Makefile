.PHONY: run clean install uninstall-most uninstall


run:
	./surface-dtx-daemon -c ./etc/surface-dtx.cfg

clean:
	@rm -rf dtx/__pycache__

install:
	@echo "Installing .py files to '${DESTDIR}/opt/surface-dtx/'."
	@mkdir -p "${DESTDIR}/opt/surface-dtx/"
	@cp -r dtx "${DESTDIR}/opt/surface-dtx/"
	@cp "surface-dtx-daemon" "${DESTDIR}/opt/surface-dtx/"
	@cp "LICENSE" "${DESTDIR}/opt/surface-dtx/"
	@cp "README.md" "${DESTDIR}/opt/surface-dtx/"

	@chmod 644 "${DESTDIR}/opt/surface-dtx/dtx/"*.py
	@chmod 644 "${DESTDIR}/opt/surface-dtx/LICENSE"
	@chmod 644 "${DESTDIR}/opt/surface-dtx/README.md"
	@chmod 755 "${DESTDIR}/opt/surface-dtx/surface-dtx-daemon"

	@echo "Installing config files to '${DESTDIR}/etc/surface-dtx/'."
	@mkdir -p "${DESTDIR}/etc/surface-dtx/"
	@cp etc/* "${DESTDIR}/etc/surface-dtx/"

	@chmod 644 "${DESTDIR}/etc/surface-dtx/surface-dtx.cfg"
	@chmod 755 "${DESTDIR}/etc/surface-dtx/attach.sh"
	@chmod 755 "${DESTDIR}/etc/surface-dtx/detach.sh"

	@echo "Installing systemd unit file to '${DESTDIR}/usr/lib/systemd/system/surface-dtx.service'."
	@mkdir -p "${DESTDIR}/usr/lib/systemd/system/"
	@cp systemd/surface-dtx.service "${DESTDIR}/usr/lib/systemd/system/surface-dtx.service"

	@chmod 644 "${DESTDIR}/usr/lib/systemd/system/surface-dtx.service"

	@echo "Installation complete."
	@echo "    Don't forget to run 'systemctl enable surface-dtx.service'".

uninstall-core:
	@rm -rf ${DESTDIR}/opt/surface-dtx
	@rm -rf ${DESTDIR}/usr/lib/systemd/system/surface-dtx.service

uninstall: uninstall-core
	@rm -rf ${DESTDIR}/etc/surface-dtx
