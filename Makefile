.PHONY: run clean install uninstall-most uninstall


run:
	./surface-dtx-daemon -c ./etc/surface-dtx.cfg

clean:
	@rm -rf dtx/__pycache__

install:
	@echo "Installing .py files to '${PREFIX}/opt/surface-dtx/'."
	@mkdir -p "${PREFIX}/opt/surface-dtx/"
	@cp -r dtx "${PREFIX}/opt/surface-dtx/"
	@cp "surface-dtx-daemon" "${PREFIX}/opt/surface-dtx/"
	@cp "LICENSE" "${PREFIX}/opt/surface-dtx/"
	@cp "README.md" "${PREFIX}/opt/surface-dtx/"

	@chmod 644 "${PREFIX}/opt/surface-dtx/dtx/"*.py
	@chmod 644 "${PREFIX}/opt/surface-dtx/LICENSE"
	@chmod 644 "${PREFIX}/opt/surface-dtx/README.md"
	@chmod 755 "${PREFIX}/opt/surface-dtx/surface-dtx-daemon"

	@echo "Installing config files to '${PREFIX}/etc/surface-dtx/'."
	@mkdir -p "${PREFIX}/etc/surface-dtx/"
	@cp etc/* "${PREFIX}/etc/surface-dtx/"

	@chmod 644 "${PREFIX}/etc/surface-dtx/surface-dtx.cfg"
	@chmod 755 "${PREFIX}/etc/surface-dtx/attach.sh"
	@chmod 755 "${PREFIX}/etc/surface-dtx/detach.sh"

	@echo "Installing systemd unit file to '${PREFIX}/usr/lib/systemd/system/surface-dtx.service'."
	@mkdir -p "${PREFIX}/usr/lib/systemd/system/"
	@cp systemd/surface-dtx.service "${PREFIX}/usr/lib/systemd/system/surface-dtx.service"

	@chmod 644 "${PREFIX}/usr/lib/systemd/system/surface-dtx.service"

	@echo "Installation complete."
	@echo "    Don't forget to run 'systemctl enable surface-dtx.service'".

uninstall-core:
	@rm -rf ${PREFIX}/opt/surface-dtx
	@rm -rf ${PREFIX}/usr/lib/systemd/system/surface-dtx.service

uninstall: uninstall-core
	@rm -rf ${PREFIX}/etc/surface-dtx
